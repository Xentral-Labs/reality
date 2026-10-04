"""Spec 318: historical fee claims use canonical settlement, never renewed dunning."""

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import Document, LedgerEntry, SourceRecord
from reality.services import core, dunning
from reality.services.credit_exposure import credit_exposure
from reality.services.finance.accounts import (
    create_account,
    list_accounts,
    set_default_account,
)
from reality.services.finance.settlement import adjustment_context
from reality.services.finance.settlement_flows import (
    preview_settlement,
    settlement_context,
)
from reality.services.finance.worklists import overdue_document_ids
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from reality.web.read_models import aging_page, open_item_page


def execute(session, tenant, command, values):
    proposal = create_change_proposal(
        session, tenant, command, values, actor_type="human"
    )
    return json.loads(approve_and_execute_proposal(session, tenant, proposal.id).output)


def fee_story(session, business, kind):
    tenant = business.tenant.id
    role = "dunning_fee_revenue" if kind == "dunning" else "payment_fee_expense"
    state = list_accounts(session, tenant)
    if role not in state["defaults"]:
        account = create_account(
            session,
            tenant,
            code=role,
            name=role,
            role=role,
            expected_revision=state["revision"],
        )
        set_default_account(
            session,
            tenant,
            role=role,
            account_id=account["id"],
            expected_revision=list_accounts(session, tenant)["revision"],
        )
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        core.uid("inv"),
        business.customer.id,
        "100",
        document_date="2026-01-01",
    )
    core.post_sales_invoice(session, tenant, invoice.id)
    if kind == "dunning":
        execute(
            session,
            tenant,
            "finance.dunning.record",
            {
                "expected_revision": list_accounts(session, tenant)["revision"],
                "invoice_ids": [invoice.id],
                "level": 1,
                "notice_date": "2026-10-02",
                "fee_amount": "5",
            },
        )
        fee = session.scalar(
            select(Document).where(
                Document.tenant_id == tenant, Document.type == "dunning_fee_charge"
            )
        )
    else:
        payment = core.post_customer_payment(session, tenant, invoice.id, "100")[0]
        receipt = execute(
            session,
            tenant,
            "finance.payment.return",
            {
                "payment_document_id": payment.document_id,
                "kind": "direct_debit_return",
                "returned_on": "2026-10-02",
                "reason": "Returned payment",
                "fee_amount": "5",
                "fee_bearer": "customer",
            },
        )
        fee = core._tenant_record(
            session, Document, tenant, receipt["fee_charge_document_id"]
        )
    assert fee is not None
    return invoice, fee


@pytest.mark.parametrize("kind", ["dunning", "return"])
def test_historical_fee_is_a_separate_claim_on_shared_and_web_reads(
    session, business, kind
):
    tenant = business.tenant.id
    invoice, fee = fee_story(session, business, kind)
    counts = tuple(
        session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        for model in (LedgerEntry, SourceRecord)
    )
    rows = {
        row["document"].id: row for row in core.financial_open_items(session, tenant)
    }
    assert rows[fee.id]["open"] == Decimal(5)
    assert rows[fee.id]["origin"] == "fee"
    assert rows[fee.id]["control"].source_record_id == fee.source_record_id
    assert sum(row["open"] for row in rows.values()) == Decimal(105)
    web, pager = open_item_page(session, tenant)
    assert {row["document"].id for row in web} == {invoice.id, fee.id}
    assert pager.total == 2
    assert credit_exposure(session, tenant, business.customer.id)["open_invoices"][
        "amount"
    ] == Decimal(105)
    assert counts == tuple(
        session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        for model in (LedgerEntry, SourceRecord)
    )


