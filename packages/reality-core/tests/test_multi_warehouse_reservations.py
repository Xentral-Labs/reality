"""Orders served from several warehouses (spec 303)."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import BusinessEvent, Reservation
from reality.services import core
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
)
from reality.tools.application import approve_and_execute_proposal


def _munich(session, business, name="Munich Warehouse"):
    return core.create_location(session, business.tenant.id, name)


def _stock(session, business, quantity, location, item=None, **identity):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        (item or business.item).id,
        quantity,
        to_location_id=location.id,
        **identity,
    )


def _promise(session, business, quantity, item=None):
    return core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        (item or business.item).id,
        business.location.id,
        quantity,
        "2026-10-10",
    )


def _reservations(session, business, promise):
    session.expire_all()
    return sorted(
        (row.location_id, row.quantity, row.status)
        for row in session.scalars(
            select(Reservation).where(
                Reservation.tenant_id == business.tenant.id,
                Reservation.commitment_id == promise.id,
            )
        )
    )


# --- T004: reserving at a named location -----------------------------------------------


def test_reserving_without_a_location_is_unchanged(session, business):
    munich = _munich(session, business)
    _stock(session, business, "6", business.location)
    _stock(session, business, "40", munich)
    promise = _promise(session, business, "10")

    result = core.reserve(session, business.tenant.id, promise.id)

    # Only the promise's own location: 6 reserved, 4 short, Munich untouched.
    assert (result.reserved, result.shortage) == (Decimal(6), Decimal(4))
    assert _reservations(session, business, promise) == [
        (business.location.id, Decimal("6.0000"), "active")
    ]


def test_the_rest_is_reserved_at_a_named_second_location(session, business):
    tenant = business.tenant.id
    munich = _munich(session, business)
    _stock(session, business, "6", business.location)
    _stock(session, business, "40", munich)
    promise = _promise(session, business, "10")
    core.reserve(session, tenant, promise.id)

    result = core.reserve(session, tenant, promise.id, location_id=munich.id)

    # The rest is what is still open; Munich has plenty and gives exactly it.
    assert (result.requested, result.reserved, result.shortage) == (
        Decimal(4),
        Decimal(4),
        Decimal(0),
    )
    assert _reservations(session, business, promise) == sorted(
        [
            (business.location.id, Decimal("6.0000"), "active"),
            (munich.id, Decimal("4.0000"), "active"),
        ]
    )
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.subject_id == result.reservation.id,
        )
    )
    assert json.loads(event.payload)["location_id"] == munich.id
    # Munich's own availability now counts what it holds for the order.
    assert core.active_reserved(session, tenant, business.item.id, munich.id) == 4


def test_availability_is_judged_at_the_named_location(session, business):
    tenant = business.tenant.id
    munich = _munich(session, business)
    _stock(session, business, "3", munich)
    other = _promise(session, business, "2")
    core.reserve(session, tenant, other.id, location_id=munich.id)
    promise = _promise(session, business, "10")

    result = core.reserve(session, tenant, promise.id, location_id=munich.id)

    # Munich holds 3, of which 2 are reserved for another order.
    assert (result.reserved, result.shortage) == (Decimal(1), Decimal(9))


def test_nothing_available_there_reserves_nothing(session, business):
    tenant = business.tenant.id
    munich = _munich(session, business)
    promise = _promise(session, business, "10")

    result = core.reserve(session, tenant, promise.id, location_id=munich.id)

    assert (result.reservation, result.reserved) == (None, Decimal(0))
    assert _reservations(session, business, promise) == []


def test_a_location_that_cannot_serve_is_refused(session, business):
    tenant = business.tenant.id
    from reality.db.core import Location

    promise = _promise(session, business, "10")
    transit = _munich(session, business, "In transit")
    transit.allows_stock = False
    closed = _munich(session, business, "Old warehouse")
    session.commit()
    core.set_master_data_active(session, tenant, Location, closed.id, False)

    for location in (transit, closed):
        with pytest.raises(core.InvalidOperation) as refused:
            core.reserve(session, tenant, promise.id, location_id=location.id)
        assert refused.value.code == "reservation_location_not_stock"

    other = core.create_tenant(session, "Other GmbH")
    foreign = core.create_location(session, other.id, "Foreign warehouse")
    with pytest.raises(core.NotFound):
        core.reserve(session, tenant, promise.id, location_id=foreign.id)
    assert _reservations(session, business, promise) == []


def test_a_lot_is_reserved_where_it_lies(session, business):
    tenant = business.tenant.id
    item = core.create_item(session, tenant, "LOT-303", "Lot item", tracking_type="lot")
    lot = core.create_lot(session, tenant, item.id, "L-303")
    munich = _munich(session, business)
    _stock(session, business, "5", munich, item=item, lot_id=lot.id)
    promise = _promise(session, business, "5", item=item)

    # Positive control: the lot is not at home, so nothing is reserved there.
    assert core.reserve(session, tenant, promise.id, lot_id=lot.id).reserved == 0
    result = core.reserve(
        session, tenant, promise.id, lot_id=lot.id, location_id=munich.id
    )

    assert result.reserved == Decimal(5)
    assert result.reservation.lot_id == lot.id


def test_a_reservation_elsewhere_is_released_like_any_other(session, business):
    tenant = business.tenant.id
    munich = _munich(session, business)
    _stock(session, business, "4", munich)
    promise = _promise(session, business, "4")
    reserved = core.reserve(session, tenant, promise.id, location_id=munich.id)

    core.release_reservation(session, tenant, reserved.reservation.id)

    assert _reservations(session, business, promise) == [
        (munich.id, Decimal("4.0000"), "released")
    ]
    assert core.active_reserved(session, tenant, business.item.id, munich.id) == 0


# --- T005: the reviewed reservation ----------------------------------------------------


def test_the_review_shows_the_named_location_and_its_stock(session, business):
    tenant = business.tenant.id
    munich = _munich(session, business)
    _stock(session, business, "40", munich)
    promise = _promise(session, business, "10")

    proposal = prepare_delivery_action(
        session,
        tenant,
        "reserve",
        {"commitment_id": promise.id, "location_id": munich.id},
        request_id="r303-munich",
    )
    review = json.loads(proposal.input)["_delivery_review"]
    assert review["intent"]["location_id"] == munich.id
    assert review["state"]["inventory"]["location_id"] == munich.id
    assert Decimal(review["state"]["inventory"]["available"]) == 40
    assert review["effect"]["applied"] == "10"
    assert _reservations(session, business, promise) == []

    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=review["token"], confirmed=True
    )
    assert _reservations(session, business, promise) == [
        (munich.id, Decimal("10.0000"), "active")
    ]
    assert delivery_proposal_detail(session, tenant, proposal.id)["verification"] == (
        "verified"
    )


def test_the_review_refuses_a_location_that_cannot_serve(session, business):
    tenant = business.tenant.id
    transit = _munich(session, business, "In transit")
    transit.allows_stock = False
    session.commit()
    promise = _promise(session, business, "10")

    with pytest.raises(core.InvalidOperation) as refused:
        prepare_delivery_action(
            session,
            tenant,
            "reserve",
            {"commitment_id": promise.id, "location_id": transit.id},
            request_id="r303-transit",
        )
    assert refused.value.code == "reservation_location_not_stock"
