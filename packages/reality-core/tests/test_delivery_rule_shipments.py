"""Spec 306 FR-002: ship complete in readiness and on every person-facing shipment path."""

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.delivery_rules import state_delivery_rule
from reality.services.fulfillment_readiness import fulfillment_readiness
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


@pytest.fixture
def lamp(session, business):
    return reviewed_create_item(session, business.tenant.id, "LAMP-306", "Lamp 306")


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


def _ship_complete(session, business):
    state_delivery_rule(
        session,
        business.tenant.id,
        "ship_complete",
        "Customer refuses partial deliveries",
        party_id=business.customer.id,
    )


def _dispatch(session, business, tracking, lines):
    """A reviewed packaged dispatch of (commitment, item, quantity) lines."""
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "carrier": "DHL",
            "tracking_number": tracking,
            "movements": [
                {
                    "commitment_id": commitment.id,
                    "item_id": item.id,
                    "from_location_id": business.location.id,
                    "quantity": quantity,
                }
                for commitment, item, quantity in lines
            ],
        },
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=token,
        confirmed=True,
    )


def _single_shipment(session, business, commitment, item, quantity, request):
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "movement_create",
        {
            "movement_type": "shipment",
            "commitment_id": commitment.id,
            "item_id": item.id,
            "from_location_id": business.location.id,
            "quantity": quantity,
        },
        request_id=request,
    )


def _refused(code, call):
    with pytest.raises(core.InvalidOperation) as refused:
        call()
    assert refused.value.code == code, refused.value.code
    return refused.value


def test_readiness_waits_for_the_whole_order(session, business, lamp):
    tenant = business.tenant.id
    _, (bikes, lamps) = _order(
        session, business, "SO-306-R", [(business.item, "5"), (lamp, "3")]
    )
    _stock(session, business, business.item, "5")
    _stock(session, business, lamp, "1")
    core.reserve(session, tenant, bikes.id)
    core.reserve(session, tenant, lamps.id)
    # Positive control: without a rule the reserved bikes are ready.
    assert fulfillment_readiness(session, tenant, bikes.id).ship_ready

    _ship_complete(session, business)

    readiness = fulfillment_readiness(session, tenant, bikes.id)
    assert not readiness.ship_ready
    assert "ship_complete_incomplete" in readiness.blocker_codes
    # A part of a line is incomplete as well.
    _stock(session, business, lamp, "2")
    core.reserve(session, tenant, lamps.id)
    assert fulfillment_readiness(session, tenant, bikes.id).ship_ready
    partial = fulfillment_readiness(
        session, tenant, bikes.id, proposed_quantity=Decimal(2)
    )
    assert "ship_complete_incomplete" in partial.blocker_codes


def test_every_shipment_path_refuses_a_partial_order(session, business, lamp):
    tenant = business.tenant.id
    _, (bikes, lamps) = _order(
        session, business, "SO-306-S", [(business.item, "5"), (lamp, "3")]
    )
    _stock(session, business, business.item, "5")
    _stock(session, business, lamp, "3")
    core.reserve(session, tenant, bikes.id)
    core.reserve(session, tenant, lamps.id)
    _ship_complete(session, business)

    # One line alone, as a package or as a single shipment.
    error = _refused(
        "shipment_ship_complete_partial",
        lambda: _dispatch(session, business, "TRK-1", [(bikes, business.item, "5")]),
    )
    assert error.values["order"] == "SO-306-S"
    _refused(
        "shipment_ship_complete_partial",
        lambda: _single_shipment(session, business, bikes, business.item, "5", "s1"),
    )
    # Both lines, but one of them partly.
    _refused(
        "shipment_ship_complete_partial",
        lambda: _dispatch(
            session,
            business,
            "TRK-2",
            [(bikes, business.item, "5"), (lamps, lamp, "2")],
        ),
    )

    executed = _dispatch(
        session,
        business,
        "TRK-3",
        [(bikes, business.item, "5"), (lamps, lamp, "3")],
    )
    assert executed.status == "executed"
    assert core.stock_at(session, tenant, lamp.id) == 0


def test_a_lifted_order_ships_in_parts_while_others_wait(session, business, lamp):
    tenant = business.tenant.id
    lifted, (bikes, _) = _order(
        session, business, "SO-306-L", [(business.item, "5"), (lamp, "3")]
    )
    _, (other_bikes, _) = _order(
        session, business, "SO-306-W", [(business.item, "2"), (lamp, "1")]
    )
    _stock(session, business, business.item, "7")
    core.reserve(session, tenant, bikes.id)
    core.reserve(session, tenant, other_bikes.id)
    _ship_complete(session, business)

    state_delivery_rule(
        session,
        tenant,
        "partial_allowed",
        "Customer agreed by phone",
        document_id=lifted.id,
    )

    assert (
        _dispatch(session, business, "TRK-L", [(bikes, business.item, "5")]).status
        == "executed"
    )
    _refused(
        "shipment_ship_complete_partial",
        lambda: _dispatch(
            session, business, "TRK-W", [(other_bikes, business.item, "2")]
        ),
    )


