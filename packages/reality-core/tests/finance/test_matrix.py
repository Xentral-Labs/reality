"""The displayed transaction matrix agrees with actual operational postings."""

import json

import pytest
from sqlalchemy import func, select

from reality.db.core import FinanceState, LedgerEntry, SubledgerAccount
from reality.services import core
from reality.services.finance import accounts
from reality.tools.application import create_change_proposal
from tests.finance.test_references import confirm


@pytest.mark.parametrize("side", ["customer", "supplier"])
def test_matrix_matches_actual_invoice_credit_payment_refund(session, business, side):
    tenant = business.tenant.id
    customer = side == "customer"
    party = business.customer if customer else business.supplier
    invoice_kind = "sales_invoice" if customer else "supplier_invoice"
    credit_kind = "credit_note" if customer else "supplier_credit_note"
    invoice = core.create_document(
        session, tenant, invoice_kind, "INV", party.id, "119"
    )
    credit = core.create_document(session, tenant, credit_kind, "CR", party.id, "59")
    post_invoice = core.post_sales_invoice if customer else core.post_supplier_invoice
    post_credit = (
        core.post_sales_credit_note if customer else core.post_supplier_credit_note
    )
    payment = core.post_customer_payment if customer else core.post_supplier_payment
    refund = core.post_customer_refund if customer else core.post_supplier_refund
    actual = {
        invoice_kind: post_invoice(session, tenant, invoice.id),
        credit_kind: post_credit(session, tenant, credit.id),
        side + "_payment": payment(session, tenant, invoice.id, "20"),
        side + "_refund": refund(session, tenant, credit.id, "10"),
    }
    rows = {
        row["transaction"]: row
        for row in accounts.transaction_matrix(session, tenant)["operations"]
    }
    assert len(rows) == 14
    for kind, entries in actual.items():
        assert {(e.debit_credit, e.account, e.account_id) for e in entries} == {
            (leg["side"], leg["role"], leg["account"]["id"])
            for leg in rows[kind]["legs"]
        }
        assert all(leg["status"] == "configured" for leg in rows[kind]["legs"])


def test_matrix_missing_blocked_defaults_and_tenant_scope_are_read_only(
    session, business
):
    tenant = core.create_tenant(
        session, "Unconfigured", _with_finance_defaults=False
    ).id
    before = session.scalar(select(func.count()).select_from(FinanceState))
    result = accounts.transaction_matrix(session, tenant)
    assert all(
        leg["status"] == "missing" and leg["account"] is None
        for row in result["operations"]
        for leg in row["legs"]
    )
    assert session.scalar(select(func.count()).select_from(FinanceState)) == before
    assert (
        session.scalar(
            select(func.count())
            .select_from(SubledgerAccount)
            .where(SubledgerAccount.tenant_id == tenant)
        )
        == 0
    )
    current = accounts.list_accounts(session, business.tenant.id)
    cash = current["defaults"]["cash"]
    accounts.update_account(session, business.tenant.id, cash, state="blocked")
    rows = accounts.transaction_matrix(session, business.tenant.id)["operations"]
    assert all(
        leg["status"] == "blocked"
        for row in rows
        for leg in row["legs"]
        if leg["role"] == "cash"
    )
    assert all(
        leg["account"] is None
        for row in accounts.transaction_matrix(session, tenant)["operations"]
        for leg in row["legs"]
    )
    with pytest.raises(core.NotFound):
        accounts.transaction_matrix(session, "missing")


def test_default_changes_do_not_rewrite_original_settlement_accounts(session, business):
    tenant = business.tenant.id
    doc = core.create_document(
        session, tenant, "sales_invoice", "ORIGINAL", business.customer.id, "100"
    )
    entries = core.post_sales_invoice(session, tenant, doc.id)
    original = next(e for e in entries if e.account == "accounts_receivable").account_id
    replacement = accounts.create_account(
        session, tenant, code="NEW", name="New receivables", role="accounts_receivable"
    )
    accounts.set_default_account(
        session, tenant, role="accounts_receivable", account_id=replacement["id"]
    )
    row = next(
        r
        for r in accounts.transaction_matrix(session, tenant)["operations"]
        if r["transaction"] == "customer_payment"
    )
    assert (
        next(leg for leg in row["legs"] if leg["role"] == "accounts_receivable")[
            "account"
        ]["id"]
        == replacement["id"]
    )
    assert row["control_policy"] == "original_when_linked"
    payment = core.post_customer_payment(session, tenant, doc.id, "10")
    assert (
        next(e for e in payment if e.account == "accounts_receivable").account_id
        == original
    )


