import json

import pytest
from conftest import record_by_id
from sqlalchemy import func, select
from unified_fixtures import delivery_fixture

from reality.db.core import Movement, Shipment
from reality.services.core import (
    InvalidOperation,
    create_commitment,
    record_movement,
    reserve,
)
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def test_notice_requires_proposal_and_has_no_stock_effect(session, business):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_notice_record",
        {
            "direction": "inbound",
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "carrier": "DHL",
            "tracking_number": "IN-123",
        },
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(Shipment)
            .where(Shipment.tenant_id == business.tenant.id)
        )
        == 0
    )

    token = json.loads(proposal.input)["_delivery_review"]["token"]
    with pytest.raises(InvalidOperation, match="review"):
        approve_and_execute_proposal(session, business.tenant.id, proposal.id)
    executed = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=token,
        confirmed=True,
    )
    output = json.loads(executed.output)
    assert output["shipment_id"]
    assert (
        session.scalar(
            select(func.count())
            .select_from(Movement)
            .where(Movement.tenant_id == business.tenant.id)
        )
        == 0
    )

    replayed = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=token,
        confirmed=True,
    )
    assert replayed.id == executed.id
    assert json.loads(replayed.output) == output


def test_notice_review_rejects_changed_counterparty_state(session, business):
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_notice_record",
        {
            "direction": "inbound",
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
        },
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    # Add a role directly as fixture setup, never as an application path.
    from reality.db.core import PartyRole, uid

    session.add(
        PartyRole(
            id=uid("pro"),
            tenant_id=business.tenant.id,
            party_id=business.supplier.id,
            role="customer",
        )
    )
    session.commit()
    with pytest.raises(InvalidOperation, match="fresh review"):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            review_token=token,
            confirmed=True,
        )
    assert proposal.status == "proposed"


def test_notice_lost_response_reconciles_without_second_effect(session, business):
    from reality.services.delivery_actions import reconcile_delivery
    from reality.services.shipments import record_shipment_notice

    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_notice_record",
        {
            "direction": "inbound",
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
        },
    )
    proposal.status = "executing"
    session.commit()
    shipment, package, event = record_shipment_notice(
        session,
        business.tenant.id,
        direction="inbound",
        purpose="supplier_delivery",
        counterparty_id=business.supplier.id,
        action_id=proposal.id,
    )

    result = reconcile_delivery(session, business.tenant.id, proposal.id)

    assert result["status"] == "executed"
    assert result["verification"] == "verified"
    assert result["receipt"] == {
        "shipment_id": shipment.id,
        "package_id": package.id,
        "event_id": event.id,
    }
    assert session.scalar(select(func.count()).select_from(Shipment)) == 1


def test_tracking_event_and_supersession_are_separate_reviewed_append_only_actions(
    session, business
):
    from reality.db.core import ShipmentEvent, ShipmentEventSupersession
    from reality.services.shipments import record_shipment_notice

    shipment, package, announced = record_shipment_notice(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
    )
    event_proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_event_record",
        {
            "shipment_id": shipment.id,
            "shipment_package_id": package.id,
            "event_type": "in_transit",
            "reporter_type": "carrier",
        },
    )
    assert session.scalar(select(func.count()).select_from(ShipmentEvent)) == 1
    event_token = json.loads(event_proposal.input)["_delivery_review"]["token"]
    event_result = approve_and_execute_proposal(
        session,
        business.tenant.id,
        event_proposal.id,
        review_token=event_token,
        confirmed=True,
    )
    event_id = json.loads(event_result.output)["event_id"]
    assert event_id != announced.id

    correction_proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_event_supersede",
        {"event_id": event_id, "reason": "Carrier correction"},
    )
    assert (
        session.scalar(select(func.count()).select_from(ShipmentEventSupersession)) == 0
    )
    correction_token = json.loads(correction_proposal.input)["_delivery_review"][
        "token"
    ]
    correction_result = approve_and_execute_proposal(
        session,
        business.tenant.id,
        correction_proposal.id,
        review_token=correction_token,
        confirmed=True,
    )
    receipt = json.loads(correction_result.output)
    assert receipt["event_id"] == event_id
    assert receipt["supersession_id"]
    original = record_by_id(session, ShipmentEvent, event_id)
    assert original.event_type == "in_transit"


def test_dispatch_review_rejects_changed_stock_state(session, business):
    fixture = delivery_fixture(session, business, quantity="2")
    reserve(session, business.tenant.id, fixture.commitment.id)
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
                    "quantity": "2",
                }
            ],
        },
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        1,
        to_location_id=business.location.id,
    )

    with pytest.raises(InvalidOperation, match="fresh review"):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            review_token=token,
            confirmed=True,
        )


def test_receive_confirmation_replays_one_atomic_package(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        3,
        None,
    )
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "movements": [
                {
                    "commitment_id": commitment.id,
                    "item_id": business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": "3",
                }
            ],
        },
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    first = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=token,
        confirmed=True,
    )
    replay = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=token,
        confirmed=True,
    )
    receipt = json.loads(first.output)

    assert replay.id == first.id
    assert json.loads(replay.output) == receipt
    assert (
        session.scalar(
            select(func.count())
            .select_from(Movement)
            .where(Movement.shipment_package_id == receipt["package_id"])
        )
        == 1
    )
