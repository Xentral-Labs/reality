"""Spec 356: base account references belong only to actual new-company setup."""

import pytest
from sqlalchemy import func, select

from reality.db.core import FinanceState, SubledgerAccount, Tenant
from reality.domain.finance import BASE_ACCOUNT_ROLES
from reality.services import core
from reality.services.finance import accounts


def test_fixed_account_bootstrap_cannot_modify_an_existing_company(session):
    tenant = core.create_tenant(
        session, "Already created", _with_finance_defaults=False
    )
    with pytest.raises(core.InvalidOperation) as refused:
        accounts._bootstrap_accounts(session, tenant.id)
    assert refused.value.code == "intake_approval_required"
    assert (
        session.scalar(
            select(func.count())
            .select_from(SubledgerAccount)
            .where(SubledgerAccount.tenant_id == tenant.id)
        )
        == 0
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(FinanceState)
            .where(FinanceState.tenant_id == tenant.id)
        )
        == 0
    )


@pytest.mark.parametrize(
    "attack",
    [
        "repeated",
        "changed_identity",
        "early_commit",
        "after_write_failure",
        "sibling_header",
        "sibling_terms",
    ],
)
def test_new_company_reference_callback_cannot_escape_or_partially_commit(
    session, monkeypatch, attack
):
    target = core.create_tenant(
        session, "Existing target without defaults", _with_finance_defaults=False
    )
    original = accounts._bootstrap_accounts
    baseline = {
        model: session.scalar(select(func.count()).select_from(model))
        for model in (Tenant, SubledgerAccount, FinanceState)
    }

    def callback(db, tenant):
        if attack == "changed_identity":
            tenant = target.id
        original(db, tenant)
        if attack == "repeated":
            original(db, tenant)
        if attack == "early_commit":
            db.commit()
        if attack == "after_write_failure":
            raise RuntimeError("Failure after fixed account references")
        if attack == "sibling_header":
            core.create_document(
                db, tenant, "sales_order", "UNREVIEWED", None, "1", _commit=False
            )
        if attack == "sibling_terms":
            core.create_payment_term(
                db, tenant, "UNREVIEWED", "Unreviewed terms", 30, _commit=False
            )

    monkeypatch.setattr(accounts, "_bootstrap_accounts", callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        core.create_tenant(session, "New atomic reference company")
    session.rollback()
    assert {
        model: session.scalar(select(func.count()).select_from(model))
        for model in baseline
    } == baseline


def test_new_company_defaults_preserve_fixed_roles_without_financial_postings(session):
    from reality.db.core import LedgerEntry

    tenant = core.create_tenant(session, "New fixed reference company")
    rows = session.scalars(
        select(SubledgerAccount).where(SubledgerAccount.tenant_id == tenant.id)
    ).all()
    assert {row.role: row.name for row in rows} == BASE_ACCOUNT_ROLES
    assert all(row.state == "active" and row.revision == 1 for row in rows)
    assert (
        session.scalar(
            select(func.count())
            .select_from(LedgerEntry)
            .where(LedgerEntry.tenant_id == tenant.id)
        )
        == 0
    )