def test_posted_customer_credit_supports_financial_attribution(session, business):
    from reality.services.finance.components import component_context, component_history

    tenant = business.tenant.id
    doc = core.create_document(
        session, tenant, "credit_note", "ACTUAL-CREDIT", business.customer.id, "119"
    )
    core.post_sales_credit_note(session, tenant, doc.id)
    before = session.scalar(select(func.count()).select_from(LedgerEntry))
    context = component_context(session, tenant, doc.id)
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.component.assign",
        {
            "document_id": doc.id,
            "basis": "gross",
            "expected_revision": context["revision"],
            "expected_evidence_hash": context["items"][0]["evidence_hash"],
            "reason": "Canonical customer credit",
            "parts": [],
        },
    )
    receipt = confirm(session, tenant, proposal)
    assert (
        component_history(session, tenant, receipt["component_id"])["items"][0][
            "unassigned"
        ]
        == "119"
    )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == before


def test_matrix_http_cli_mcp_share_read_only_results(scheduled_database, monkeypatch):
    from fastapi.testclient import TestClient
    from typer.testing import CliRunner

    from reality.cli import app as cli_module
    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.web.api import database_session
    from reality.web.app import app

    _, factory, tenant, _ = scheduled_database
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    with factory() as db:
        expected = accounts.transaction_matrix(db, tenant)
        app.dependency_overrides[database_session] = lambda: db
        try:
            with TestClient(app) as client:
                response = client.get(f"/api/tenants/{tenant}/finance/matrix")
                assert response.status_code == 200, response.text
                assert response.json() == expected
                assert (
                    client.get("/api/tenants/missing/finance/matrix").status_code == 404
                )
            assert (
                MCP_TOOL_REGISTRY["finance_matrix"].handler(db, tenant, {}) == expected
            )
        finally:
            app.dependency_overrides.clear()
    result = CliRunner().invoke(
        cli_module.app, ["finance-matrix", "--tenant-id", tenant]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == expected


def test_matrix_opening_directions_match_actual_import(session, business):
    from tests.finance.test_opening import prepare

    tenant = business.tenant.id
    proposal = prepare(session, business)
    receipt = confirm(session, tenant, proposal)
    from reality.db.core import Document

    operations = {
        r["transaction"]: r
        for r in accounts.transaction_matrix(session, tenant)["operations"]
    }
    for document in session.scalars(
        select(Document).where(
            Document.tenant_id == tenant, Document.type.like("opening_%")
        )
    ):
        entries = session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant, LedgerEntry.document_id == document.id
            )
        ).all()
        assert {(e.account, e.debit_credit) for e in entries} == {
            (leg["role"], leg["side"]) for leg in operations[document.type]["legs"]
        }
    assert receipt


@pytest.mark.parametrize("side", ["customer", "supplier"])
def test_matrix_adjustments_match_actual_accepted_reductions(session, business, side):
    from tests.finance.test_adjustments import prepare

    tenant = business.tenant.id
    _, _, proposal = prepare(session, business, side)
    receipt = confirm(session, tenant, proposal)
    row = next(
        r
        for r in accounts.transaction_matrix(session, tenant)["operations"]
        if r["transaction"] == side + "_settlement_adjustment"
    )
    entries = session.scalars(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.posting_group_id == receipt["posting_group_id"],
        )
    ).all()
    assert {(e.account, e.debit_credit) for e in entries} == {
        (leg["role"], leg["side"]) for leg in row["legs"]
    }
    assert row["control_policy"] == "original_required"
