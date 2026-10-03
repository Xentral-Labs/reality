"""Guided settlement records stated cash and consumes credit exactly once."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import (
    Document,
    LedgerEntry,
    SettlementAllocation,
    SourceRecord,
    SubledgerAccount,
)
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
    """
    BUSINESS TEST:
    Underpayment optional reduction and independent inverse.
    GIVEN:
    Customer or supplier invoice 100; accept parameter controls an agreed reduction of 2.
    WHEN:
    Propose and confirm payment 98, replay confirmation and optionally reverse reduction.
    THEN:
    Proposal changes no balance; claim remains 2 without reduction or zero with it; replay is identical and reduction reversal leaves payment active.
    """
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
    """
    BUSINESS TEST:
    Excess credit reuse refund and refund inverse.
    GIVEN:
    Customer or supplier invoice 100 is paid 102.
    WHEN:
    Allocate one unit of excess to another invoice, refund one and reverse refund.
    THEN:
    Credit starts at 2, allocation creates no cash entry, other claim becomes 9, refund consumes remaining credit and reversal restores 1.
    """
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
    """
    BUSINESS TEST:
    Stale and failed confirmation leave no partial cash.
    GIVEN:
    A customer payment proposal exists and the invoice changes before confirmation.
    WHEN:
    Confirm stale proposal, then inject failure after settlement allocation in a fresh proposal.
    THEN:
    Stale confirmation conflicts; injected failure leaves source, document, ledger and allocation counts unchanged.
    """
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
    """
    BUSINESS TEST:
    Settlement tenant boundary.
    GIVEN:
    An invoice belongs to the business tenant.
    WHEN:
    Read settlement context and propose payment using another tenant.
    THEN:
    Both requests report not found.
    """
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
    """
    BUSINESS TEST:
    Invalid payment intent rejected before proposal.
    GIVEN:
    Parameterized amount/allocation pairs include nonfinite, zero, excessive precision, negative or excessive allocations.
    WHEN:
    Prepare a customer invoice payment proposal.
    THEN:
    Each invalid pair raises InvalidOperation.
    """
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
    """
    BUSINESS TEST:
    Payment source effect cannot repeat across versions.
    GIVEN:
    A bank source effect has already produced a confirmed payment.
    WHEN:
    Create a newer version of the same bank line and propose the same cash effect.
    THEN:
    The repeated effect conflicts despite the newer source version.
    """
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
    """
    BUSINESS TEST:
    Credit note can be reused and refunded.
    GIVEN:
    Customer or supplier credit note 10 and an invoice exist.
    WHEN:
    Allocate 4 of credit, refund 6 and request another refund of 1.
    THEN:
    Available credit becomes zero and the additional refund is refused.
    """
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
    """
    BUSINESS TEST:
    Rejects foreign party blocked and reversed credit.
    GIVEN:
    A customer payment leaves excess credit 2.
    WHEN:
    Try another customer's invoice, another tenant, a blocked account refund and reversed payment context.
    THEN:
    Each request is refused with the asserted party, tenant, account or reversal restriction.
    """
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
    """
    BUSINESS TEST:
    Supplier reduction requires agreement and combined limit.
    GIVEN:
    Supplier invoice 100 and proposed reduction 2 exist.
    WHEN:
    Prepare payment 98 without agreement, then payment 99 with agreement and reduction 2.
    THEN:
    Missing agreement and combined amount exceeding the invoice are refused.
    """
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


def test_payment_diagnostics_name_missing_cash_account_role(session, business):
    """
    BUSINESS TEST:
    Payment diagnostics name missing cash account role.
    GIVEN:
    A customer invoice exists and cash account default is removed.
    WHEN:
    Prepare payment 100.
    THEN:
    Refusal explicitly names the missing cash account default.
    """
    tenant = business.tenant.id
    invoice = invoice_for(session, business, "customer")
    session.query(SubledgerAccount).filter_by(tenant_id=tenant, role="cash").update(
        {"default_destination_id": None}
    )
    session.flush()

    with pytest.raises(
        core.InvalidOperation,
        match="Missing account default for cash. Configure finance accounts first",
    ):
        propose(
            session,
            tenant,
            invoice.id,
            amount="100",
            allocation_amount="100",
        )


def test_payment_without_reduction_does_not_require_reduction_account(
    session, business
):
    """
    BUSINESS TEST:
    Payment without reduction does not require reduction account.
    GIVEN:
    A customer invoice exists but reduction account default is absent.
    WHEN:
    Prepare and confirm a full payment without reduction.
    THEN:
    Review has no reduction, uses cash and confirmation leaves no claim.
    """
    tenant = business.tenant.id
    invoice = invoice_for(session, business, "customer")
    session.query(SubledgerAccount).filter_by(
        tenant_id=tenant, role="customer_reduction"
    ).update({"default_destination_id": None})
    session.flush()

    proposal = propose(
        session,
        tenant,
        invoice.id,
        amount="100",
        allocation_amount="100",
    )
    review = json.loads(proposal.output)["settlement"]
    assert review["reduction"] is None
    assert review["cash_account_code"] == "cash"
    assert Decimal(execute(session, tenant, proposal)["remaining_claim"]) == 0


def test_http_and_mcp_proposals_share_service_without_early_effects(session, business):
    """
    BUSINESS TEST:
    Http and mcp proposals share service without early effects.
    GIVEN:
    A customer invoice 100 is exposed through HTTP and MCP.
    WHEN:
    Prepare payment 102 allocating 100 through both channels, then approve HTTP proposal.
    THEN:
    Preparation leaves claim 100; approval returns excess 2; MCP declares proposal access and supported settlement modes.
    """
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
    """
    BUSINESS TEST:
    Confirmation requires owner when auth enabled.
    GIVEN:
    A customer payment proposal exists and authentication is enabled.
    WHEN:
    Confirm without an owner principal.
    THEN:
    Owner refusal occurs and invoice remains open for 100.
    """
    tenant = business.tenant.id
    invoice = invoice_for(session, business, "customer")
    proposal = propose(session, tenant, invoice.id, amount="10", allocation_amount="10")
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    with pytest.raises(core.InvalidOperation, match="owner"):
        execute(session, tenant, proposal)
    assert core.open_invoice_amount(session, tenant, invoice.id) == 100


def test_concurrent_payment_confirmations_only_consume_once(postgres_database):
    """
    BUSINESS TEST:
    Concurrent payment confirmations only consume once.
    GIVEN:
    Two separate proposals each offer payment 102 against the same invoice 100.
    WHEN:
    Confirm both concurrently in independent database sessions.
    THEN:
    One executes and one is stale; invoice is settled with four ledger entries.
    """
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
    """
    BUSINESS TEST:
    Payment rejects unrepresentable amount or ambiguous time.
    GIVEN:
    Parameterized changes supply an oversized amount, timezone-free timestamp or invalid date.
    WHEN:
    Prepare payment against a customer invoice.
    THEN:
    Each unrepresentable or ambiguous input is refused.
    """
    invoice = invoice_for(session, business, "customer")
    values = {"amount": "10", "allocation_amount": "10", **changes}
    with pytest.raises(core.InvalidOperation):
        propose(session, business.tenant.id, invoice.id, **values)


def test_payment_credit_context_carries_candidate_reasons(session, business):
    """
    Feature 168 FR-014/FR-015: candidates reach the guided flow and MCP with reasons.

    BUSINESS TEST:
    Payment credit context carries candidate reasons.
    GIVEN:
    Unallocated customer payment 100 references a second invoice 250 in remittance text.
    WHEN:
    Read service/tool candidates, allocate to the matching 100 invoice and read again.
    THEN:
    Candidates explain amount or reference matches, tool agrees with service, and consumed credit has no remaining candidates.
    """
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
