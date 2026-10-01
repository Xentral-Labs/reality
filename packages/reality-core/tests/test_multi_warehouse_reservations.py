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


# --- T006: readiness and shipping per location -----------------------------------------


def _split(session, business):
    """6 at home and 4 in Munich reserved for one promise of 10."""
    tenant = business.tenant.id
    munich = _munich(session, business)
    _stock(session, business, "6", business.location)
    _stock(session, business, "40", munich)
    promise = _promise(session, business, "10")
    core.reserve(session, tenant, promise.id)
    core.reserve(session, tenant, promise.id, location_id=munich.id)
    return munich, promise


def _readiness(session, business, promise, **kwargs):
    from reality.services.fulfillment_readiness import fulfillment_readiness

    return fulfillment_readiness(session, business.tenant.id, promise.id, **kwargs)


def _queue_line(session, business, promise):
    from reality.services import projections

    projections.refresh_operational_projections(session, business.tenant.id, force=True)
    rows = projections.projection_rows(
        session, business.tenant.id, projections.FULFILLMENT_QUEUE
    )
    return next(
        line
        for row in rows
        for line in row["lines"]
        if line["commitment_id"] == promise.id
    )


def test_reservations_in_two_warehouses_make_the_promise_ready(session, business):
    _, promise = _split(session, business)

    readiness = _readiness(session, business, promise)
    assert readiness.ship_ready, readiness.blocker_codes
    assert (readiness.reserved_quantity, readiness.physical_quantity) == (
        Decimal("10"),
        Decimal("10"),
    )
    line = _queue_line(session, business, promise)
    assert Decimal(line["shippable_quantity"]) == 10
    assert "insufficient_stock" not in line["blocking_reasons"]


def test_a_reservation_counts_only_with_what_its_warehouse_still_holds(
    session, business
):
    tenant = business.tenant.id
    munich, promise = _split(session, business)
    # Munich's stock is moved away; its reservation is no longer covered.
    core.record_movement(
        session,
        tenant,
        "adjustment",
        business.item.id,
        "38",
        from_location_id=munich.id,
        reason="count",
    )

    readiness = _readiness(session, business, promise)
    assert not readiness.ship_ready
    assert "insufficient_stock" in readiness.blocker_codes
    assert Decimal(_queue_line(session, business, promise)["shippable_quantity"]) == 8


def test_without_reservations_elsewhere_readiness_is_unchanged(session, business):
    tenant = business.tenant.id
    munich = _munich(session, business)
    _stock(session, business, "40", munich)
    promise = _promise(session, business, "10")

    # Munich's stock alone never made a promise at home ready.
    assert set(_readiness(session, business, promise).blocker_codes) == {
        "insufficient_reservation",
        "insufficient_stock",
    }
    # Stock at home and no reservation: only the reservation is missing, as before.
    _stock(session, business, "10", business.location)
    readiness = _readiness(session, business, promise)
    assert readiness.blocker_codes == ("insufficient_reservation",)
    core.reserve(session, tenant, promise.id)
    assert _readiness(session, business, promise).ship_ready


def _dispatch(session, business, movements, tracking):
    from reality.tools.application import create_change_proposal

    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "carrier": "DHL",
            "tracking_number": tracking,
            "movements": movements,
        },
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )


def _movement(business, promise, location, quantity):
    return {
        "commitment_id": promise.id,
        "item_id": business.item.id,
        "from_location_id": location.id,
        "quantity": quantity,
    }


def test_each_warehouse_ships_its_part_as_its_own_package(session, business):
    tenant = business.tenant.id
    munich, promise = _split(session, business)

    first = _dispatch(
        session, business, [_movement(business, promise, business.location, "6")], "T1"
    )
    second = _dispatch(
        session, business, [_movement(business, promise, munich, "4")], "T2"
    )

    assert (first.status, second.status) == ("executed", "executed")
    assert core.open_quantity(session, tenant, promise.id) == 0
    assert _reservations(session, business, promise) == sorted(
        [
            (business.location.id, Decimal("6.0000"), "consumed"),
            (munich.id, Decimal("4.0000"), "consumed"),
        ]
    )
    assert core.stock_at(session, tenant, business.item.id, munich.id) == 36


def test_a_warehouse_ships_only_what_is_reserved_there(session, business):
    munich, promise = _split(session, business)
    # Home holds enough on its shelves; what it lacks is the reservation.
    _stock(session, business, "14", business.location)

    # Ten from home would take Munich's four from stock nobody reserved there.
    with pytest.raises(core.InvalidOperation) as refused:
        _dispatch(
            session,
            business,
            [_movement(business, promise, business.location, "10")],
            "T-ALL",
        )
    assert refused.value.code == "shipment_blocked_readiness"
    # Munich reserved four; five cannot leave from there.
    with pytest.raises(core.InvalidOperation) as refused:
        _dispatch(
            session, business, [_movement(business, promise, munich, "5")], "T-MUC"
        )
    assert refused.value.code == "shipment_blocked_readiness"
    # Positive control: what is reserved at home ships from home.
    assert (
        _dispatch(
            session,
            business,
            [_movement(business, promise, business.location, "6")],
            "T-HOME",
        ).status
        == "executed"
    )
