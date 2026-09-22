import json
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import BusinessEvent
from reality.services.core import (
    InvalidOperation,
    active_commitment_hold,
    create_commitment,
    hold_commitment,
    record_movement,
    reserve,
)
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
)
from reality.tools import application as application_tools
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def test_core_cancellation_requires_a_non_empty_reason(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        1,
        "2026-12-01",
    )

    with pytest.raises(InvalidOperation, match="requires a reason"):
        from reality.services.core import cancel_commitment

        cancel_commitment(
            session,
            business.tenant.id,
            commitment.id,
            reason="   ",
        )


def test_reviewed_cancellation_closes_open_remainder_and_releases_controls(
    session, business
):
    tenant_id = business.tenant.id
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        10,
        "2026-12-01",
    )
    reservation = reserve(session, tenant_id, commitment.id, 10).reservation
    hold_commitment(session, tenant_id, commitment.id, reason_code="customer_request")

    proposal = prepare_delivery_action(
        session,
        tenant_id,
        "commitment_cancel",
        {"commitment_id": commitment.id, "reason": "Customer cancelled"},
        request_id="cancel-commitment-1",
    )
    detail = delivery_proposal_detail(session, tenant_id, proposal.id)
    assert detail["review"]["effect"]["cancelled_open"] == "10"
    assert detail["review"]["effect"]["stock_changes"] is False

    executed = approve_and_execute_proposal(
        session,
        tenant_id,
        proposal.id,
        review_token=detail["review"]["token"],
        confirmed=True,
    )
    assert executed.status == "executed"
    session.refresh(commitment)
    session.refresh(reservation)
    assert commitment.status == "cancelled"
    assert reservation.status == "released"
    assert active_commitment_hold(session, tenant_id, commitment.id) is None
    verified = delivery_proposal_detail(session, tenant_id, proposal.id)
    assert verified["verification"] == "verified"
    assert verified["receipt"]["commitment_id"] == commitment.id
    assert verified["observation"] == {
        "commitment_id": commitment.id,
        "status": "cancelled",
    }
    assert verified["lifecycle"] == "executed"
    assert verified["recorded_effect"] == verified["receipt"]
    assert verified["current_observation"] == verified["observation"]
    assert verified["remaining_work"] == []
    assert verified["safe_next_action"] == "none"
    assert Decimal(detail["review"]["state"]["fulfilled"]) == 0


def test_cancellation_verification_rejects_event_that_does_not_match_intent(
    session, business
):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        1,
        "2026-12-01",
    )
    proposal = prepare_delivery_action(
        session,
        business.tenant.id,
        "commitment_cancel",
        {"commitment_id": commitment.id, "reason": "Customer cancelled"},
        request_id="cancel-intent-mismatch",
    )
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=detail["review"]["token"],
        confirmed=True,
    )
    event = session.query(BusinessEvent).filter_by(action_id=proposal.id).one()
    payload = json.loads(event.payload)
    payload["reason"] = "Different cancellation"
    event.payload = json.dumps(payload, sort_keys=True)
    session.commit()

    unresolved = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert unresolved["verification"] == "unresolved"
    assert unresolved["recorded_effect"] is None
    assert unresolved["safe_next_action"] == "reconcile"


def test_reviewed_revision_discloses_and_applies_reservation_release(session, business):
    tenant_id = business.tenant.id
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        10,
        "2026-12-01",
    )
    original = reserve(session, tenant_id, commitment.id, 10).reservation
    assert original is not None

    proposal = prepare_delivery_action(
        session,
        tenant_id,
        "commitment_revise",
        {"commitment_id": commitment.id, "quantity": "6", "note": "Customer reduced"},
        request_id="revise-commitment-1",
    )
    detail = delivery_proposal_detail(session, tenant_id, proposal.id)
    assert detail["review"]["effect"] == {
        "revised_open": "6",
        "retained_reservation_quantity": "6",
        "released_reservation_quantity": "4",
        "selection_required": False,
        "document_changes": False,
        "movement_changes": False,
    }

    executed = approve_and_execute_proposal(
        session,
        tenant_id,
        proposal.id,
        review_token=detail["review"]["token"],
        confirmed=True,
    )
    assert executed.status == "executed"
    session.refresh(original)
    assert original.status == "released"
    verified = delivery_proposal_detail(session, tenant_id, proposal.id)
    assert verified["verification"] == "verified"
    assert verified["observation"]["quantity"] == "6.0000"
    assert verified["observation"]["open"] == "6.0000"


