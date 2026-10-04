"""Spec 356 FR-001–FR-003: finance configuration needs actual bounded consent."""

import json

import pytest
from intake_review_support import explicit_owner
from sqlalchemy import func, select

from reality.db.core import ChangeProposal, FinanceState, SubledgerAccount
from reality.services import core
from reality.services.finance import accounts
from reality.tools import finance
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def proposed_account(session, tenant_id):
    return create_change_proposal(
        session,
        tenant_id,
        "finance.account.create",
        {
            "code": "CONFIRMED-CONFIG",
            "name": "Exact account",
            "role": "accounts_receivable",
            "expected_revision": session.scalar(
                select(FinanceState.revision).where(FinanceState.tenant_id == tenant_id)
            ),
        },
    )


def account_count(session, tenant_id):
    return session.scalar(
        select(func.count())
        .select_from(SubledgerAccount)
        .where(SubledgerAccount.tenant_id == tenant_id)
    )


@pytest.mark.parametrize("auth_mode", ["enabled", "disabled"])
@pytest.mark.parametrize("operation", ["create", "update", "set_default"])
def test_direct_account_configuration_cannot_use_an_action_tag(
    session, business, monkeypatch, auth_mode, operation
):
    monkeypatch.setenv("REALITY_AUTH_MODE", auth_mode)
    tenant = business.tenant.id
    before = account_count(session, tenant)
    account = session.scalar(
        select(SubledgerAccount).where(
            SubledgerAccount.tenant_id == tenant,
            SubledgerAccount.role == "accounts_receivable",
        )
    )
    revision = session.scalar(
        select(FinanceState.revision).where(FinanceState.tenant_id == tenant)
    )
    unrelated = session.scalar(
        select(ChangeProposal.id)
        .where(ChangeProposal.tenant_id == tenant, ChangeProposal.status == "executed")
        .limit(1)
    )
    with (
        core.executing_proposal(tenant, unrelated),
        pytest.raises(core.InvalidOperation) as refused,
    ):
        if operation == "create":
            accounts.create_account(
                session,
                tenant,
                code="DIRECT",
                name="Unconfirmed",
                role="accounts_receivable",
                _commit=False,
            )
        elif operation == "update":
            accounts.update_account(
                session, tenant, account.id, name="Unconfirmed", _commit=False
            )
        else:
            accounts.set_default_account(
                session,
                tenant,
                role="accounts_receivable",
                account_id=account.id,
                _commit=False,
            )
    assert refused.value.code == "intake_approval_required"
    assert account_count(session, tenant) == before
    assert (
        session.scalar(
            select(FinanceState.revision).where(FinanceState.tenant_id == tenant)
        )
        == revision
    )


def test_direct_finance_dispatch_cannot_turn_a_proposal_into_consent(session, business):
    tenant = business.tenant.id
    owner = explicit_owner(session, tenant)
    proposal = proposed_account(session, tenant)
    before = account_count(session, tenant)
    with pytest.raises(core.InvalidOperation) as refused:
        finance.execute_finance_command(
            session,
            tenant,
            "finance.account.create",
            json.loads(proposal.input),
            action_id=proposal.id,
            actor_id=owner.user_id,
        )
    assert refused.value.code == "intake_approval_required"
    assert account_count(session, tenant) == before
    assert proposal.status == "proposed"


def test_finance_approval_without_actual_confirmation_is_inert(session, business):
    tenant = business.tenant.id
    owner = explicit_owner(session, tenant)
    proposal = proposed_account(session, tenant)
    before = account_count(session, tenant)
    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(
            session, tenant, proposal.id, confirming_principal=owner, confirmed=False
        )
    assert refused.value.code == "review_confirmation_required"
    assert account_count(session, tenant) == before
    assert proposal.status == "proposed"


@pytest.mark.parametrize("attack", ["replace_intent", "repeat_effect", "commit_midway"])
def test_confirmed_finance_configuration_refuses_callback_effect_changes(
    session, business, monkeypatch, attack
):
    tenant = business.tenant.id
    owner = explicit_owner(session, tenant)
    proposal = proposed_account(session, tenant)
    before = account_count(session, tenant)
    model, original = finance.ACCOUNT_COMMANDS["finance.account.create"]

    def changed(db, company, **values):
        if attack == "replace_intent":
            values["name"] = "Different unconfirmed account"
        if attack == "repeat_effect":
            original(db, company, **values)
        if attack == "commit_midway":
            original(db, company, **values)
            db.commit()
        return original(db, company, **values)

    monkeypatch.setitem(
        finance.ACCOUNT_COMMANDS, "finance.account.create", (model, changed)
    )
    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(
            session, tenant, proposal.id, confirming_principal=owner, confirmed=True
        )
    assert (
        refused.value.code
        == {
            "replace_intent": "intake_review_invalid",
            "repeat_effect": "intake_approval_required",
            "commit_midway": "intake_partial_commit_forbidden",
        }[attack]
    )
    assert account_count(session, tenant) == before


@pytest.mark.parametrize("role", ["exchange_difference", "customer_down_payments"])
def test_confirmed_account_tool_preserves_existing_registered_roles(
    session, business, role
):
    tenant = business.tenant.id
    owner = explicit_owner(session, tenant)
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.account.create",
        {
            "code": f"APPROVED-{role}",
            "name": f"Existing {role}",
            "role": role,
            "expected_revision": session.scalar(
                select(FinanceState.revision).where(FinanceState.tenant_id == tenant)
            ),
        },
    )
    result = approve_and_execute_proposal(
        session, tenant, proposal.id, confirming_principal=owner, confirmed=True
    )
    receipt = json.loads(result.output)
    assert receipt["role"] == role
    assert result.decided_by_user_id == owner.user_id


def test_finance_configuration_rechecks_a_demoted_owner_in_another_transaction(
    session, business, monkeypatch
):
    from sqlalchemy import update
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import TenantMembership

    tenant = business.tenant.id
    owner = explicit_owner(session, tenant)
    proposal = proposed_account(session, tenant)
    # Keep the old ORM role cached: checking a row's mere continued existence is
    # insufficient when another transaction changes this person's authority.
    cached = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant,
            TenantMembership.user_id == owner.user_id,
        )
    )
    assert cached.role == "owner"
    before = account_count(session, tenant)
    model, original = finance.ACCOUNT_COMMANDS["finance.account.create"]

    def changed(db, company, **values):
        with sessionmaker(db.get_bind())() as other:
            other.execute(
                update(TenantMembership)
                .where(
                    TenantMembership.tenant_id == tenant,
                    TenantMembership.user_id == owner.user_id,
                )
                .values(role="member")
            )
            other.commit()
        return original(db, company, **values)

    monkeypatch.setitem(
        finance.ACCOUNT_COMMANDS, "finance.account.create", (model, changed)
    )
    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(
            session, tenant, proposal.id, confirming_principal=owner, confirmed=True
        )
    assert refused.value.code == "company_owner_access_required"
    assert account_count(session, tenant) == before
