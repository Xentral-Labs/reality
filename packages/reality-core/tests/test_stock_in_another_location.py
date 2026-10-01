"""Stock in another warehouse (spec 303 FR-003)."""

import json
from decimal import Decimal

from sqlalchemy import event

from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.exceptions import operational_exceptions
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)

CLASS = "stock_in_another_location"


def _found(session, tenant_id):
    rows = [
        row
        for row in operational_exceptions(session, tenant_id)
        if row.class_id == CLASS
    ]
    assert len({row.id for row in rows}) == len(rows)
    return {row.record_id: row for row in rows}


def _location(session, business, name):
    return core.create_location(session, business.tenant.id, name)


def _stock(session, business, quantity, location, item=None):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        (item or business.item).id,
        quantity,
        to_location_id=location.id,
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


def test_stock_elsewhere_is_named_when_home_cannot_cover_the_rest(session, business):
    tenant = business.tenant.id
    munich = _location(session, business, "Munich")
    berlin = _location(session, business, "Berlin")
    _stock(session, business, "2", business.location)
    _stock(session, business, "10", berlin)
    _stock(session, business, "40", munich)
    promise = _promise(session, business, "10")

    row = _found(session, tenant)[promise.id]
    assert row.record_type == "commitment"
    assert row.severity == "normal"
    assert (
        row.causal_values["unreserved_quantity"],
        row.causal_values["own_available_quantity"],
        row.causal_values["elsewhere"],
    ) == (Decimal(10), Decimal(2), "Munich 40 · Berlin 10")
    # Most available first; each proposes what it could cover of the gap.
    assert [
        (entry["location_id"], entry["available"], entry["proposed"])
        for entry in row.trace["locations"]
    ] == [(munich.id, "40", "8"), (berlin.id, "10", "8")]


def test_nothing_is_named_when_home_covers_the_rest(session, business):
    tenant = business.tenant.id
    munich = _location(session, business, "Munich")
    _stock(session, business, "40", munich)
    _stock(session, business, "10", business.location)
    promise = _promise(session, business, "10")
    assert promise.id not in _found(session, tenant)

    # Positive control: another order takes home's stock, and Munich is named.
    other = _promise(session, business, "5")
    core.reserve(session, tenant, other.id)
    assert promise.id in _found(session, tenant)


def test_nothing_is_named_when_no_other_warehouse_has_any(session, business):
    tenant = business.tenant.id
    munich = _location(session, business, "Munich")
    promise = _promise(session, business, "10")
    assert promise.id not in _found(session, tenant)
    _stock(session, business, "3", munich)
    assert promise.id in _found(session, tenant)


def test_a_reserved_held_cancelled_or_shipped_promise_is_not_named(session, business):
    tenant = business.tenant.id
    munich = _location(session, business, "Munich")
    _stock(session, business, "40", munich)

    reserved = _promise(session, business, "4")
    held = _promise(session, business, "4")
    cancelled = _promise(session, business, "4")
    assert {reserved.id, held.id, cancelled.id} <= set(_found(session, tenant))

    core.reserve(session, tenant, reserved.id, location_id=munich.id)
    core.hold_commitment(session, tenant, held.id, "customer_request")
    core.cancel_commitment(session, tenant, cancelled.id, reason="customer withdrew")
    found = _found(session, tenant)
    assert not {reserved.id, held.id, cancelled.id} & set(found)

    shipped = _promise(session, business, "2")
    _stock(session, business, "2", business.location)
    core.reserve(session, tenant, shipped.id)
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=shipped.id,
    )
    assert shipped.id not in _found(session, tenant)


def test_a_customer_on_delivery_hold_is_not_named(session, business):
    tenant = business.tenant.id
    munich = _location(session, business, "Munich")
    _stock(session, business, "40", munich)
    promise = _promise(session, business, "4")
    assert promise.id in _found(session, tenant)

    core.hold_party_delivery(session, tenant, business.customer.id, "credit_check")
    assert promise.id not in _found(session, tenant)


def test_only_serving_warehouses_count(session, business):
    from reality.db.core import Location

    tenant = business.tenant.id
    transit = _location(session, business, "In transit")
    closed = _location(session, business, "Old warehouse")
    _stock(session, business, "40", transit)
    _stock(session, business, "40", closed)
    transit.allows_stock = False
    session.commit()
    core.set_master_data_active(session, tenant, Location, closed.id, False)
    promise = _promise(session, business, "4")

    assert promise.id not in _found(session, tenant)


def test_what_other_orders_reserved_there_is_not_available(session, business):
    tenant = business.tenant.id
    munich = _location(session, business, "Munich")
    _stock(session, business, "5", munich)
    other = _promise(session, business, "5")
    core.reserve(session, tenant, other.id, location_id=munich.id)
    promise = _promise(session, business, "4")

    # Munich's five are all reserved for the other order.
    assert promise.id not in _found(session, tenant)


def test_reserving_there_through_the_review_clears_it(session, business):
    tenant = business.tenant.id
    munich = _location(session, business, "Munich")
    _stock(session, business, "40", munich)
    promise = _promise(session, business, "4")
    location = _found(session, tenant)[promise.id].trace["locations"][0]

    proposal = prepare_delivery_action(
        session,
        tenant,
        "reserve",
        {
            "commitment_id": promise.id,
            "location_id": location["location_id"],
            "quantity": location["proposed"],
        },
        request_id="s303-reserve",
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=token, confirmed=True
    )

    assert promise.id not in _found(session, tenant)


def test_a_transfer_through_the_review_clears_it(session, business):
    tenant = business.tenant.id
    munich = _location(session, business, "Munich")
    _stock(session, business, "40", munich)
    promise = _promise(session, business, "4")
    location = _found(session, tenant)[promise.id].trace["locations"][0]

    proposal = create_change_proposal(
        session,
        tenant,
        "movement_create",
        {
            "movement_type": "transfer",
            "item_id": business.item.id,
            "quantity": location["proposed"],
            "from_location_id": location["location_id"],
            "to_location_id": business.location.id,
        },
    )
    # A transfer is reviewed like any delivery action (spec 303).
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=token, confirmed=True
    )

    # Home now holds the four; reserving is the usual next step.
    assert promise.id not in _found(session, tenant)
    assert core.reserve(session, tenant, promise.id).reserved == 4


def test_the_statement_count_does_not_grow_with_promises(session, business):
    from reality.services.exceptions import _stock_in_another_location_exceptions

    tenant = business.tenant.id
    munich = _location(session, business, "Munich")
    made = 0

    def statements(promises):
        nonlocal made
        for _ in range(promises - made):
            item = core.create_item(session, tenant, f"SKU-W-{made}", "W")
            _stock(session, business, "5", munich, item=item)
            _promise(session, business, "2", item=item)
            made += 1
        count = 0

        def counter(*_):
            nonlocal count
            count += 1

        engine = session.get_bind()
        event.listen(engine, "before_cursor_execute", counter)
        try:
            found = _stock_in_another_location_exceptions(session, tenant, core.now())
        finally:
            event.remove(engine, "before_cursor_execute", counter)
        assert len(found) == promises
        return count

    assert statements(2) == statements(20)


def test_another_company_sees_none_of_it(session, business):
    tenant = business.tenant.id
    munich = _location(session, business, "Munich")
    _stock(session, business, "40", munich)
    promise = _promise(session, business, "4")
    other = core.create_tenant(session, "Other GmbH")

    assert _found(session, other.id) == {}
    assert promise.id in _found(session, tenant)