@pytest.mark.parametrize("kind", ["dunning", "return"])
def test_fee_has_no_inherited_aging_discount_or_dunning(session, business, kind):
    tenant = business.tenant.id
    _, fee = fee_story(session, business, kind)
    core.create_payment_term(
        session,
        tenant,
        "FEE-TERM",
        "Invoice discount",
        30,
        discount_percent="2",
        discount_days=10,
    )
    reviewed_update_party(
        session,
        tenant,
        business.customer.id,
        business.customer.name,
        "customer",
        payment_term_code="FEE-TERM",
    )
    moment = datetime(2027, 1, 1, tzinfo=UTC)
    shared = next(
        row
        for row in core.aging_register(session, tenant, as_of=moment)
        if row["document"].id == fee.id
    )
    assert shared["due_date"] is None
    assert shared["days_overdue"] is None
    assert shared["payment_term"] is None
    assert shared["discount_date"] is None
    web, _ = aging_page(session, tenant, as_of=moment)
    assert next(row for row in web if row["document"].id == fee.id)["due_date"] is None
    assert fee.id not in overdue_document_ids(session, tenant, as_of=moment)
    with pytest.raises(core.InvalidOperation):
        dunning.preview_notice(
            session,
            tenant,
            {
                "invoice_ids": [fee.id],
                "level": 1,
                "notice_date": "2027-01-01",
                "fee_amount": "0",
                "reason": "",
                "number": "",
            },
        )
    with pytest.raises(core.InvalidOperation):
        adjustment_context(session, tenant, fee.id)


@pytest.mark.parametrize("kind", ["dunning", "return"])
def test_fee_payment_is_reviewed_partial_replayable_and_reversible(
    session, business, kind
):
    tenant = business.tenant.id
    invoice, fee = fee_story(session, business, kind)
    core.post_customer_payment(session, tenant, invoice.id, "100")
    assert settlement_context(session, tenant, fee.id)["side"] == "customer"
    assert settlement_context(session, tenant, fee.id)["reduction_allowed"] is False
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.settlement.apply",
        {
            "document_id": fee.id,
            "mode": "payment",
            "amount": "2",
            "allocation_amount": "2",
            "reference": "Fee payment",
            "effective_at": "2026-10-03T08:00:00Z",
            "expected_revision": list_accounts(session, tenant)["revision"],
        },
        actor_type="human",
    )
    assert core.open_invoice_amount(session, tenant, fee.id) == 5
    receipt = json.loads(
        approve_and_execute_proposal(session, tenant, proposal.id).output
    )
    assert core.open_invoice_amount(session, tenant, fee.id) == 3
    assert (
        json.loads(approve_and_execute_proposal(session, tenant, proposal.id).output)
        == receipt
    )
    core.reverse_ledger_posting_group(
        session,
        tenant,
        receipt["payment"]["posting_group_id"],
        reason="Fee payment returned",
    )
    assert core.open_invoice_amount(session, tenant, fee.id) == 5
    control = core._settlement_control_entry(session, tenant, fee.id)
    core.reverse_ledger_posting_group(
        session, tenant, control.posting_group_id, reason="Fee withdrawn"
    )
    row = next(
        row
        for row in core.financial_open_items(session, tenant)
        if row["document"].id == fee.id
    )
    assert row["status"] == "reversed"
    assert row["open"] == 0


@pytest.mark.parametrize("kind", ["dunning", "return"])
def test_existing_credit_pays_fee_with_scope_amount_and_discount_guards(
    session, business, kind
):
    tenant = business.tenant.id
    _, fee = fee_story(session, business, kind)
    credit = core.record_customer_payment(
        session,
        tenant,
        party_id=business.customer.id,
        amount="10",
        currency="EUR",
        payment_number=core.uid("pay"),
    )[0]
    context = settlement_context(session, tenant, credit.document_id)
    assert fee.id in {choice["id"] for choice in context["invoices"]}
    values = {
        "document_id": credit.document_id,
        "mode": "allocate_credit",
        "invoice_id": fee.id,
        "amount": "5",
        "expected_revision": context["revision"],
    }
    with pytest.raises(core.InvalidOperation):
        preview_settlement(session, tenant, values | {"amount": "6"})
    other_currency = core.record_customer_payment(
        session,
        tenant,
        party_id=business.customer.id,
        amount="5",
        currency="USD",
        payment_number=core.uid("pay"),
    )[0]
    values["expected_revision"] = list_accounts(session, tenant)["revision"]
    with pytest.raises(core.InvalidOperation, match="same party, currency and account"):
        preview_settlement(
            session, tenant, values | {"document_id": other_currency.document_id}
        )
    foreign = core.create_tenant(session, "Other fee owner")
    assert core.financial_open_items(session, foreign.id, document_ids={fee.id}) == []
    with pytest.raises(core.NotFound):
        settlement_context(session, foreign.id, fee.id)
    with pytest.raises(core.InvalidOperation):
        preview_settlement(
            session,
            tenant,
            {
                "document_id": fee.id,
                "mode": "payment",
                "amount": "4",
                "allocation_amount": "4",
                "reference": "No discount on fees",
                "effective_at": "2026-10-03T08:00:00Z",
                "expected_revision": values["expected_revision"],
                "reduction": {
                    "amount": "1",
                    "reason_category": "early_payment_discount",
                    "reason": "Not entitled",
                },
            },
        )
    execute(session, tenant, "finance.settlement.apply", values)
    assert core.open_invoice_amount(session, tenant, fee.id) == 0


