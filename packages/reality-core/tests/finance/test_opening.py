"""Imported residual positions preserve coverage and reuse normal settlement."""

import json
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import Document, LedgerEntry, SettlementAllocation, SourceRecord
from reality.services import core
from reality.services.finance.accounts import initialize_accounts, list_accounts
from reality.services.finance.credits import available_credit_items
from reality.services.finance.opening import opening_context
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def rows_for(business):
    return [
        {
            "party_id": party.id,
            "direction": direction,
            "currency": "EUR",
            "amount": amount,
            "external_item_key": direction,
            "reference": direction,
        }
        for party, direction, amount in (
            (business.customer, "customer_debt", "1000"),
            (business.customer, "customer_credit", "100"),
            (business.supplier, "supplier_debt", "800"),
            (business.supplier, "supplier_credit", "50"),
        )
    ]


def prepare(session, business, *, rows=None, **changes):
    tenant = business.tenant.id
    if "opening_counterpart" not in list_accounts(session, tenant)["defaults"]:
        initialize_accounts(session, tenant)
    arguments = {
        "expected_revision": list_accounts(session, tenant)["revision"],
        "source_namespace": "previous_erp",
        "snapshot_key": "2026-cutover",
        "cutover_date": "2026-01-01",
        "coverage_kind": "individual",
        "reason": "Carry stated outstanding positions",
        "items": rows if rows is not None else rows_for(business),
        **changes,
    }
    return create_change_proposal(
        session, tenant, "finance.opening.import", arguments, actor_type="human"
    )


def confirm(session, tenant, proposal):
    return json.loads(approve_and_execute_proposal(session, tenant, proposal.id).output)


def settle(session, tenant, document, **values):
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.settlement.apply",
        {
            "document_id": document,
            "expected_revision": list_accounts(session, tenant)["revision"],
            **values,
        },
    )
    return confirm(session, tenant, proposal)


def test_four_directions_are_residual_positions_without_cash_or_turnover(
    session, business
):
    tenant = business.tenant.id
    proposal = prepare(session, business)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
    receipt = confirm(session, tenant, proposal)
    assert confirm(session, tenant, proposal) == receipt
    entries = list(session.scalars(select(LedgerEntry)))
    assert len(entries) == 8
    assert {e.account for e in entries} == {
        "opening_counterpart",
        "accounts_receivable",
        "accounts_payable",
    }
    positions = {r["direction"]: r for r in receipt["items"]}
    for direction, amount in (
        ("customer_debt", 1000),
        ("customer_credit", 100),
        ("supplier_debt", 800),
        ("supplier_credit", 50),
    ):
        assert (
            core.open_invoice_amount(
                session, tenant, positions[direction]["document_id"]
            )
            == amount
        )
    customer = positions["customer_debt"]["document_id"]
    settle(
        session,
        tenant,
        customer,
        mode="payment",
        amount="400",
        allocation_amount="400",
        reference="Actual payment",
        effective_at="2026-02-01T12:00:00Z",
    )
    settle(
        session,
        tenant,
        positions["customer_credit"]["document_id"],
        mode="allocate_credit",
        invoice_id=customer,
        amount="100",
    )
    assert core.open_invoice_amount(session, tenant, customer) == 500
    supplier = positions["supplier_debt"]["document_id"]
    settle(
        session,
        tenant,
        positions["supplier_credit"]["document_id"],
        mode="allocate_credit",
        invoice_id=supplier,
        amount="50",
    )
    assert core.open_invoice_amount(session, tenant, supplier) == 750


@pytest.mark.parametrize("side", ["customer", "supplier"])
def test_opening_credit_refund_and_reversal_preserve_original_credit(
    session, business, side
):
    tenant = business.tenant.id
    row = next(r for r in rows_for(business) if r["direction"] == f"{side}_credit")
    receipt = confirm(session, tenant, prepare(session, business, rows=[row]))
    origin = receipt["items"][0]["document_id"]
    refund = settle(
        session,
        tenant,
        origin,
        mode="refund_credit",
        amount="25",
        reference="Actual refund",
        effective_at="2026-02-01T12:00:00Z",
    )
    values = available_credit_items(session, tenant, side=side)
    assert values["items"][0]["origin"] == "opening"
    assert Decimal(values["items"][0]["open"]) == Decimal(row["amount"]) - 25
    core.reverse_ledger_posting_group(
        session, tenant, refund["refund"]["posting_group_id"], reason="Refund reversed"
    )
    assert Decimal(
        available_credit_items(session, tenant, side=side)["items"][0]["open"]
    ) == Decimal(row["amount"])


