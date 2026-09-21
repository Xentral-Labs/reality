from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import LedgerEntry
from reality.services import core
from reality.services.finance.accounts import (
    create_account,
    initialize_accounts,
    list_accounts,
    set_default_account,
    update_account,
)


def invoice(session, business, kind="sales_invoice", amount="100"):
    party = business.customer if kind == "sales_invoice" else business.supplier
    doc = core.create_document(
        session, business.tenant.id, kind, core.uid("test"), party.id, amount
    )
    return doc


def test_required_ids_and_explicit_setup(session, business):
    business.tenant = core.create_tenant(session, "Fresh", _with_finance_defaults=False)
    business.customer = core.create_party(
        session, business.tenant.id, "Customer", "customer"
    )
    assert list_accounts(session, business.tenant.id)["accounts"] == []
    doc = invoice(session, business)
    with pytest.raises(core.InvalidOperation, match="default"):
        core.post_sales_invoice(session, business.tenant.id, doc.id)
    initialize_accounts(session, business.tenant.id)
    entries = core.post_sales_invoice(session, business.tenant.id, doc.id)
    assert all(e.account_id for e in entries)
    assert "account" not in LedgerEntry.__table__.columns
    assert len(initialize_accounts(session, business.tenant.id)["accounts"]) == 10


def test_default_change_preserves_invoice_account_and_blocked_inverse(
    session, business
):
    initialize_accounts(session, business.tenant.id)
    doc = invoice(session, business)
    entries = core.post_sales_invoice(session, business.tenant.id, doc.id)
    original = next(e for e in entries if e.account == "accounts_receivable")
    new = create_account(
        session,
        business.tenant.id,
        code="CUSTOM",
        name="Receivables 2",
        role="accounts_receivable",
    )
    set_default_account(
        session, business.tenant.id, role="accounts_receivable", account_id=new["id"]
    )
    paid = core.post_customer_payment(session, business.tenant.id, doc.id, "40")
    assert (
        next(e for e in paid if e.account == "accounts_receivable").account_id
        == original.account_id
    )
    assert core.open_invoice_amount(session, business.tenant.id, doc.id) == Decimal(60)
    update_account(session, business.tenant.id, original.account_id, state="blocked")
    with pytest.raises(core.InvalidOperation, match="blocked"):
        core.post_customer_payment(session, business.tenant.id, doc.id, "10")
    core.reverse_ledger_posting_group(
        session, business.tenant.id, entries[0].posting_group_id, reason="Correction"
    )
    inverses = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == business.tenant.id,
                LedgerEntry.document_id.is_(None),
            )
        )
    )
    assert original.account_id in {e.account_id for e in inverses}


def test_account_role_tenant_and_code_validation(session, business):
    initialize_accounts(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation):
        create_account(
            session, business.tenant.id, code="bad", name="Bad", role="guess"
        )
    other = core.create_tenant(session, "Other")
    foreign = create_account(
        session, other.id, code="AR", name="AR", role="accounts_receivable"
    )
    with pytest.raises(core.NotFound):
        set_default_account(
            session,
            business.tenant.id,
            role="accounts_receivable",
            account_id=foreign["id"],
        )


def test_credit_cannot_be_consumed_again_after_refund(session, business):
    initialize_accounts(session, business.tenant.id)
    note = core.create_document(
        session, business.tenant.id, "credit_note", "CN", business.customer.id, "100"
    )
    core.post_sales_credit_note(session, business.tenant.id, note.id)
    core.post_customer_refund(session, business.tenant.id, note.id, "80")
    doc = invoice(session, business)
    core.post_sales_invoice(session, business.tenant.id, doc.id)
    with pytest.raises(core.InvalidOperation, match="unallocated"):
        core.allocate_credit_note(session, business.tenant.id, note.id, doc.id, "30")