@pytest.mark.parametrize("bearer,amount", [("company", "5"), ("none", "0")])
def test_company_borne_and_zero_fees_create_no_customer_claim(
    session, business, bearer, amount
):
    tenant = business.tenant.id
    _, first_fee = fee_story(session, business, "return")
    invoice = core.create_document(
        session, tenant, "sales_invoice", core.uid("inv"), business.customer.id, "100"
    )
    core.post_sales_invoice(session, tenant, invoice.id)
    payment = core.post_customer_payment(session, tenant, invoice.id, "100")[0]
    receipt = execute(
        session,
        tenant,
        "finance.payment.return",
        {
            "payment_document_id": payment.document_id,
            "kind": "direct_debit_return",
            "returned_on": "2026-10-02",
            "reason": "Returned",
            "fee_amount": amount,
            "fee_bearer": bearer,
        },
    )
    assert receipt["fee_charge_document_id"] is None
    rows = core.financial_open_items(session, tenant)
    assert [row["document"].id for row in rows if row["origin"] == "fee"] == [
        first_fee.id
    ]


@pytest.mark.parametrize("kind", ["dunning", "return"])
def test_fee_projection_and_automatic_dunning_share_claim_policy(
    session, business, kind
):
    from reality.services import dunning_runs, projections

    tenant = business.tenant.id
    _, fee = fee_story(session, business, kind)
    payload = projections._build_financial_rows(session, tenant)[fee.id]
    assert payload["origin"] == "fee"
    assert payload["flow"] == "receivable"
    assert payload["open"] == Decimal(5)
    assert fee.type not in dunning_runs.DUNNABLE_TYPES


@pytest.mark.parametrize("kind", ["dunning", "return"])
def test_fee_http_and_mcp_use_same_confirmed_payment_contract(session, business, kind):
    from fastapi.testclient import TestClient

    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.web.api import database_session
    from reality.web.app import app

    tenant = business.tenant.id
    _, fee = fee_story(session, business, kind)
    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{tenant}"
            context = client.get(base + f"/finance/settlements/context/{fee.id}")
            assert context.status_code == 200
            assert context.json()["reduction_allowed"] is False
            args = {
                "document_id": fee.id,
                "mode": "payment",
                "amount": "5",
                "allocation_amount": "5",
                "reference": "Fee paid",
                "effective_at": "2026-10-03T08:00:00Z",
                "expected_revision": context.json()["revision"],
            }
            response = client.post(
                base + "/finance/settlements/proposals",
                json={
                    "tool": "finance.settlement.apply",
                    "arguments": args,
                },
            )
            assert response.status_code == 200, response.text
            mcp = MCP_TOOL_REGISTRY["finance_settlement_propose"].handler(
                session, tenant, args
            )
            assert mcp["status"] == "proposed"
            assert core.open_invoice_amount(session, tenant, fee.id) == 5
            result = client.post(
                base + f"/change-proposals/{response.json()['id']}/approve", json={}
            )
            assert result.status_code == 200, result.text
            assert core.open_invoice_amount(session, tenant, fee.id) == 0
    finally:
        app.dependency_overrides.clear()


from intake_review_support import reviewed_update_party
