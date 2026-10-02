"""Spec 312: customer pickup and the time goods moved versus when it was recorded."""

import json
from datetime import timedelta

import pytest
from unified_fixtures import delivery_fixture

from reality.db.core import Movement
from reality.services import core
from reality.services.shipments import shipment_explain
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def _dispatch(session, business, fixture, quantity="2", **extra):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": fixture.commitment.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": quantity,
                }
            ],
            **extra,
        },
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )
    return json.loads(executed.output)


def _stock_since(session, business, days=10, quantity="10"):
    """Stock that arrived well before any stated shipment time."""
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        occurred_at=core.now() - timedelta(days=days),
    )


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def test_a_customer_collects_and_says_who(session, business):
    tenant = business.tenant.id
    fixture = delivery_fixture(session, business, quantity="2")
    core.reserve(session, tenant, fixture.commitment.id)

    output = _dispatch(
        session, business, fixture, delivery_mode="pickup", collected_by="M. Müller"
    )

    detail = shipment_explain(session, tenant, output["shipment_id"])
    assert (detail["delivery_mode"], detail["collected_by"]) == ("pickup", "M. Müller")
    assert detail["packages"][0]["carrier"] is None
    session.refresh(fixture.commitment)
    assert fixture.commitment.status == "fulfilled"


def test_a_pickup_takes_no_carrier_and_is_for_customers_only(session, business):
    tenant = business.tenant.id
    fixture = delivery_fixture(session, business, quantity="4")
    core.reserve(session, tenant, fixture.commitment.id)
    _refused(
        "shipment_pickup_carrier_refused",
        lambda: _dispatch(
            session, business, fixture, delivery_mode="pickup", carrier="DHL"
        ),
    )
    _refused(
        "shipment_delivery_mode_invalid",
        lambda: _dispatch(session, business, fixture, delivery_mode="drone"),
    )
    _refused(
        "shipment_collector_pickup_only",
        lambda: _dispatch(
            session, business, fixture, carrier="DHL", collected_by="Someone"
        ),
    )
    from reality.services.shipments import record_shipment_notice

    _refused(
        "shipment_pickup_customer_only",
        lambda: record_shipment_notice(
            session,
            tenant,
            direction="inbound",
            purpose="supplier_delivery",
            counterparty_id=business.supplier.id,
            delivery_mode="pickup",
        ),
    )
    # Positive control: by carrier, as before, reads as carrier.
    output = _dispatch(session, business, fixture, carrier="DHL", tracking_number="T-1")
    assert (
        shipment_explain(session, tenant, output["shipment_id"])["delivery_mode"]
        == "carrier"
    )


def test_movements_carry_when_the_goods_left(session, business):
    tenant = business.tenant.id
    fixture = delivery_fixture(session, business, quantity="2")
    core.reserve(session, tenant, fixture.commitment.id)
    _stock_since(session, business)
    left = core.now() - timedelta(days=3)

    output = _dispatch(session, business, fixture, occurred_at=left.isoformat())

    (movement,) = [
        session.get(Movement, (tenant, movement_id))
        for movement_id in output["movement_ids"]
    ]
    assert core.utc_datetime(movement.occurred_at) == left
    detail = shipment_explain(session, tenant, output["shipment_id"])
    assert detail["moved_at"] == left
    assert detail["confirmation_lag_seconds"] >= 3 * 24 * 3600 - 5


def test_a_future_time_is_refused_and_no_time_has_no_lag(session, business):
    tenant = business.tenant.id
    fixture = delivery_fixture(session, business, quantity="2")
    core.reserve(session, tenant, fixture.commitment.id)
    _refused(
        "shipment_occurred_at_future",
        lambda: _dispatch(
            session,
            business,
            fixture,
            occurred_at=(core.now() + timedelta(days=1)).isoformat(),
        ),
    )
    output = _dispatch(session, business, fixture)
    detail = shipment_explain(session, tenant, output["shipment_id"])
    assert (detail["moved_at"], detail["confirmation_lag_seconds"]) == (None, None)


def test_an_agent_records_a_pickup_through_the_strict_schema(session, business):
    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.mcp.server import _reject_unknown_fields

    fixture = delivery_fixture(session, business, quantity="1")
    core.reserve(session, business.tenant.id, fixture.commitment.id)
    _stock_since(session, business)
    arguments = {
        "purpose": "customer_delivery",
        "counterparty_id": business.customer.id,
        "delivery_mode": "pickup",
        "collected_by": "Fahrer Kunde",
        "occurred_at": (core.now() - timedelta(hours=2)).isoformat(),
        "movements": [
            {
                "commitment_id": fixture.commitment.id,
                "item_id": business.item.id,
                "from_location_id": business.location.id,
                "quantity": "1",
            }
        ],
    }
    definition = MCP_TOOL_REGISTRY["shipment_dispatch_propose"]
    _reject_unknown_fields(definition.input_schema, arguments)

    proposed = definition.handler(session, business.tenant.id, arguments)

    assert proposed["proposal_id"]


def test_goods_cannot_leave_before_they_arrived(session, business):
    """A late confirmation cannot date a shipment before its stock came in."""
    from reality.services.delivery_actions import prepare_delivery_action

    tenant = business.tenant.id
    fixture = delivery_fixture(session, business, quantity="2")
    core.reserve(session, tenant, fixture.commitment.id)
    # The fixture's stock was received now; a shipment a week ago had nothing.
    week_ago = (core.now() - timedelta(days=7)).isoformat()
    _refused(
        "shipment_occurred_before_stock",
        lambda: _dispatch(session, business, fixture, occurred_at=week_ago),
    )
    # The review refuses it too, and a pickup on a supplier return.
    _refused(
        "shipment_occurred_before_stock",
        lambda: prepare_delivery_action(
            session,
            tenant,
            "shipment_dispatch",
            {
                "purpose": "customer_delivery",
                "counterparty_id": business.customer.id,
                "occurred_at": week_ago,
                "movements": [
                    {
                        "commitment_id": fixture.commitment.id,
                        "item_id": business.item.id,
                        "from_location_id": business.location.id,
                        "quantity": "2",
                    }
                ],
            },
            request_id="moved-early",
        ),
    )
    # Positive control: now, after the receipt, the stock is there.
    _dispatch(session, business, fixture, occurred_at=core.now().isoformat())