def test_original_total_and_unknown_due_date_never_create_new_authority(
    session, business
):
    row = rows_for(business)[0] | {
        "amount": "600",
        "original_total": "1000",
        "original_document_date": "2025-12-01",
    }
    receipt = confirm(
        session, business.tenant.id, prepare(session, business, rows=[row])
    )
    item = receipt["items"][0]
    document = record_by_id(session, Document, item["document_id"])
    assert document.gross_amount == 600
    source = record_by_id(session, SourceRecord, document.source_record_id)
    assert json.loads(source.payload)["item"]["original_total"] == "1000"
    aging = core.aging_register(session, business.tenant.id)
    assert aging[0]["due_date"] is None
    assert aging[0]["days_overdue"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"snapshot_key": "changed"},
        {"cutover_date": "2026-02-01"},
        {"coverage_kind": "summary"},
    ],
)
def test_duplicate_or_replaced_scope_never_adds_another_balance(
    session, business, changes
):
    tenant = business.tenant.id
    confirm(session, tenant, prepare(session, business))
    before = session.scalar(select(func.count()).select_from(LedgerEntry))
    with pytest.raises(core.Conflict):
        prepare(session, business, **changes)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == before


def test_summary_detail_overlap_is_refused_even_under_new_item_key(session, business):
    tenant = business.tenant.id
    row = rows_for(business)[0]
    confirm(
        session, tenant, prepare(session, business, rows=[row], coverage_kind="summary")
    )
    with pytest.raises(core.Conflict):
        prepare(session, business, rows=[row | {"external_item_key": "detail-1"}])


def test_stale_owner_and_tenant_boundaries(session, business, monkeypatch):
    tenant = business.tenant.id
    proposal = prepare(session, business)
    foreign = core.create_tenant(session, "Foreign opening")
    with pytest.raises(core.NotFound):
        approve_and_execute_proposal(session, foreign.id, proposal.id)
    with pytest.raises(core.NotFound):
        create_change_proposal(
            session, foreign.id, "finance.opening.import", json.loads(proposal.input)
        )
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    with pytest.raises(core.InvalidOperation, match="owner"):
        approve_and_execute_proposal(session, tenant, proposal.id)
    monkeypatch.setenv("REALITY_AUTH_MODE", "disabled")
    from reality.services.finance.accounts import create_account

    create_account(session, tenant, code="OTHER", name="Other bank", role="cash")
    with pytest.raises(core.Conflict):
        approve_and_execute_proposal(session, tenant, proposal.id)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0


def test_batch_rollback_removes_every_evidence_and_entry(
    session, business, monkeypatch
):
    from reality.db.opening import OpeningItem, OpeningScope

    tenant = business.tenant.id
    proposal = prepare(session, business)
    models = [
        OpeningScope,
        OpeningItem,
        SourceRecord,
        Document,
        LedgerEntry,
        SettlementAllocation,
    ]
    before = [
        session.scalar(select(func.count()).select_from(model)) for model in models
    ]
    original = core.post_ledger
    count = 0

    def fail(*args, **kwargs):
        nonlocal count
        entries = original(*args, **kwargs)
        count += 1
        if count == 2:
            raise RuntimeError("Injected second item failure")
        return entries

    monkeypatch.setattr(core, "post_ledger", fail)
    with pytest.raises(RuntimeError):
        approve_and_execute_proposal(session, tenant, proposal.id)
    assert [
        session.scalar(select(func.count()).select_from(model)) for model in models
    ] == before


def test_historical_original_and_ambiguous_cash_are_held_for_review(session, business):
    tenant = business.tenant.id
    confirm(session, tenant, prepare(session, business))
    source, _, _ = core.store_source_record(
        session, tenant, "previous_erp", "invoice", "customer_debt", {"total": "1000"}
    )
    original = core.create_document(
        session,
        tenant,
        "sales_invoice",
        "Original reference",
        business.customer.id,
        "1000",
        document_date="2025-12-01",
        source_record_id=source.id,
    )
    with pytest.raises(core.InvalidOperation, match="opening"):
        core.post_sales_invoice(session, tenant, original.id)
    assert record_by_id(session, SourceRecord, source.id) is not None
    with pytest.raises(core.InvalidOperation, match="cutover|timestamp"):
        core.record_customer_payment(session, tenant, business.customer.id, "10")
    from datetime import UTC, datetime

    with pytest.raises(core.InvalidOperation, match="cutover"):
        core.record_customer_payment(
            session,
            tenant,
            business.customer.id,
            "10",
            effective_at=datetime(2025, 12, 1, tzinfo=UTC),
        )


