"""Accepted reductions are explicit, evidenced and independent of actual cash."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import LedgerEntry, SourceRecord
from reality.services import core
from reality.services.finance.accounts import (
    create_account,
    list_accounts,
    set_default_account,
    update_account,
)
from reality.services.finance.settlement import adjustment_context
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def prepare(session, business, side, amount="20", **changes):
    tenant = business.tenant.id
    role = f"{side}_reduction"
    if role not in list_accounts(session, tenant)["defaults"]:
        account = create_account(session, tenant, code=role, name=role, role=role)
        set_default_account(session, tenant, role=role, account_id=account["id"])
    party = business.customer if side == "customer" else business.supplier
    kind = "sales_invoice" if side == "customer" else "supplier_invoice"
    invoice = core.create_document(
        session, tenant, kind, core.uid("inv"), party.id, "100"
    )
    getattr(core, f"post_{'sales' if side == 'customer' else 'supplier'}_invoice")(
        session, tenant, invoice.id
    )
    payment = getattr(core, f"post_{side}_payment")(session, tenant, invoice.id, "80")
    context = adjustment_context(session, tenant, invoice.id)
    args = {
        "invoice_id": invoice.id,
        "amount": amount,
        "expected_revision": context["revision"],
        "reason_category": "early_payment_discount",
        "reason": "Agreed stated discount",
        "agreement": "Supplier terms explicitly grant EUR 20"
        if side == "supplier"
        else "",
    }
    args.update(changes)
    proposal = create_change_proposal(
        session, tenant, "finance.adjustment.accept", args, actor_type="human"
    )
    return invoice, payment, proposal


@pytest.mark.parametrize("side", ["customer", "supplier"])
def test_confirmed_adjustment_and_independent_inverse(session, business, side):
    invoice, payment, proposal = prepare(session, business, side)
    tenant = business.tenant.id
    assert core.open_invoice_amount(session, tenant, invoice.id) == 20
    result = approve_and_execute_proposal(session, tenant, proposal.id)
    receipt = json.loads(result.output)
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0
    entries = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant,
                LedgerEntry.posting_group_id == receipt["posting_group_id"],
            )
        )
    )
    assert len(entries) == 2
    assert {e.account for e in entries} == {
        f"{side}_reduction",
        "accounts_receivable" if side == "customer" else "accounts_payable",
    }
    assert all(e.amount == Decimal(20) for e in entries)
    evidence = session.get(SourceRecord, receipt["source_record_id"])
    assert json.loads(evidence.payload)["reason"] == "Agreed stated discount"
    assert (
        json.loads(approve_and_execute_proposal(session, tenant, proposal.id).output)
        == receipt
    )
    counterpart = next(e for e in entries if e.account == f"{side}_reduction")
    update_account(session, tenant, account_id=counterpart.account_id, state="blocked")
    core.reverse_ledger_posting_group(
        session, tenant, receipt["posting_group_id"], reason="Agreement corrected"
    )
    assert core.open_invoice_amount(session, tenant, invoice.id) == 20
    assert not core._ledger_reversal_for_group(
        session, tenant, payment[0].posting_group_id
    )[0]


@pytest.mark.parametrize(
    "changes", [{"amount": "21"}, {"reason": ""}, {"agreement": ""}]
)
def test_supplier_rejects_unsupported_reduction(session, business, changes):
    with pytest.raises(core.InvalidOperation):
        prepare(session, business, "supplier", **changes)


def test_stale_confirmation_has_no_partial_effect(session, business):
    invoice, _, proposal = prepare(session, business, "customer")
    core.post_customer_payment(session, business.tenant.id, invoice.id, "1")
    count = session.scalar(select(func.count()).select_from(LedgerEntry))
    with pytest.raises(core.Conflict):
        approve_and_execute_proposal(session, business.tenant.id, proposal.id)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == count
    assert core.open_invoice_amount(session, business.tenant.id, invoice.id) == 19


def test_adjustment_tenant_boundary(session, business):
    invoice, _, proposal = prepare(session, business, "customer")
    foreign = core.create_tenant(session, "Other adjustment company")
    with pytest.raises(core.NotFound):
        adjustment_context(session, foreign.id, invoice.id)
    with pytest.raises(core.NotFound):
        create_change_proposal(
            session, foreign.id, "finance.adjustment.accept", json.loads(proposal.input)
        )
    with pytest.raises(core.NotFound):
        approve_and_execute_proposal(session, foreign.id, proposal.id)


def test_adjustment_rollback_removes_evidence_and_effects(
    session, business, monkeypatch
):
    from reality.db.core import Document, SettlementAllocation

    invoice, _, proposal = prepare(session, business, "customer")
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
        approve_and_execute_proposal(session, business.tenant.id, proposal.id)
    assert [
        session.scalar(select(func.count()).select_from(model)) for model in models
    ] == before
    assert core.open_invoice_amount(session, business.tenant.id, invoice.id) == 20


def test_external_adjustment_effect_is_consumed_once(session, business):
    tenant = business.tenant.id
    source, _, _ = core.store_source_record(
        session, tenant, "payment_advice", "discount", "ADVICE-1", {"discount": "10"}
    )
    invoice, _, proposal = prepare(
        session,
        business,
        "customer",
        amount="10",
        source_record_id=source.id,
        source_effect_id="discount-1",
    )
    approve_and_execute_proposal(session, tenant, proposal.id)
    arguments = json.loads(proposal.input)
    arguments["expected_revision"] = list_accounts(session, tenant)["revision"]
    arguments["reason"] = "Changed text must not create a second effect"
    with pytest.raises(core.Conflict, match="already been accepted"):
        create_change_proposal(session, tenant, "finance.adjustment.accept", arguments)
    assert core.open_invoice_amount(session, tenant, invoice.id) == 10


def test_concurrent_adjustments_serialize_availability(postgres_database):
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
            tenant = core.create_tenant(session, "Concurrent reductions")
            customer = core.create_party(session, tenant.id, "Customer", "customer")
            invoice, _, first = prepare(
                session, SimpleNamespace(tenant=tenant, customer=customer), "customer"
            )
            second = create_change_proposal(
                session, tenant.id, "finance.adjustment.accept", json.loads(first.input)
            )
            tenant_id, invoice_id, ids = tenant.id, invoice.id, [first.id, second.id]
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
            assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 6
    finally:
        engine.dispose()


def test_additive_reduction_migration_preserves_populated_accounts(
    postgres_database, monkeypatch
):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from reality.db.core import SubledgerAccount

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0048_finance_accounts")
    engine = create_engine(postgres_database)
    try:
        with Session(engine, expire_on_commit=False) as session:
            tenant = core.create_tenant(session, "Migration claim")
            party = core.create_party(session, tenant.id, "Customer", "customer")
            invoice = core.create_document(
                session,
                tenant.id,
                "sales_invoice",
                "BEFORE",
                party.id,
                "100",
                document_date="2026-01-05",
            )
            # Populate the historical schema directly; current posting services require the new coverage tables.
            accounts = {
                a.role: a.id
                for a in session.scalars(
                    select(SubledgerAccount).where(
                        SubledgerAccount.tenant_id == tenant.id
                    )
                )
            }
            postings = [
                LedgerEntry(
                    id=core.uid("led"),
                    tenant_id=tenant.id,
                    posting_group_id="migration-before",
                    account_id=accounts[role],
                    party_id=party.id,
                    document_id=invoice.id,
                    amount=100,
                    currency="EUR",
                    debit_credit=side,
                    effective_at=core.now(),
                )
                for role, side in (
                    ("accounts_receivable", "debit"),
                    ("sales_revenue", "credit"),
                )
            ]
            session.add_all(postings)
            session.commit()
            identities = [e.account_id for e in postings]
            tenant_id = tenant.id
        command.upgrade(config, "head")
        with Session(engine) as session:
            assert {e.account_id for e in session.scalars(select(LedgerEntry))} == set(
                identities
            )
            create_account(
                session,
                tenant_id,
                code="RED",
                name="Reduction",
                role="customer_reduction",
            )
        with pytest.raises(RuntimeError, match="Reduction accounts exist"):
            command.downgrade(config, "0048_finance_accounts")
        with Session(engine) as session:
            assert (
                session.scalar(select(func.count()).select_from(SubledgerAccount)) == 6
            )
            # The refused downgrade leaves the schema at whatever the head is; pinning
            # a revision name here broke on every new migration.
            from alembic.script import ScriptDirectory

            assert (
                session.scalar(text("SELECT version_num FROM alembic_version"))
                == ScriptDirectory.from_config(config).get_current_head()
            )
    finally:
        engine.dispose()


@pytest.mark.parametrize("amount", ["not-money", "NaN", "0", "-1", "0.00001"])
def test_invalid_stated_amount_never_creates_adjustment(session, business, amount):
    with pytest.raises(core.InvalidOperation):
        prepare(session, business, "customer", amount=amount)
    assert not session.scalar(
        select(SourceRecord.id).where(
            SourceRecord.source_system == "internal_settlement_adjustment"
        )
    )


def test_existing_credit_evidence_must_be_reused(session, business):
    tenant = business.tenant.id
    source, _, _ = core.store_source_record(
        session,
        tenant,
        "supplier_document",
        "credit_note",
        "CREDIT-EXISTS",
        {"amount": "20"},
    )
    core.create_document(
        session,
        tenant,
        "credit_note",
        "CREDIT-EXISTS",
        business.customer.id,
        "20",
        source_record_id=source.id,
    )
    with pytest.raises(core.InvalidOperation, match="existing credit note"):
        prepare(
            session,
            business,
            "customer",
            source_record_id=source.id,
            source_effect_id="1",
        )


def test_new_source_version_cannot_repeat_accepted_effect(session, business):
    tenant = business.tenant.id
    source, _, _ = core.store_source_record(
        session,
        tenant,
        "payment_advice",
        "discount",
        "VERSIONED",
        {"discount": "10", "note": "first"},
    )
    invoice, _, proposal = prepare(
        session,
        business,
        "customer",
        amount="10",
        source_record_id=source.id,
        source_effect_id="discount-1",
    )
    approve_and_execute_proposal(session, tenant, proposal.id)
    changed, _, _ = core.store_source_record(
        session,
        tenant,
        "payment_advice",
        "discount",
        "VERSIONED",
        {"discount": "10", "note": "corrected explanation"},
    )
    assert changed.id != source.id
    arguments = json.loads(proposal.input) | {
        "source_record_id": changed.id,
        "expected_revision": list_accounts(session, tenant)["revision"],
    }
    with pytest.raises(core.Conflict, match="already been accepted"):
        create_change_proposal(session, tenant, "finance.adjustment.accept", arguments)
    assert core.open_invoice_amount(session, tenant, invoice.id) == 10
