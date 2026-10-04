"""Spec 356: canonical effects require current real interactive MCP consent."""

from datetime import timedelta

import pytest
from sqlalchemy import func, select
from test_mcp_oauth_service import _challenge

from reality.db.core import ChangeProposal, Party, SubledgerAccount
from reality.db.mcp_authorization import MCPUserCredential
from reality.mcp.catalog import dispatch_mcp_tool
from reality.services import core
from reality.services.finance import accounts
from reality.services.mcp_authorization import (
    approve_interaction,
    create_interaction,
    exchange_code,
    resolve_interactive_principal,
)
from reality.tools.application import create_change_proposal
from reality.tools.finance import ACCOUNT_COMMANDS


def actual_confirmation_principal(session, business, owner, *, scopes=None, allowed_tools=None):
    verifier = "v" * 64
    interaction = create_interaction(
        session,
        client_id="https://client.example/metadata.json",
        client_metadata={"client_name": "Current consent proof"},
        redirect_uri="https://client.example/callback",
        resource="https://mcp.example/",
        requested_scopes=scopes or ["reality:confirm"],
        code_challenge=_challenge(verifier),
        state="opaque",
    )
    grant, code = approve_interaction(
        session,
        interaction.id,
        user_id=owner.id,
        tenant_id=business.tenant.id,
        allowed_tools=allowed_tools or ["proposal_approve_and_execute"],
    )
    issued = exchange_code(
        session,
        code=code,
        client_id=interaction.client_id,
        redirect_uri=interaction.redirect_uri,
        resource=interaction.resource,
        code_verifier=verifier,
    )
    principal = resolve_interactive_principal(session, issued.access_token)
    assert principal is not None
    credential = session.scalar(
        select(MCPUserCredential).where(
            MCPUserCredential.tenant_id == business.tenant.id,
            MCPUserCredential.id == principal.credential_id,
        )
    )
    return grant, credential, principal


@pytest.mark.parametrize("family", ["master", "finance"])
@pytest.mark.parametrize(
    "change", ["grant_revoke", "credential_revoke", "expiry", "permission", "scope"]
)
def test_real_interactive_authority_changed_after_dispatch_has_no_business_effect(
    session, business, scheduled_owner, monkeypatch, family, change
):
    tenant = business.tenant.id
    grant, credential, principal = actual_confirmation_principal(
        session, business, scheduled_owner
    )
    if family == "master":
        tool, arguments = (
            "party_create",
            {
                "records": [
                    {
                        "name": "Current MCP partner",
                        "type": "customer",
                        "roles": ["customer"],
                    }
                ]
            },
        )
        module, name, model = core, "create_party", Party
    else:
        tool, arguments = (
            "finance.account.create",
            {
                "code": "CURRENT-MCP",
                "name": "Current MCP account",
                "role": "cash",
                "expected_revision": accounts.list_accounts(session, tenant)[
                    "revision"
                ],
            },
        )
        module, name, model = accounts, "create_account", SubledgerAccount
    proposal = create_change_proposal(session, tenant, tool, arguments)
    before = session.scalar(
        select(func.count()).select_from(model).where(model.tenant_id == tenant)
    )
    original = getattr(module, name)

    def callback(*args, **values):
        if change == "grant_revoke":
            grant.revoked_at = core.now()
        elif change == "credential_revoke":
            credential.revoked_at = core.now()
        elif change == "expiry":
            credential.access_expires_at = core.now() - timedelta(seconds=1)
        elif change == "permission":
            grant.allowed_tools = ["exceptions_list"]
        else:
            grant.scopes = ["reality:read"]
        session.flush()
        return original(*args, **values)

    if family == "finance":
        request_model, _ = ACCOUNT_COMMANDS["finance.account.create"]
        monkeypatch.setitem(
            ACCOUNT_COMMANDS, "finance.account.create", (request_model, callback)
        )
    else:
        monkeypatch.setattr(module, name, callback)
    with pytest.raises(core.InvalidOperation) as refused:
        dispatch_mcp_tool(
            session,
            principal,
            "proposal_approve_and_execute",
            {"proposal_id": proposal.id, "approved": True},
        )
    assert refused.value.code == "intake_approval_required"
    session.rollback()
    assert (
        session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        == before
    )


@pytest.mark.parametrize("family", ["master", "finance"])
def test_real_current_interactive_confirmation_records_its_actual_person_and_receipt(
    session, business, scheduled_owner, family
):
    tenant = business.tenant.id
    grant, credential, principal = actual_confirmation_principal(
        session, business, scheduled_owner
    )
    if family == "master":
        tool, arguments = (
            "party_create",
            {
                "records": [
                    {
                        "name": "Current MCP partner",
                        "type": "customer",
                        "roles": ["customer"],
                    }
                ]
            },
        )
        model = Party
    else:
        tool, arguments = (
            "finance.account.create",
            {
                "code": "CURRENT-MCP",
                "name": "Current MCP account",
                "role": "cash",
                "expected_revision": accounts.list_accounts(session, tenant)[
                    "revision"
                ],
            },
        )
        model = SubledgerAccount
    proposal = create_change_proposal(session, tenant, tool, arguments)
    before = session.scalar(
        select(func.count()).select_from(model).where(model.tenant_id == tenant)
    )
    result = dispatch_mcp_tool(
        session,
        principal,
        "proposal_approve_and_execute",
        {"proposal_id": proposal.id, "approved": True},
    )
    receipt = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant, ChangeProposal.id == proposal.id
        )
    )
    assert result["status"] == receipt.status == "executed"
    assert receipt.decided_by_user_id == grant.user_id == scheduled_owner.id
    assert receipt.decided_via_token_id is None
    assert (
        credential.grant_id == grant.id
        and credential.revoked_at is None
        and grant.revoked_at is None
    )
    assert (
        session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        == before + 1
    )
    replay = dispatch_mcp_tool(
        session,
        principal,
        "proposal_approve_and_execute",
        {"proposal_id": proposal.id, "approved": True},
    )
    assert replay["status"] == "executed"
    assert (
        session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        == before + 1
    )
