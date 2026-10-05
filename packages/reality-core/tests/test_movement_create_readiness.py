"""Spec 294 FR-006, restoring spec 275 FR-005: Record shipment honours prepayment.

A prepayment order must stay non-shippable until paid. `shipment_dispatch`
refused it, but a reviewed `movement_create` shipment against the same promise
went through, so an unpaid prepayment order could leave through *Record
shipment*. Both routes now share the payment part of the readiness decision.
"""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import Movement
from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.tools.application import approve_and_execute_proposal


def _prepayment_order(session, business, *, reserve=True):
    tenant = business.tenant.id
    core.create_payment_term(
        session, tenant, "PREPAY", "Prepayment", 0, requires_prepayment=True
    )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    _, _, lines, commitments = core.create_manual_order(
        session,
        tenant,
        "sales",
        "SO-294-PREPAY",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "50.00",
                "gross_amount": "100.00",
            }
        ],
        "100.00",
        payment_term_code="PREPAY",
    )
    if reserve:
        core.reserve(session, tenant, commitments[0].id)
    return lines[0], commitments[0]


def _prepare_shipment(session, business, commitment, request_id):
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "movement_create",
        {
            "movement_type": "shipment",
            "item_id": business.item.id,
            "quantity": "2",
            "from_location_id": business.location.id,
            "commitment_id": commitment.id,
        },
        request_id=request_id,
    )


def _confirm(session, business, proposal):
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )


def _shipments(session, business):
    return session.scalar(
        select(func.count())
        .select_from(Movement)
        .where(Movement.tenant_id == business.tenant.id, Movement.type == "shipment")
    )


def test_record_shipment_refuses_an_unpaid_prepayment_order(session, business):
    _, commitment = _prepayment_order(session, business)

    with pytest.raises(core.InvalidOperation) as refused:
        _prepare_shipment(session, business, commitment, "ship-unpaid")

    assert refused.value.code == "shipment_blocked_readiness"
    assert "prepayment" in refused.value.values["blockers"]
    assert _shipments(session, business) == 0


def test_record_shipment_refuses_at_confirmation_when_payment_is_reversed(
    session, business
):
    """Preparation and execution both enforce current readiness (spec 275 FR-010)."""
    tenant = business.tenant.id
    line, commitment = _prepayment_order(session, business)
    receipt = core.record_sales_invoice(session, tenant, line.id, "2", "100.00", "RE-P")
    invoice_id = next(
        row["id"] for row in receipt["records"] if row["family"] == "document"
    )
    entries = core.post_customer_payment(session, tenant, invoice_id, "100.00")
    proposal = _prepare_shipment(session, business, commitment, "ship-reversed")

    core.reverse_ledger_posting_group(
        session, tenant, entries[0].posting_group_id, reason="Payment bounced"
    )

    with pytest.raises(core.InvalidOperation) as refused:
        _confirm(session, business, proposal)
    assert refused.value.code == "shipment_blocked_readiness"
    assert _shipments(session, business) == 0


def test_record_shipment_ships_a_paid_prepayment_order(session, business):
    """Positive control: once paid, the same shipment is recorded."""
    tenant = business.tenant.id
    line, commitment = _prepayment_order(session, business)
    receipt = core.record_sales_invoice(session, tenant, line.id, "2", "100.00", "RE-P")
    invoice_id = next(
        row["id"] for row in receipt["records"] if row["family"] == "document"
    )
    core.post_customer_payment(session, tenant, invoice_id, "100.00")

    executed = _confirm(
        session, business, _prepare_shipment(session, business, commitment, "ship-paid")
    )

    assert executed.status == "executed"
    assert core.fulfilled_quantity(session, tenant, commitment.id) == Decimal(2)


def test_record_shipment_still_records_an_unreserved_net_term_delivery(
    session, business
):
    """A supported net-term delivery needs no reservation to record its physical shipment."""
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    document = core.create_document(
        session, tenant, "sales_order", "NET-TERM-SHIPMENT", business.customer.id, "0"
    )
    commitment = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "2",
        "2026-10-01",
        document_id=document.id,
    )

    executed = _confirm(
        session, business, _prepare_shipment(session, business, commitment, "ship-net")
    )

    assert executed.status == "executed"
    assert core.fulfilled_quantity(session, tenant, commitment.id) == Decimal(2)


# --- Every person-facing way of recording a shipment (code review of #261) ------


def test_the_movement_tool_handler_refuses_an_unpaid_prepayment_order(
    session, business
):
    """Practice companies execute the handler without the delivery review."""
    from reality.tools.application import TOOLS

    _, commitment = _prepayment_order(session, business)

    with pytest.raises(core.InvalidOperation) as refused:
        TOOLS["movement_create"].handler(
            session,
            business.tenant.id,
            {
                "movement_type": "shipment",
                "item_id": business.item.id,
                "quantity": "2",
                "from_location_id": business.location.id,
                "commitment_id": commitment.id,
            },
        )
    assert refused.value.code == "shipment_blocked_readiness"
    assert _shipments(session, business) == 0


def test_the_cli_refuses_to_record_an_unpaid_prepayment_shipment(
    session, business, monkeypatch
):
    from sqlalchemy.orm import sessionmaker
    from typer.testing import CliRunner

    from reality.cli import app as cli_module

    _, commitment = _prepayment_order(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)

    result = CliRunner().invoke(
        cli_module.app,
        [
            "movement",
            "record",
            "shipment",
            business.item.id,
            "2",
            "--tenant",
            business.tenant.id,
            "--from-location-id",
            business.location.id,
            "--commitment-id",
            commitment.id,
        ],
    )

    assert result.exit_code != 0
    assert "Shipment blocked" in result.output
    assert _shipments(session, business) == 0


def test_the_movement_endpoint_refuses_an_unpaid_prepayment_shipment(
    session, business, monkeypatch
):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web import api as api_module
    from reality.web import app as web_module

    _, commitment = _prepayment_order(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)

    response = client.post(
        f"/api/tenants/{business.tenant.id}/movements",
        json={
            "type": "shipment",
            "item_id": business.item.id,
            "quantity": "2",
            "from_location_id": business.location.id,
            "commitment_id": commitment.id,
        },
    )

    assert response.status_code in {400, 409, 422}, response.text
    assert "shipment_blocked_readiness" in response.text
    assert _shipments(session, business) == 0
    # Positive control: the same endpoint records an ordinary net-term shipment.
    ordinary = core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        "2026-10-01",
    )
    recorded = client.post(
        f"/api/tenants/{business.tenant.id}/movements",
        json={
            "type": "shipment",
            "item_id": business.item.id,
            "quantity": "1",
            "from_location_id": business.location.id,
            "commitment_id": ordinary.id,
        },
    )
    assert recorded.status_code == 201, recorded.text
