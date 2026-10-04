"""Spec 356: fixed authored setup still requires current actual consent."""

import json
from datetime import timedelta
from types import SimpleNamespace

import pytest
from intake_review_support import explicit_owner
from sqlalchemy import func, select
from test_current_mcp_decision_authority import actual_confirmation_principal

from reality.db.core import (
    AppUser,
    ChangeProposal,
    Commitment,
    Document,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Party,
    SourceRecord,
    TenantMembership,
)
from reality.demo import normal_month
from reality.mcp.auth import create_mcp_access_token
from reality.mcp.catalog import dispatch_mcp_tool
from reality.services import core
from reality.tools import application


def fresh_company(session):
    tenant = core.create_tenant(session, "Actual fixed consent company")
    owner = explicit_owner(session, tenant.id)
    user = session.get(AppUser, owner.user_id)
    session.commit()
    return tenant, owner, user


def counts(session, tenant):
    return {
        model: session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        for model in (
            Party,
            Item,
            Location,
            SourceRecord,
            Document,
            Commitment,
            Movement,
            LedgerEntry,
        )
    }


@pytest.mark.parametrize("tool", ["demo_seed", "normal_month"])
@pytest.mark.parametrize(
    "change",
    [
        "grant_revoke",
        "credential_revoke",
        "expiry",
        "permission",
        "scope",
        "membership",
        "manual_token",
    ],
)
def test_fixed_setup_rechecks_actual_authority_before_its_canonical_write(
    session, monkeypatch, tool, change
):
    tenant, owner, user = fresh_company(session)
    grant, credential, principal = actual_confirmation_principal(
        session, SimpleNamespace(tenant=tenant), user
    )
    token, _ = create_mcp_access_token(
        session,
        tenant.id,
        "Actual fixed confirmation",
        ["proposal_approve_and_execute"],
        issued_by_user_id=user.id,
    )
    proposal = application.create_change_proposal(session, tenant.id, tool, {})
    baseline = counts(session, tenant.id)
    module = core if tool == "demo_seed" else normal_month
    original = module.create_party

    def callback(*args, **kwargs):
        if change == "grant_revoke":
            grant.revoked_at = core.now()
        elif change == "credential_revoke":
            credential.revoked_at = core.now()
        elif change == "expiry":
            credential.access_expires_at = core.now() - timedelta(seconds=1)
        elif change == "permission":
            grant.allowed_tools = ["stock"]
        elif change == "scope":
            grant.scopes = ["reality:read"]
        elif change == "membership":
            membership = session.scalars(
                select(TenantMembership).where(
                    TenantMembership.tenant_id == tenant.id,
                    TenantMembership.user_id == owner.user_id,
                )
            ).one()
            membership.status = "removed"
        else:
            token.revoked_at = core.now()
        session.flush()
        original(*args, **kwargs)
        pytest.fail(
            "The canonical fixed-profile writer accepted changed actual authority."
        )

    monkeypatch.setattr(module, "create_party", callback)
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        if change == "manual_token":
            application.approve_and_execute_proposal(
                session,
                tenant.id,
                proposal.id,
                confirmed=True,
                settling_token_id=token.id,
            )
        elif change == "membership":
            application.approve_and_execute_proposal(
                session,
                tenant.id,
                proposal.id,
                confirmed=True,
                confirming_principal=owner,
            )
        else:
            dispatch_mcp_tool(
                session,
                principal,
                "proposal_approve_and_execute",
                {"proposal_id": proposal.id, "approved": True},
            )
    assert refused.value.code == (
        "company_not_found" if change == "membership" else "intake_approval_required"
    )
    session.rollback()
    assert counts(session, tenant.id) == baseline


@pytest.mark.parametrize("tool", ["demo_seed", "normal_month"])
def test_fixed_setup_retains_actual_oauth_person_and_replays_its_receipt(session, tool):
    tenant, owner, user = fresh_company(session)
    _, _, principal = actual_confirmation_principal(
        session, SimpleNamespace(tenant=tenant), user
    )
    proposal = application.create_change_proposal(session, tenant.id, tool, {})
    response = dispatch_mcp_tool(
        session,
        principal,
        "proposal_approve_and_execute",
        {"proposal_id": proposal.id, "approved": True},
    )
    receipt = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant.id, ChangeProposal.id == proposal.id
        )
    )
    assert response["status"] == receipt.status == "executed"
    assert receipt.decided_by_user_id == owner.user_id
    assert receipt.decided_via_token_id is None
    assert json.loads(receipt.input)["profile"] in {
        "compact-demo.v2",
        "normal-month.v2",
    }
    before = counts(session, tenant.id)
    replay = dispatch_mcp_tool(
        session,
        principal,
        "proposal_approve_and_execute",
        {"proposal_id": proposal.id, "approved": True},
    )
    assert replay["status"] == "executed"
    assert counts(session, tenant.id) == before