def test_cancelled_and_shipped_lines_count_as_complete(session, business, lamp):
    tenant = business.tenant.id
    _, (bikes, lamps) = _order(
        session, business, "SO-306-C", [(business.item, "5"), (lamp, "3")]
    )
    _stock(session, business, business.item, "5")
    core.reserve(session, tenant, bikes.id)
    _ship_complete(session, business)
    assert not fulfillment_readiness(session, tenant, bikes.id).ship_ready

    core.cancel_commitment(session, tenant, lamps.id, reason="Customer drops lamps")

    assert fulfillment_readiness(session, tenant, bikes.id).ship_ready
    assert (
        _dispatch(session, business, "TRK-C", [(bikes, business.item, "5")]).status
        == "executed"
    )


def test_a_movement_recorded_as_stated_is_not_refused(session, business, lamp):
    """The rule binds what a person ships through the reviewed paths, not the core
    record a source interpretation writes when a source states goods left."""
    tenant = business.tenant.id
    _, (bikes, _) = _order(
        session, business, "SO-306-I", [(business.item, "5"), (lamp, "3")]
    )
    _stock(session, business, business.item, "5")
    _ship_complete(session, business)

    # A source states the goods left: recorded as stated (spec 294 FR-006).
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
        commitment_id=bikes.id,
    )

    assert core.stock_at(session, tenant, business.item.id) == 0


def test_the_fulfillment_queue_names_the_rule(session, business, lamp):
    from reality.services import projections

    tenant = business.tenant.id
    _, (bikes, lamps) = _order(
        session, business, "SO-306-Q", [(business.item, "5"), (lamp, "3")]
    )
    _stock(session, business, business.item, "5")
    core.reserve(session, tenant, bikes.id)

    def reasons():
        projections.refresh_operational_projections(session, tenant, force=True)
        return {
            line["commitment_id"]: line["blocking_reasons"]
            for row in projections.projection_rows(
                session, tenant, projections.FULFILLMENT_QUEUE
            )
            for line in row["lines"]
        }

    # Positive control: without a rule the reserved bikes are not blocked.
    assert reasons()[bikes.id] == []
    _ship_complete(session, business)

    assert "ship_complete_incomplete" in reasons()[bikes.id]
    assert "insufficient_reservation" in reasons()[lamps.id]


# --- review round (T017) ---------------------------------------------------------------


def test_a_line_split_across_two_warehouses_ships_complete(session, business, lamp):
    tenant = business.tenant.id
    munich = reviewed_create_location(session, tenant, "Munich 306")
    _, (bikes,) = _order(session, business, "SO-306-SPLIT", [(business.item, "5")])
    _stock(session, business, business.item, "3")
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "2",
        to_location_id=munich.id,
    )
    core.reserve(session, tenant, bikes.id, "3")
    core.reserve(session, tenant, bikes.id, "2", location_id=munich.id)
    _ship_complete(session, business)
    proposal = create_change_proposal(
        session,
        tenant,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "carrier": "DHL",
            "tracking_number": "TRK-SPLIT",
            "movements": [
                {
                    "commitment_id": bikes.id,
                    "item_id": business.item.id,
                    "from_location_id": location,
                    "quantity": quantity,
                }
                for location, quantity in (
                    (business.location.id, "3"),
                    (munich.id, "2"),
                )
            ],
        },
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]

    executed = approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=token, confirmed=True
    )

    assert executed.status == "executed"
    assert core.stock_at(session, tenant, business.item.id) == 0


def test_a_single_line_order_ships_complete_as_one_shipment(session, business):
    tenant = business.tenant.id
    _, (bikes,) = _order(session, business, "SO-306-ONE", [(business.item, "5")])
    _stock(session, business, business.item, "5")
    core.reserve(session, tenant, bikes.id)
    _ship_complete(session, business)

    proposal = _single_shipment(session, business, bikes, business.item, "5", "one")

    assert json.loads(proposal.input)["_delivery_review"]["token"]
    _refused(
        "shipment_ship_complete_partial",
        lambda: _single_shipment(session, business, bikes, business.item, "4", "four"),
    )


def test_a_quantity_that_is_no_number_keeps_its_own_refusal(session, business, lamp):
    _, (bikes, _) = _order(
        session, business, "SO-306-NAN", [(business.item, "5"), (lamp, "3")]
    )
    _ship_complete(session, business)

    # The movement's own quantity check answers, as it does without a rule.
    with pytest.raises(ArithmeticError):
        _dispatch(session, business, "TRK-NAN", [(bikes, business.item, "abc")])


from intake_review_support import reviewed_create_item, reviewed_create_location
