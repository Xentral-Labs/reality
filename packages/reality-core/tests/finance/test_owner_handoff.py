"""Finance proposals retain one agent-to-owner-to-agent identity."""

import json
from decimal import Decimal

import pytest

from reality.mcp.catalog import MCP_TOOL_REGISTRY, dispatch_tool
from reality.services import core
from reality.services.finance.accounts import list_accounts
from reality.services.memberships import Principal
from reality.services.proposal_reviews import proposal_review
from reality.tools.application import approve_and_execute_proposal


def _posted_customer_invoice(session, business):
    invoice = core.create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "INV-OWNER-HANDOFF-257",
        business.customer.id,
        "100",
    )
    core.post_sales_invoice(session, business.tenant.id, invoice.id)
    return invoice


def test_agent_owner_agent_finance_handoff_uses_one_proposal_identity(
    session, business, scheduled_owner, monkeypatch
):
    tenant_id = business.tenant.id
    invoice = _posted_customer_invoice(session, business)
    arguments = {
        "mode": "payment",
        "document_id": invoice.id,
        "expected_revision": list_accounts(session, tenant_id)["revision"],
        "amount": "100",
        "allocation_amount": "100",
        "reference": "Owner-reviewed bank evidence",
        "effective_at": "2026-09-23T08:00:00Z",
    }

    prepared = MCP_TOOL_REGISTRY["finance_settlement_propose"].handler(
        session, tenant_id, arguments
    )
    proposal_id = prepared["proposal_id"]
    assert prepared["status"] == "proposed"
    assert prepared["next_step"] == {
        "review_required": True,
        "review_read": "proposal_review",
        "decision_handoff": "proposal-review",
        "required_principal": "authenticated_active_owner",
        "explicit_confirmation": True,
        "confirmation_tool": "proposal_approve_and_execute",
        "reconciliation_read": "proposal_execution_status",
        "verification_reads": ["finance.settlement.context"],
    }
    assert core.open_invoice_amount(session, tenant_id, invoice.id) == Decimal(100)

    review = proposal_review(session, tenant_id, proposal_id)
    assert review["id"] == proposal_id
    assert review["next_step"] == prepared["next_step"]
    assert review["confirmable"] is True
    assert review["preview"]["settlement"]["remaining_claim"] == "0.0000"

    monkeypatch.setenv("REALITY_AUTH_MODE", "required")
    with pytest.raises(core.InvalidOperation, match="confirming company owner"):
        dispatch_tool(
            session,
            tenant_id,
            "proposal_approve_and_execute",
            {"proposal_id": proposal_id, "approved": True},
            allowed_access=("confirm",),
        )
    assert core.open_invoice_amount(session, tenant_id, invoice.id) == Decimal(100)

    executed = approve_and_execute_proposal(
        session,
        tenant_id,
        proposal_id,
        confirming_principal=Principal(scheduled_owner.id),
    )
    receipt = json.loads(executed.output)
    assert executed.id == proposal_id
    assert executed.decided_by_user_id == scheduled_owner.id
    assert Decimal(receipt["remaining_claim"]) == 0

    reconciled = dispatch_tool(
        session,
        tenant_id,
        "proposal_execution_status",
        {"proposal_id": proposal_id},
        allowed_access=("read",),
    )
    assert reconciled["proposal_id"] == proposal_id
    assert reconciled["status"] == "executed"
    assert reconciled["receipt"] == receipt
    assert core.open_invoice_amount(session, tenant_id, invoice.id) == 0


def test_finance_review_and_reconciliation_do_not_disclose_foreign_proposal(
    session, business
):
    invoice = _posted_customer_invoice(session, business)
    tenant_id = business.tenant.id
    prepared = MCP_TOOL_REGISTRY["finance_settlement_propose"].handler(
        session,
        tenant_id,
        {
            "mode": "payment",
            "document_id": invoice.id,
            "expected_revision": list_accounts(session, tenant_id)["revision"],
            "amount": "10",
            "allocation_amount": "10",
            "reference": "Tenant boundary",
            "effective_at": "2026-09-23T08:00:00Z",
        },
    )
    foreign = core.create_tenant(session, "Foreign finance review")

    with pytest.raises(core.NotFound):
        proposal_review(session, foreign.id, prepared["proposal_id"])
    with pytest.raises(core.NotFound):
        dispatch_tool(
            session,
            foreign.id,
            "proposal_execution_status",
            {"proposal_id": prepared["proposal_id"]},
            allowed_access=("read",),
        )