def test_web_api_prepares_cancellation_without_bypassing_confirmation(
    session, business, monkeypatch
):
    tenant_id = business.tenant.id
    commitment = create_commitment(
        session,
        tenant_id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        4,
        "2026-12-01",
    )
    monkeypatch.setattr(
        api_module, "Session", sessionmaker(session.bind, expire_on_commit=False)
    )
    client = TestClient(web_module.app)
    base = f"/api/tenants/{tenant_id}"

    prepared = client.post(
        f"{base}/delivery-actions/prepare",
        json={
            "request_id": "web-cancel-commitment",
            "tool": "commitment_cancel",
            "arguments": {
                "commitment_id": commitment.id,
                "reason": "Supplier discontinued item",
            },
        },
    )
    assert prepared.status_code == 200, prepared.text
    review = prepared.json()
    session.refresh(commitment)
    assert commitment.status == "open"

    confirmed = client.post(
        f"{base}/change-proposals/{review['id']}/approve",
        json={"confirmed": True, "review_token": review["review"]["token"]},
    )
    assert confirmed.status_code == 200, confirmed.text
    session.refresh(commitment)
    assert commitment.status == "cancelled"


def test_cli_cancellation_previews_and_confirms_shared_action(
    session, business, monkeypatch
):
    tenant_id = business.tenant.id
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        3,
        "2026-12-01",
    )
    monkeypatch.setattr(
        cli_module, "Session", sessionmaker(session.bind, expire_on_commit=False)
    )
    monkeypatch.setattr(cli_module, "init_db", lambda: None)

    result = CliRunner().invoke(
        cli_module.app,
        [
            "commitment",
            "cancel",
            commitment.id,
            "Customer withdrew order",
            "--tenant",
            tenant_id,
            "--yes",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "cancelled_open" in result.output
    session.refresh(commitment)
    assert commitment.status == "cancelled"


def test_known_reviewed_handler_refusal_restores_proposal_without_effect(
    session, business, monkeypatch
):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        2,
        "2026-12-01",
    )
    proposal = prepare_delivery_action(
        session,
        business.tenant.id,
        "commitment_cancel",
        {"commitment_id": commitment.id, "reason": "Customer request"},
        request_id="known-domain-refusal",
    )
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    original = application_tools.TOOLS["commitment_cancel"]

    def refuse(_session, _tenant_id, _arguments):
        raise application_tools.InvalidOperation("Known refusal before effect")

    monkeypatch.setitem(
        application_tools.TOOLS,
        "commitment_cancel",
        application_tools.Tool(
            original.name, original.description, original.mutating, refuse
        ),
    )

    with pytest.raises(application_tools.InvalidOperation, match="Known refusal"):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            review_token=detail["review"]["token"],
            confirmed=True,
        )

    session.refresh(proposal)
    session.refresh(commitment)
    assert proposal.status == "proposed"
    assert commitment.status == "open"


def test_unexpected_reviewed_handler_failure_remains_unresolved(
    session, business, monkeypatch
):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        2,
        "2026-12-01",
    )
    proposal = prepare_delivery_action(
        session,
        business.tenant.id,
        "commitment_cancel",
        {"commitment_id": commitment.id, "reason": "Customer request"},
        request_id="unknown-handler-outcome",
    )
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    original = application_tools.TOOLS["commitment_cancel"]

    def interrupt(_session, _tenant_id, _arguments):
        raise RuntimeError("Connection disappeared at effect boundary")

    monkeypatch.setitem(
        application_tools.TOOLS,
        "commitment_cancel",
        application_tools.Tool(
            original.name, original.description, original.mutating, interrupt
        ),
    )

    with pytest.raises(RuntimeError, match="effect boundary"):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            review_token=detail["review"]["token"],
            confirmed=True,
        )

    session.expire_all()
    assert delivery_proposal_detail(session, business.tenant.id, proposal.id)["status"] == "executing"