def test_opening_context_exposes_configured_account_and_current_revision(
    session, business
):
    prepare(session, business)
    context = opening_context(session, business.tenant.id)
    assert context["counterpart"]["role"] == "opening_counterpart"
    assert context["revision"] == list_accounts(session, business.tenant.id)["revision"]


def test_explicit_due_date_and_filtered_http_registers(session, business):
    from fastapi.testclient import TestClient

    from reality.web.api import database_session
    from reality.web.app import app

    tenant = business.tenant.id
    rows = rows_for(business)
    rows[0]["due_date"] = "2025-12-15"
    confirm(session, tenant, prepare(session, business, rows=rows))
    aging = next(
        row
        for row in core.aging_register(session, tenant)
        if row["document"].type == "opening_customer_debt"
    )
    assert aging["due_date"].isoformat() == "2025-12-15"
    assert aging["days_overdue"] > 0
    from reality.services.projections import rebuild_projections

    rebuild_projections(session, tenant, ["open_financial_items"])
    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            for flow, expected in (("receivable", 1000), ("payable", 800)):
                response = client.get(
                    f"/api/tenants/{tenant}/finance/open-items?flow={flow}"
                )
                assert response.status_code == 200, response.text
                body = response.json()
                assert len(body["items"]) == 1
                assert body["items"][0]["origin"] == "opening"
                assert Decimal(body["totals"][0]["open"]) == expected
    finally:
        app.dependency_overrides.clear()


def test_http_mcp_previews_and_confirmed_receipt_are_shared(session, business):
    from fastapi.testclient import TestClient

    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.web.api import database_session
    from reality.web.app import app

    tenant = business.tenant.id
    prepared = prepare(session, business)
    args = json.loads(prepared.input)
    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{tenant}"
            context = client.get(base + "/finance/opening/context")
            assert context.status_code == 200
            response = client.post(
                base + "/finance/opening/proposals",
                json={"tool": "finance.opening.import", "arguments": args},
            )
            assert response.status_code == 200, response.text
            assert (
                MCP_TOOL_REGISTRY["finance_opening_propose"].handler(
                    session, tenant, args
                )["status"]
                == "proposed"
            )
            assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
            result = client.post(
                base + f"/change-proposals/{response.json()['id']}/approve", json={}
            )
            assert result.status_code == 200, result.text
            assert len(result.json()["output"]["items"]) == 4
            assert (
                MCP_TOOL_REGISTRY["finance_opening_propose"].input_schema["type"]
                == "object"
            )
    finally:
        app.dependency_overrides.clear()


def test_opening_origin_cannot_be_posted_twice_or_fabricated(session, business):
    tenant = business.tenant.id
    receipt = confirm(session, tenant, prepare(session, business))
    document_id = receipt["items"][0]["document_id"]
    postings = [
        ("accounts_receivable", "debit", "10"),
        ("opening_counterpart", "credit", "10"),
    ]
    with pytest.raises(core.InvalidOperation, match="Opening"):
        core.post_ledger(session, tenant, document_id, business.customer.id, postings)
    fabricated = core.create_document(
        session, tenant, "opening_customer_debt", "FAKE", business.customer.id, "10"
    )
    with pytest.raises(core.InvalidOperation, match="Opening"):
        core.post_ledger(session, tenant, fabricated.id, business.customer.id, postings)


def test_opening_import_and_legacy_payment_share_lock_order(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from datetime import UTC, datetime
    from threading import Barrier
    from types import SimpleNamespace

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from reality.db.core import Base

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as session:
            tenant = core.create_tenant(session, "Opening race")
            customer = core.create_party(session, tenant.id, "Customer", "customer")
            supplier = core.create_party(session, tenant.id, "Supplier", "supplier")
            business = SimpleNamespace(
                tenant=tenant, customer=customer, supplier=supplier
            )
            proposal = prepare(session, business, rows=rows_for(business)[:1])
            tenant_id, party_id, proposal_id = tenant.id, customer.id, proposal.id
        barrier = Barrier(2)

        def run(mode):
            with Session(engine) as session:
                session.execute(text("SET LOCAL lock_timeout = '8s'"))
                barrier.wait(timeout=10)
                if mode == "payment":
                    core.record_customer_payment(
                        session,
                        tenant_id,
                        party_id,
                        "10",
                        effective_at=datetime(2026, 2, 1, tzinfo=UTC),
                    )
                    return "paid"
                try:
                    approve_and_execute_proposal(session, tenant_id, proposal_id)
                    return "imported"
                except core.Conflict:
                    return "stale"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, ["opening", "payment"]))
        assert results[0] in {"imported", "stale"}
        assert results[1] == "paid"
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(LedgerEntry)) == (
                4 if results[0] == "imported" else 2
            )
    finally:
        engine.dispose()


