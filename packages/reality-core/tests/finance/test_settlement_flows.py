"""Guided settlement records stated cash and consumes credit exactly once."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import Document, LedgerEntry, SettlementAllocation, SourceRecord
from reality.services import core
from reality.services.finance.accounts import initialize_accounts, list_accounts
from reality.services.finance.settlement_flows import settlement_context
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def invoice_for(session, business, side, amount="100"):
    tenant = business.tenant.id
    party = business.customer if side == "customer" else business.supplier
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice" if side == "customer" else "supplier_invoice",
        core.uid("inv"),
        party.id,
        amount,
    )
    getattr(
        core, "post_sales_invoice" if side == "customer" else "post_supplier_invoice"
    )(session, tenant, invoice.id)
    return invoice


def propose(session, tenant, document, mode="payment", **values):
    args = {
        "document_id": document,
        "mode": mode,
        "expected_revision": list_accounts(session, tenant)["revision"],
        **values,
    }
    if mode != "allocate_credit":
        args.setdefault("reference", "Bank statement line 1")
        args.setdefault("effective_at", "2026-09-10T08:00:00Z")
    return create_change_proposal(
        session, tenant, "finance.settlement.apply", args, actor_type="human"
    )


def execute(session, tenant, proposal):
    return json.loads(approve_and_execute_proposal(session, tenant, proposal.id).output)


@pytest.mark.parametrize("side", ["customer", "supplier"])
@pytest.mark.parametrize("accept", [False, True])
def test_underpayment_optional_reduction_and_independent_inverse(
    session, business, side, accept
):
    tenant = business.tenant.id
    if accept:
        initialize_accounts(session, tenant)
    invoice = invoice_for(session, business, side)
    extra = (
        {
            "reduction": {
                "amount": "2",
                "reason_category": "early_payment_discount",
                "reason": "Stated discount",
                "agreement": "Agreed by supplier",
            }
        }
        if accept
        else {}
    )
    proposal = propose(
        session, tenant, invoice.id, amount="98", allocation_amount="98", **extra
    )
    review = json.loads(proposal.output)["settlement"]
    assert Decimal(review["remaining_claim"]) == (0 if accept else 2)
    assert core.open_invoice_amount(session, tenant, invoice.id) == 100
    receipt = execute(session, tenant, proposal)
    assert core.open_invoice_amount(session, tenant, invoice.id) == (0 if accept else 2)
    assert execute(session, tenant, proposal) == receipt
    assert Decimal(receipt["cash_amount"]) == 98
    if accept:
        core.reverse_ledger_posting_group(
            session,
            tenant,
            receipt["reduction"]["posting_group_id"],
            reason="Discount revoked",
        )
        assert core.open_invoice_amount(session, tenant, invoice.id) == 2
        assert not core._ledger_reversal_for_group(
            session, tenant, receipt["payment"]["posting_group_id"]
        )[0]


@pytest.mark.parametrize("side", ["customer", "supplier"])
def test_excess_credit_reuse_refund_and_refund_inverse(session, business, side):
    tenant = business.tenant.id
    invoice = invoice_for(session, business, side)
    paid = execute(
        session,
        tenant,
        propose(session, tenant, invoice.id, amount="102", allocation_amount="100"),
    )
    origin = paid["payment"]["document_id"]
    assert Decimal(settlement_context(session, tenant, origin)["available"]) == 2
    other = invoice_for(session, business, side, "10")
    cash_count = session.scalar(
        select(func.count())
        .select_from(LedgerEntry)
        .where(LedgerEntry.account == "cash")
    )
    allocated = execute(
        session,
        tenant,
        propose(
            session, tenant, origin, "allocate_credit", invoice_id=other.id, amount="1"
        ),
    )
    assert Decimal(allocated["cash_amount"]) == 0
    assert core.open_invoice_amount(session, tenant, other.id) == 9
    assert (
        session.scalar(
            select(func.count())
            .select_from(LedgerEntry)
            .where(LedgerEntry.account == "cash")
        )
        == cash_count
    )
    refunded = execute(
        session, tenant, propose(session, tenant, origin, "refund_credit", amount="1")
    )
    assert Decimal(settlement_context(session, tenant, origin)["available"]) == 0
    core.reverse_ledger_posting_group(
        session,
        tenant,
        refunded["refund"]["posting_group_id"],
        reason="Refund reversed",
    )
    assert Decimal(settlement_context(session, tenant, origin)["available"]) == 1


def test_stale_and_failed_confirmation_leave_no_partial_cash(
    session, business, monkeypatch
):
    tenant = business.tenant.id
    invoice = invoice_for(session, business, "customer")
    proposal = propose(
        session, tenant, invoice.id, amount="102", allocation_amount="100"
    )
    core.post_customer_payment(session, tenant, invoice.id, "1")
    with pytest.raises(core.Conflict):
        execute(session, tenant, proposal)
    proposal = propose(
        session, tenant, invoice.id, amount="102", allocation_amount="99"
    )
    models = [SourceRecord, Document, LedgerEntry, SettlementAllocation]
    before = [
        session.scalar(select(func.count()).select_from(model)) for model in models
    ]
    allocate = core.allocate_settlement

    def fail(*args, **kwargs):
        allocate(*args, **kwargs)
        raise RuntimeError("Injected allocation failure")

    monkeypatch.setattr(core, "allocate_settlement", fail)
    with pytest.raises(RuntimeError):
        execute(session, tenant, proposal)
    assert [
        session.scalar(select(func.count()).select_from(model)) for model in models
    ] == before


def test_settlement_tenant_boundary(session, business):
    invoice = invoice_for(session, business, "customer")
    tenant = core.create_tenant(session, "Other")
    with pytest.raises(core.NotFound):
        settlement_context(session, tenant.id, invoice.id)
    with pytest.raises(core.NotFound):
        propose(session, tenant.id, invoice.id, amount="1", allocation_amount="1")


@pytest.mark.parametrize(
    "amount,allocation",
    [
        ("NaN", "1"),
        ("0", "0"),
        ("1.00001", "1"),
        ("1", "2"),
        ("102", "101"),
        ("1", "-1"),
    ],
)
def test_invalid_payment_intent_rejected_before_proposal(
    session, business, amount, allocation
):
    invoice = invoice_for(session, business, "customer")
    with pytest.raises(core.InvalidOperation):
        propose(
            session,
            business.tenant.id,
            invoice.id,
            amount=amount,
            allocation_amount=allocation,
        )


def test_payment_source_effect_cannot_repeat_across_versions(session, business):
    tenant = business.tenant.id
    invoice = invoice_for(session, business, "customer")
    source, _, _ = core.store_source_record(
        session, tenant, "bank", "line", "1", {"amount": "10"}
    )
    values = {
        "amount": "10",
        "allocation_amount": "10",
        "source_record_id": source.id,
        "source_effect_id": "cash",
    }
    execute(session, tenant, propose(session, tenant, invoice.id, **values))
    changed, _, _ = core.store_source_record(
        session, tenant, "bank", "line", "1", {"amount": "10", "note": "updated"}
    )
    with pytest.raises(core.Conflict):
        propose(
            session, tenant, invoice.id, **(values | {"source_record_id": changed.id})
        )


@pytest.mark.parametrize("side", ["customer", "supplier"])
def test_credit_note_can_be_reused_and_refunded(session, business, side):
    tenant = business.tenant.id
    party = business.customer if side == "customer" else business.supplier
    note = core.create_document(
        session,
        tenant,
        "credit_note" if side == "customer" else "supplier_credit_note",
        "CREDIT",
        party.id,
        "10",
    )
    getattr(
        core,
        "post_sales_credit_note" if side == "customer" else "post_supplier_credit_note",
    )(session, tenant, note.id)
    invoice = invoice_for(session, business, side)
    execute(
        session,
        tenant,
        propose(
            session,
            tenant,
            note.id,
            "allocate_credit",
            invoice_id=invoice.id,
            amount="4",
        ),
    )
    execute(
        session, tenant, propose(session, tenant, note.id, "refund_credit", amount="6")
    )
    assert Decimal(settlement_context(session, tenant, note.id)["available"]) == 0
    with pytest.raises(core.InvalidOperation, match="available credit"):
        propose(session, tenant, note.id, "refund_credit", amount="1")


def test_rejects_foreign_party_blocked_and_reversed_credit(session, business):
    from reality.services.finance.accounts import update_account

    tenant = business.tenant.id
    invoice = invoice_for(session, business, "customer")
    result = execute(
        session,
        tenant,
        propose(session, tenant, invoice.id, amount="102", allocation_amount="100"),
    )
    origin = result["payment"]["document_id"]
    party = core.create_party(session, tenant, "Another customer", "customer")
    other = core.create_document(
        session, tenant, "sales_invoice", "OTHER", party.id, "10"
    )
    core.post_sales_invoice(session, tenant, other.id)
    with pytest.raises(core.InvalidOperation, match="same party"):
        propose(
            session, tenant, origin, "allocate_credit", invoice_id=other.id, amount="1"
        )
    foreign = core.create_tenant(session, "Foreign credit owner")
    with pytest.raises(core.NotFound):
        settlement_context(session, foreign.id, origin)
    account = settlement_context(session, tenant, origin)["control_account_id"]
    update_account(session, tenant, account_id=account, state="blocked")
    with pytest.raises(core.InvalidOperation):
        propose(session, tenant, origin, "refund_credit", amount="1")
    core.reverse_ledger_posting_group(
        session,
        tenant,
        result["payment"]["posting_group_id"],
        reason="Payment reversed",
    )
    with pytest.raises(core.InvalidOperation, match="reversed"):
        settlement_context(session, tenant, origin)


def test_supplier_reduction_requires_agreement_and_combined_limit(session, business):
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    invoice = invoice_for(session, business, "supplier")
    reduction = {
        "amount": "2",
        "reason_category": "agreed_deduction",
        "reason": "Agreed reduction",
    }
    with pytest.raises(core.InvalidOperation, match="agreement"):
        propose(
            session,
            tenant,
            invoice.id,
            amount="98",
            allocation_amount="98",
            reduction=reduction,
        )
    with pytest.raises(core.InvalidOperation, match="exceed"):
        propose(
            session,
            tenant,
            invoice.id,
            amount="99",
            allocation_amount="99",
            reduction=reduction | {"agreement": "Supplier approval"},
        )


def test_http_and_mcp_proposals_share_service_without_early_effects(session, business):
    from fastapi.testclient import TestClient

    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.web.api import database_session
    from reality.web.app import app

    tenant = business.tenant.id
    invoice = invoice_for(session, business, "customer")
    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{tenant}"
            context = client.get(base + f"/finance/settlements/context/{invoice.id}")
            assert context.status_code == 200
            args = {
                "mode": "payment",
                "document_id": invoice.id,
                "amount": "102",
                "allocation_amount": "100",
                "reference": "HTTP payment",
                "effective_at": "2026-09-10T08:00:00Z",
                "expected_revision": context.json()["revision"],
            }
            response = client.post(
                base + "/finance/settlements/proposals",
                json={"tool": "finance.settlement.apply", "arguments": args},
            )
            assert response.status_code == 200, response.text
            mcp = MCP_TOOL_REGISTRY["finance_settlement_propose"].handler(
                session, tenant, args
            )
            assert mcp["status"] == "proposed"
            assert core.open_invoice_amount(session, tenant, invoice.id) == 100
            result = client.post(
                base + f"/change-proposals/{response.json()['id']}/approve", json={}
            )
            assert result.status_code == 200, result.text
            assert Decimal(result.json()["output"]["remaining_credit"]) == 2
            schema = MCP_TOOL_REGISTRY["finance_settlement_propose"].input_schema
            assert schema["type"] == "object"
            assert set(schema["properties"]["mode"]["enum"]) == {
                "payment",
                "allocate_credit",
                "refund_credit",
            }
            assert "finance_settlement_context" in MCP_TOOL_REGISTRY
            assert MCP_TOOL_REGISTRY["finance_settlement_propose"].access == "propose"
    finally:
        app.dependency_overrides.clear()


def test_confirmation_requires_owner_when_auth_enabled(session, business, monkeypatch):
    tenant = business.tenant.id
    invoice = invoice_for(session, business, "customer")
    proposal = propose(session, tenant, invoice.id, amount="10", allocation_amount="10")
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    with pytest.raises(core.InvalidOperation, match="owner"):
        execute(session, tenant, proposal)
    assert core.open_invoice_amount(session, tenant, invoice.id) == 100


def test_concurrent_payment_confirmations_only_consume_once(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from reality.db.core import Base

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as session:
            tenant = core.create_tenant(session, "Concurrent payments")
            customer = core.create_party(session, tenant.id, "Customer", "customer")
            invoice = invoice_for(
                session, SimpleNamespace(tenant=tenant, customer=customer), "customer"
            )
            first = propose(
                session, tenant.id, invoice.id, amount="102", allocation_amount="100"
            )
            second = propose(
                session, tenant.id, invoice.id, amount="102", allocation_amount="100"
            )
            ids, tenant_id, invoice_id = [first.id, second.id], tenant.id, invoice.id
        barrier = Barrier(2)

        def confirm(identity):
            with Session(engine) as session:
                barrier.wait(timeout=10)
                try:
                    return approve_and_execute_proposal(
                        session, tenant_id, identity
                    ).status
                except core.Conflict:
                    return "stale"

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(confirm, ids)) == ["executed", "stale"]
        with Session(engine) as session:
            assert core.open_invoice_amount(session, tenant_id, invoice_id) == 0
            assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 4
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "changes",
    [
        {"amount": "100000000000000"},
        {"effective_at": "2026-09-10T08:00:00"},
        {"effective_at": "not-a-date"},
    ],
)
def test_payment_rejects_unrepresentable_amount_or_ambiguous_time(
    session, business, changes
):
    invoice = invoice_for(session, business, "customer")
    values = {"amount": "10", "allocation_amount": "10", **changes}
    with pytest.raises(core.InvalidOperation):
        propose(session, business.tenant.id, invoice.id, **values)


def test_payment_credit_context_carries_candidate_reasons(session, business):
    """Feature 168 FR-014/FR-015: candidates reach the guided flow and MCP with reasons."""
    from reality.services.payment_intake import (
        NormalisedPayment,
        Reference,
        interpret_customer_payment,
    )
    from reality.tools.application import run_read_tool

    tenant = business.tenant.id
    matching = invoice_for(session, business, "customer", amount="100")
    other = invoice_for(session, business, "customer", amount="250")
    source, _job = core.enqueue_source(
        session,
        tenant,
        "demo_data",
        "payment",
        "credit-context",
        {"synthetic": True, "remittance_text": f"see {other.number}"},
        _commit=False,
    )
    _, payment, _, allocation, _ = interpret_customer_payment(
        session,
        tenant,
        source,
        NormalisedPayment(
            party_id=business.customer.id,
            amount=Decimal(100),
            currency="EUR",
            effective_at="2026-09-10T08:00:00+00:00",
            external_payment_id="txn-credit-context",
            references=(Reference(type="customer_number", value="C-1"),),
            remittance_text=f"see {other.number}",
        ),
    )
    assert allocation is None
    context = settlement_context(session, tenant, payment.id)
    by_id = {choice["id"]: choice for choice in context["invoices"]}
    assert by_id[matching.id]["reasons"] == ["amount equals the open amount"]
    assert by_id[other.id]["reasons"] == [
        "invoice number appears in the remittance text"
    ]
    assert [choice["id"] for choice in context["candidates"]] == [
        choice["id"] for choice in context["invoices"] if choice["reasons"]
    ]
    via_tool = run_read_tool(
        session, tenant, "finance.settlement.context", {"document_id": payment.id}
    )
    assert via_tool["candidates"] == context["candidates"]
    proposal = propose(
        session,
        tenant,
        payment.id,
        mode="allocate_credit",
        amount="100",
        invoice_id=matching.id,
    )
    assert execute(session, tenant, proposal)["allocation_id"]
    assert settlement_context(session, tenant, payment.id)["candidates"] == []
