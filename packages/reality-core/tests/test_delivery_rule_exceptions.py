"""Spec 306 FR-005: orders waiting for completeness and rests against a no-backorder rule."""

from datetime import UTC, datetime

import pytest

from reality.services import core
from reality.services.delivery_rules import state_delivery_rule
from reality.services.exceptions import operational_exceptions


@pytest.fixture
def lamp(session, business):
    return reviewed_create_item(session, business.tenant.id, "LAMP-306E", "Lamp 306")


def _order(session, business, number, lines):
    _, document, _, commitments = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": item.id,
                "quantity": quantity,
                "unit_price": "10",
                "gross_amount": str(int(quantity) * 10),
            }
            for item, quantity in lines
        ],
        str(sum(int(quantity) * 10 for _, quantity in lines)),
        requested_delivery_at=datetime(2026, 10, 20, tzinfo=UTC),
    )
    return document, commitments


def _stock(session, business, item, quantity):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        item.id,
        quantity,
        to_location_id=business.location.id,
    )


def _rows(session, business, class_id):
    return {
        row.record_id: row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == class_id
    }


def _rule(session, business, rule):
    state_delivery_rule(
        session,
        business.tenant.id,
        rule,
        "Customer asked",
        party_id=business.customer.id,
    )


def test_an_order_waiting_only_for_completeness_is_reported(session, business, lamp):
    tenant = business.tenant.id
    document, (bikes, lamps) = _order(
        session, business, "SO-306-E1", [(business.item, "5"), (lamp, "3")]
    )
    _stock(session, business, business.item, "5")
    core.reserve(session, tenant, bikes.id)
    # Positive control: without the rule nothing waits for completeness.
    assert document.id not in _rows(session, business, "order_waiting_for_completeness")
    _rule(session, business, "ship_complete")

    row = _rows(session, business, "order_waiting_for_completeness")[document.id]

    assert row.record_type == "document"
    assert row.trace["ready_commitment_ids"] == [bikes.id]
    assert row.trace["waiting_commitment_ids"] == [lamps.id]
    assert row.trace["rule_source"] == "customer"
    # Once the whole order can ship, it no longer waits.
    _stock(session, business, lamp, "3")
    core.reserve(session, tenant, lamps.id)
    assert document.id not in _rows(session, business, "order_waiting_for_completeness")


def test_an_order_with_nothing_ready_is_not_waiting_for_the_rule(
    session, business, lamp
):
    document, _ = _order(
        session, business, "SO-306-E2", [(business.item, "5"), (lamp, "3")]
    )
    _rule(session, business, "ship_complete")

    assert document.id not in _rows(session, business, "order_waiting_for_completeness")


def test_a_rest_after_a_shipment_is_a_backorder_against_the_rule(
    session, business, lamp
):
    tenant = business.tenant.id
    _, (bikes, lamps) = _order(
        session, business, "SO-306-E3", [(business.item, "10"), (lamp, "2")]
    )
    _rule(session, business, "no_backorders")
    # Positive control: nothing shipped yet, nothing is a backorder.
    assert not _rows(session, business, "backorder_against_rule")
    _stock(session, business, business.item, "6")
    core.reserve(session, tenant, bikes.id)
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "6",
        from_location_id=business.location.id,
        commitment_id=bikes.id,
    )

    rows = _rows(session, business, "backorder_against_rule")

    assert set(rows) == {bikes.id, lamps.id}
    assert rows[bikes.id].causal_values["open_quantity"] == 4
    assert rows[lamps.id].causal_values["open_quantity"] == 2
    core.cancel_commitment(session, tenant, bikes.id, reason="No backorders by rule")
    assert set(_rows(session, business, "backorder_against_rule")) == {lamps.id}


def test_without_a_no_backorder_rule_a_rest_is_ordinary(session, business):
    tenant = business.tenant.id
    _, (bikes,) = _order(session, business, "SO-306-E4", [(business.item, "10")])
    _stock(session, business, business.item, "6")
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "6",
        from_location_id=business.location.id,
        commitment_id=bikes.id,
    )

    assert bikes.id not in _rows(session, business, "backorder_against_rule")


# --- review round (T017) ---------------------------------------------------------------


def test_a_corrected_shipment_is_no_shipment(session, business):
    tenant = business.tenant.id
    _, (bikes,) = _order(session, business, "SO-306-COR", [(business.item, "10")])
    _rule(session, business, "no_backorders")
    _stock(session, business, business.item, "6")
    shipped = core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "6",
        from_location_id=business.location.id,
        commitment_id=bikes.id,
    )
    # Positive control: after the shipment the rest is a backorder.
    assert bikes.id in _rows(session, business, "backorder_against_rule")

    core.correct_movement(session, tenant, shipped.id, reason="Never left")

    assert bikes.id not in _rows(session, business, "backorder_against_rule")


def test_an_order_kept_back_by_a_hold_is_not_waiting_for_the_rule(
    session, business, lamp
):
    tenant = business.tenant.id
    document, (bikes, lamps) = _order(
        session, business, "SO-306-HOLD", [(business.item, "5"), (lamp, "3")]
    )
    _stock(session, business, business.item, "5")
    core.reserve(session, tenant, bikes.id)
    _rule(session, business, "ship_complete")
    assert document.id in _rows(session, business, "order_waiting_for_completeness")

    core.hold_commitment(session, tenant, lamps.id, "customer_request")

    assert document.id not in _rows(session, business, "order_waiting_for_completeness")


from intake_review_support import reviewed_create_item
