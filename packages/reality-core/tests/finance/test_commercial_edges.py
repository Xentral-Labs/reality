"""Spec 247: dunning, deposits and bad debt use shared finance controls."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import DunningNotice, LedgerEntry
from reality.mcp.catalog import dispatch_tool
from reality.services import core
from reality.services.finance.accounts import (
    create_account,
    list_accounts,
    set_default_account,
)
from reality.services.finance.credits import available_credit_rows
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def _account(session, tenant, role):
    state = list_accounts(session, tenant)
    if role in state["defaults"]:
        return
    account = create_account(
        session,
        tenant,
        code=role,
        name=role.replace("_", " ").title(),
        role=role,
        expected_revision=state["revision"],
    )
    state = list_accounts(session, tenant)
    set_default_account(
        session,
        tenant,
        role=role,
        account_id=account["id"],
        expected_revision=state["revision"],
    )


def _invoice(session, business, *, side="customer", amount="100", number="INV-EDGE-001"):
    tenant = business.tenant.id
    party = business.customer if side == "customer" else business.supplier
    kind = "sales_invoice" if side == "customer" else "supplier_invoice"
    invoice = core.create_document(
        session,
        tenant,
        kind,
        number,
        party.id,
        amount,
        document_date="2026-01-01",
    )
    getattr(core, f"post_{'sales' if side == 'customer' else 'supplier'}_invoice")(
        session, tenant, invoice.id
    )
    return invoice


def _execute(session, tenant, command, arguments):
    proposal = create_change_proposal(session, tenant, command, arguments)
    return json.loads(approve_and_execute_proposal(session, tenant, proposal.id).output)


def test_dunning_notice_keeps_invoice_and_posts_optional_fee(session, business):
    tenant = business.tenant.id
    _account(session, tenant, "dunning_fee_revenue")
    invoice = _invoice(session, business)
    result = _execute(
        session,
        tenant,
        "finance.dunning.record",
        {
            "expected_revision": list_accounts(session, tenant)["revision"],
            "invoice_ids": [invoice.id],
            "level": 2,
            "notice_date": "2026-09-21",
            "fee_amount": "5",
            "reason": "Second reminder",
            "number": "DN-2026-0001",
        },
    )
    notice = session.scalar(
        select(DunningNotice).where(DunningNotice.id == result["id"])
    )
    assert notice.level == 2 and notice.fee_amount == Decimal(5)
    assert result["invoice_ids"] == [invoice.id]
    assert core.open_invoice_amount(session, tenant, invoice.id) == 100
    assert core.open_invoice_amount(session, tenant, result["fee_document_id"]) == 5
    entries = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.posting_group_id == result["fee"]["posting_group_id"]
            )
        )
    )
    assert {entry.account for entry in entries} == {
        "accounts_receivable",
        "dunning_fee_revenue",
    }
    reversed_notice = _execute(
        session,
        tenant,
        "finance.dunning.reverse",
        {
            "expected_revision": list_accounts(session, tenant)["revision"],
            "notice_id": notice.id,
            "reason": "Reminder issued in error",
        },
    )
    assert reversed_notice["reversal_id"]
    assert core.open_invoice_amount(session, tenant, result["fee_document_id"]) == 0


def test_mcp_dunning_context_record_detail_list_and_reverse(session, business):
    tenant = business.tenant.id
    _account(session, tenant, "dunning_fee_revenue")
    invoice = _invoice(session, business, number="INV-MCP-DUNNING")
    values = {
        "invoice_ids": [invoice.id],
        "level": 1,
        "notice_date": "2026-09-23",
        "fee_amount": "2.50",
        "reason": "Explicit reminder",
        "number": "DN-MCP-257",
    }
    context = dispatch_tool(
        session, tenant, "finance_dunning_context", values, allowed_access=("read",)
    )
    prepared = dispatch_tool(
        session,
        tenant,
        "finance_dunning_record_propose",
        {**values, "expected_revision": context["revision"]},
        allowed_access=("propose",),
    )
    assert prepared["next_step"]["required_principal"] == "authenticated_active_owner"
    executed = approve_and_execute_proposal(session, tenant, prepared["proposal_id"])
    notice_id = json.loads(executed.output)["id"]

    detail = dispatch_tool(
        session,
        tenant,
        "finance_dunning_notice",
        {"notice_id": notice_id},
        allowed_access=("read",),
    )
    listed = dispatch_tool(
        session, tenant, "finance_dunning_notices", {}, allowed_access=("read",)
    )
    assert detail["fee_amount"] == "2.5000"
    assert [row["id"] for row in listed] == [notice_id]
    with pytest.raises(core.NotFound):
        dispatch_tool(
            session,
            "ten_other",
            "finance_dunning_notice",
            {"notice_id": notice_id},
            allowed_access=("read",),
        )

    revision = list_accounts(session, tenant)["revision"]
    reversal = dispatch_tool(
        session,
        tenant,
        "finance_dunning_reverse_propose",
        {
            "notice_id": notice_id,
            "reason": "Entered in error",
            "expected_revision": revision,
        },
        allowed_access=("propose",),
    )
    approve_and_execute_proposal(session, tenant, reversal["proposal_id"])
    assert dispatch_tool(
        session,
        tenant,
        "finance_dunning_notice",
        {"notice_id": notice_id},
        allowed_access=("read",),
    )["reversed"] is True


@pytest.mark.parametrize("side", ["customer", "supplier"])
def test_deposit_is_explicit_credit_and_clears_final_invoice(session, business, side):
    tenant = business.tenant.id
    invoice = _invoice(
        session,
        business,
        side=side,
        amount="80",
        number=f"INV-{side.upper()}-DEPOSIT",
    )
    deposit = _execute(
        session,
        tenant,
        "finance.deposit.record",
        {
            "expected_revision": list_accounts(session, tenant)["revision"],
            "side": side,
            "party_id": invoice.party_id,
            "amount": "100",
            "currency": "EUR",
            "reference": f"DEP-{side.upper()}-001",
            "effective_at": "2026-08-01T10:00:00+00:00",
        },
    )
    credits, _ = available_credit_rows(session, tenant, side=side)
    row = next(item for item in credits if item["document_id"] == deposit["document_id"])
    assert row["origin"] == "deposit" and Decimal(row["open"]) == 100
    clearing = _execute(
        session,
        tenant,
        "finance.deposit.clear",
        {
            "expected_revision": list_accounts(session, tenant)["revision"],
            "deposit_document_id": deposit["document_id"],
            "invoice_id": invoice.id,
            "amount": "80",
        },
    )
    assert clearing["available_after"] == "20.0000"
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0


def test_bad_debt_uses_dedicated_expense_and_never_creates_credit(session, business):
    tenant = business.tenant.id
    _account(session, tenant, "bad_debt_expense")
    invoice = _invoice(session, business, amount="100", number="INV-BAD-DEBT-001")
    core.post_customer_payment(session, tenant, invoice.id, "60")
    result = _execute(
        session,
        tenant,
        "finance.adjustment.accept",
        {
            "expected_revision": list_accounts(session, tenant)["revision"],
            "invoice_id": invoice.id,
            "amount": "25",
            "reason_category": "bad_debt",
            "reason": "Confirmed irrecoverable balance",
            "agreement": "",
            "source_record_id": None,
            "source_effect_id": None,
        },
    )
    assert core.open_invoice_amount(session, tenant, invoice.id) == 15
    entries = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.posting_group_id == result["posting_group_id"]
            )
        )
    )
    assert {entry.account for entry in entries} == {
        "accounts_receivable",
        "bad_debt_expense",
    }
    credits, _ = available_credit_rows(session, tenant, side="customer")
    assert result["document_id"] not in {row["document_id"] for row in credits}


def test_higher_revision_allows_only_the_new_quantity(session, business):
    tenant = business.tenant.id
    _, _, _, commitments = core.create_manual_order(
        session,
        tenant,
        "sales",
        "SO-OVER-001",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "source_line_id": "1",
                "item_id": business.item.id,
                "sku": business.item.sku,
                "quantity": "10",
                "unit_price": "10",
                "gross_amount": "100",
            }
        ],
        "100",
    )
    commitment = commitments[0]
    core.revise_commitment(session, tenant, commitment.id, quantity="12")
    assert core.commitment_quantity(session, tenant, commitment.id) == 12
    assert commitment.quantity == 10