def test_account_proposal_is_atomic_stale_and_idempotent(session, business):
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    current = list_accounts(session, business.tenant.id)
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "finance.account.create",
        {
            "code": "NEW",
            "name": "New cash",
            "role": "cash",
            "expected_revision": current["revision"],
        },
    )
    assert not any(
        a["code"] == "NEW"
        for a in list_accounts(session, business.tenant.id)["accounts"]
    )
    result = approve_and_execute_proposal(session, business.tenant.id, proposal.id)
    assert result.status == "executed"
    assert (
        approve_and_execute_proposal(session, business.tenant.id, proposal.id).output
        == result.output
    )
    stale = create_change_proposal(
        session,
        business.tenant.id,
        "finance.account.create",
        {
            "code": "STALE",
            "name": "Stale cash",
            "role": "cash",
            "expected_revision": current["revision"],
        },
    )
    with pytest.raises(core.Conflict, match="stale"):
        approve_and_execute_proposal(session, business.tenant.id, stale.id)
    assert not any(
        a["code"] == "STALE"
        for a in list_accounts(session, business.tenant.id)["accounts"]
    )


def test_clean_schema_migration(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect

    from reality.db.core import ROOT

    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        columns = {c["name"] for c in inspect(engine).get_columns("ledger_entry")}
        assert "account_id" in columns and "account" not in columns
    finally:
        engine.dispose()


def test_concurrent_consumers_cannot_spend_one_credit_twice(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from reality.db.core import Base

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            tenant = core.create_tenant(session, "Concurrent finance")
            tenant_id = tenant.id
            initialize_accounts(session, tenant_id)
            customer = core.create_party(session, tenant_id, "Customer", "customer")
            payment = core.record_customer_payment(
                session, tenant_id, customer.id, "100"
            )
            credit_id = next(
                e.id for e in payment if e.account == "accounts_receivable"
            )
            invoice_ids = []
            for number in ["A", "B"]:
                doc = core.create_document(
                    session, tenant_id, "sales_invoice", number, customer.id, "100"
                )
                entries = core.post_sales_invoice(session, tenant_id, doc.id)
                invoice_ids.append(
                    next(e.id for e in entries if e.account == "accounts_receivable")
                )
        barrier = Barrier(2)

        def consume(target):
            with Session(engine) as session:
                barrier.wait(timeout=10)
                try:
                    core.allocate_settlement(
                        session, tenant_id, credit_id, target, "80"
                    )
                    return "allocated"
                except core.InvalidOperation:
                    session.rollback()
                    return "refused"

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(consume, invoice_ids))
        assert sorted(outcomes) == ["allocated", "refused"]
    finally:
        engine.dispose()


def test_account_confirmation_requires_owner(session, business):
    from reality.services.memberships import Principal
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    current = list_accounts(session, business.tenant.id)
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "finance.account.create",
        {
            "code": "DENIED",
            "name": "Denied",
            "role": "cash",
            "expected_revision": current["revision"],
        },
    )
    with pytest.raises(core.NotFound):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=Principal("foreign-user"),
        )
    assert not any(
        a["code"] == "DENIED"
        for a in list_accounts(session, business.tenant.id)["accounts"]
    )


def test_account_configuration_api_uses_proposal(session, business):
    from fastapi.testclient import TestClient

    from reality.web.api import database_session
    from reality.web.app import app

    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            response = client.get(base + "/finance/accounts")
            assert response.status_code == 200
            doc = invoice(session, business)
            posted = core.post_sales_invoice(session, business.tenant.id, doc.id)
            journal = client.get(base + "/finance/journal").json()["items"]
            assert {row["account_id"] for row in journal} == {
                entry.account_id for entry in posted
            }
            assert all(row["account_code"] and row["account_name"] for row in journal)
            revision = client.get(base + "/finance/accounts").json()["revision"]
            proposal = client.post(
                base + "/finance/accounts/proposals",
                json={
                    "tool": "finance.account.create",
                    "arguments": {
                        "code": "HTTP",
                        "name": "HTTP bank",
                        "role": "cash",
                        "expected_revision": revision,
                    },
                },
            )
            assert proposal.status_code == 200, proposal.text
            assert not any(
                a["code"] == "HTTP"
                for a in client.get(base + "/finance/accounts").json()["accounts"]
            )
            applied = client.post(
                base + "/change-proposals/" + proposal.json()["id"] + "/approve",
                json={},
            )
            assert applied.status_code == 200, applied.text
            assert any(
                a["code"] == "HTTP"
                for a in client.get(base + "/finance/accounts").json()["accounts"]
            )
    finally:
        app.dependency_overrides.clear()