def test_opening_debt_reduction_and_exact_reversal_preserve_allocations(
    session, business
):
    tenant = business.tenant.id
    receipt = confirm(
        session, tenant, prepare(session, business, rows=rows_for(business)[:1])
    )
    opening = receipt["items"][0]
    settle(
        session,
        tenant,
        opening["document_id"],
        mode="payment",
        amount="980",
        allocation_amount="980",
        reference="Opening paid with stated discount",
        effective_at="2026-02-01T12:00:00Z",
        reduction={
            "amount": "20",
            "reason_category": "early_payment_discount",
            "reason": "Historic agreement explicitly carried",
            "agreement": "",
        },
    )
    assert core.open_invoice_amount(session, tenant, opening["document_id"]) == 0
    core.reverse_ledger_posting_group(
        session, tenant, opening["posting_group_id"], reason="Wrong opening residual"
    )
    assert core.open_invoice_amount(session, tenant, opening["document_id"]) == 0
    available = available_credit_items(session, tenant, side="customer")
    assert Decimal(available["items"][0]["open"]) == 980
    assert session.scalar(select(func.count()).select_from(SettlementAllocation)) == 2


@pytest.mark.parametrize("side", ["customer", "supplier"])
@pytest.mark.parametrize("kind", ["payment", "refund"])
def test_opening_scope_requires_actual_cash_time_on_legacy_writers(
    session, business, side, kind
):
    tenant = business.tenant.id
    confirm(session, tenant, prepare(session, business))
    party = business.customer if side == "customer" else business.supplier
    before = session.scalar(select(func.count()).select_from(LedgerEntry))
    with pytest.raises(core.InvalidOperation, match="timestamp"):
        getattr(core, f"record_{side}_{kind}")(session, tenant, party.id, "10")
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == before


def test_historical_cash_coverage_uses_actual_entry_time_before_import(
    session, business
):
    from datetime import UTC, datetime

    tenant = business.tenant.id
    document = core.create_document(
        session,
        tenant,
        "customer_payment",
        "Legacy dated reference",
        business.customer.id,
        "10",
        document_date="2026-02-01",
    )
    core.post_ledger(
        session,
        tenant,
        document.id,
        business.customer.id,
        [("cash", "debit", "10"), ("accounts_receivable", "credit", "10")],
        effective_at=datetime(2025, 12, 1, tzinfo=UTC),
    )
    with pytest.raises(core.Conflict, match="historical"):
        prepare(session, business, rows=rows_for(business)[:1])


def test_summary_origin_remains_explicit_in_debt_and_credit_registers(
    session, business
):
    tenant = business.tenant.id
    confirm(session, tenant, prepare(session, business, coverage_kind="summary"))
    assert {r["coverage_kind"] for r in core.financial_open_items(session, tenant)} == {
        "summary"
    }
    for side in ("customer", "supplier"):
        assert (
            available_credit_items(session, tenant, side=side)["items"][0][
                "coverage_kind"
            ]
            == "summary"
        )


def test_opening_currencies_stay_separate_and_cannot_be_cross_allocated(
    session, business
):
    tenant = business.tenant.id
    rows = rows_for(business)[:2]
    rows[1] = rows[1] | {"currency": "USD"}
    proposal = prepare(session, business, rows=rows)
    preview = json.loads(proposal.output)["opening"]
    assert {
        (row["direction"], row["currency"], Decimal(row["amount"]))
        for row in preview["totals"]
    } == {
        ("customer_debt", "EUR", Decimal(1000)),
        ("customer_credit", "USD", Decimal(100)),
    }
    receipt = confirm(session, tenant, proposal)
    positions = {row["direction"]: row["document_id"] for row in receipt["items"]}
    with pytest.raises(core.InvalidOperation):
        settle(
            session,
            tenant,
            positions["customer_credit"],
            mode="allocate_credit",
            invoice_id=positions["customer_debt"],
            amount="10",
        )
    assert session.scalar(select(func.count()).select_from(SettlementAllocation)) == 0
