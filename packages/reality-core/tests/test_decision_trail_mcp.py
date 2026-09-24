"""Spec 263 US1: a decision settled through MCP names its token and the token's issuer."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from sqlalchemy.orm import sessionmaker

from reality.db.core import (
    AppUser,
    ChangeProposal,
    MCPAccessToken,
    TenantMembership,
    now,
    uid,
)
from reality.mcp import server as mcp_module
from reality.mcp.auth import create_mcp_access_token, revoke_mcp_access_token
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from reality.web import api as api_module
from reality.web import app as web_module
from reality.web import auth as auth_module

PASSWORD = "a-long-account-password"


def _owner(session, tenant_id: str, email: str, display_name: str) -> AppUser:
    user = AppUser(
        id=uid("usr"),
        email=email,
        password_hash=auth_module.password_hasher.hash(PASSWORD),
        display_name=display_name,
        status="active",
        email_verified_at=now(),
    )
    session.add(user)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("mem"),
            tenant_id=tenant_id,
            user_id=user.id,
            role="owner",
            status="active",
        )
    )
    session.commit()
    return user


def _payment_term(session, tenant_id: str, code: str) -> ChangeProposal:
    return create_change_proposal(
        session,
        tenant_id,
        "payment_term_create",
        {"code": code, "name": f"Term {code}", "due_days": 14},
    )


def _reload(session, proposal: ChangeProposal) -> ChangeProposal:
    # The MCP handler closes the session it was handed, detaching loaded rows.
    return session.get(
        ChangeProposal,
        {"tenant_id": proposal.tenant_id, "id": proposal.id},
        populate_existing=True,
    )


async def _as_token(session, monkeypatch, token: MCPAccessToken, tool: str, arguments):
    monkeypatch.setattr(mcp_module, "Session", lambda: session)
    access = AccessToken(
        token="test",
        client_id=token.id,
        scopes=["reality:read", "reality:tool:*"],
        subject=token.tenant_id,
    )
    context = auth_context_var.set(AuthenticatedUser(access))
    try:
        result = await mcp_module.build_server().call_tool(tool, arguments)
    finally:
        auth_context_var.reset(context)
    return json.loads(result[0].text)


def test_issuing_a_token_in_the_web_records_the_owner(session, business, monkeypatch):
    owner = _owner(session, business.tenant.id, "issuer@example.com", "Ivo Issuer")
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    browser = TestClient(web_module.app)
    login = browser.post(
        "/api/auth/login", json={"email": owner.email, "password": PASSWORD}
    )
    assert login.status_code == 200

    created = browser.post(
        f"/api/tenants/{business.tenant.id}/settings/mcp/tokens",
        json={"name": "Claude Desktop", "allowed_tools": ["*"]},
    )

    assert created.status_code == 201, created.text
    token = session.get(
        MCPAccessToken, {"tenant_id": business.tenant.id, "id": created.json()["id"]}
    )
    session.refresh(token)
    assert token.created_by_user_id == owner.id


def test_a_token_issued_outside_the_web_records_no_issuer(session, business):
    token, _ = create_mcp_access_token(session, business.tenant.id, "Script")

    assert token.created_by_user_id is None


@pytest.mark.anyio
async def test_mcp_approval_records_the_token_and_names_its_issuer(
    session, business, monkeypatch
):
    owner = _owner(session, business.tenant.id, "olga@example.com", "Olga Owner")
    token, _ = create_mcp_access_token(
        session, business.tenant.id, "Claude Desktop", issued_by_user_id=owner.id
    )
    proposal = _payment_term(session, business.tenant.id, "NET14")

    result = await _as_token(
        session,
        monkeypatch,
        token,
        "proposal_approve_and_execute",
        {"proposal_id": proposal.id, "approved": True},
    )

    proposal = _reload(session, proposal)
    assert proposal.status == "executed"
    assert proposal.decided_at is not None
    assert proposal.decided_via_token_id == token.id
    # The issuer answers for the token; Reality did not see them press anything.
    assert proposal.decided_by_user_id is None
    assert result["decider"] == {
        "kind": "mcp_token",
        "token_name": "Claude Desktop",
        "token_prefix": token.token_prefix,
        "revoked": False,
        "issuer": "Olga Owner",
    }


@pytest.mark.anyio
async def test_mcp_rejection_is_attributed_like_an_approval(
    session, business, monkeypatch
):
    token, _ = create_mcp_access_token(session, business.tenant.id, "Old agent")
    proposal = _payment_term(session, business.tenant.id, "NET30")

    result = await _as_token(
        session,
        monkeypatch,
        token,
        "proposal_reject",
        {"proposal_id": proposal.id, "rejected": True},
    )

    proposal = _reload(session, proposal)
    assert proposal.status == "rejected"
    assert proposal.decided_via_token_id == token.id
    assert proposal.decided_by_user_id is None
    # A token issued before spec 263 still works and reads with an unknown issuer.
    assert result["decider"]["kind"] == "mcp_token"
    assert result["decider"]["issuer"] is None


@pytest.mark.anyio
async def test_a_revoked_token_keeps_its_past_decisions_attributed(
    session, business, monkeypatch
):
    from reality.services.decision_attribution import decision_attributions

    owner = _owner(session, business.tenant.id, "rita@example.com", "Rita Owner")
    token, _ = create_mcp_access_token(
        session, business.tenant.id, "Retired agent", issued_by_user_id=owner.id
    )
    proposal = _payment_term(session, business.tenant.id, "NET7")
    await _as_token(
        session,
        monkeypatch,
        token,
        "proposal_approve_and_execute",
        {"proposal_id": proposal.id, "approved": True},
    )

    revoke_mcp_access_token(session, business.tenant.id, token.id)

    decider = decision_attributions(session, business.tenant.id, [proposal.id])[
        proposal.id
    ]["decider"]
    assert decider["token_name"] == "Retired agent"
    assert decider["revoked"] is True
    assert decider["issuer"] == "Rita Owner"


def test_a_signed_in_approval_records_the_person_and_no_token(session, business):
    owner = _owner(session, business.tenant.id, "web@example.com", "Wen Web")
    proposal = _payment_term(session, business.tenant.id, "NET60")

    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(owner.id),
    )

    assert proposal.decided_by_user_id == owner.id
    assert proposal.decided_via_token_id is None


def test_a_person_and_a_token_together_record_the_person_only(session, business):
    owner = _owner(session, business.tenant.id, "both@example.com", "Bo Both")
    token, _ = create_mcp_access_token(session, business.tenant.id, "Agent")
    proposal = _payment_term(session, business.tenant.id, "NET90")

    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(owner.id),
        settling_token_id=token.id,
    )

    assert proposal.decided_by_user_id == owner.id
    assert proposal.decided_via_token_id is None


def test_a_restored_proposal_forgets_its_token(session, business, monkeypatch):
    """A handler refusal restores the proposal; no attribution may outlive it."""
    from reality.services.core import InvalidOperation
    from reality.tools import application as application_module

    token, _ = create_mcp_access_token(session, business.tenant.id, "Agent")
    proposal = ChangeProposal(
        id=uid("act"),
        tenant_id=business.tenant.id,
        type="tool:graph.reports.change",
        actor_type="agent",
        status="proposed",
        input="{}",
        output="{}",
    )
    session.add(proposal)
    session.commit()

    def refuse(*_args, **_kwargs):
        raise InvalidOperation("refused")

    monkeypatch.setattr("reality.services.analytics.proposals.execute_change", refuse)
    monkeypatch.setattr(
        "reality.services.analytics.proposals.reveal", lambda *args, **kwargs: None
    )
    with pytest.raises(InvalidOperation):
        application_module.approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirmed=True,
            settling_token_id=token.id,
        )

    refreshed = session.get(
        ChangeProposal, {"tenant_id": business.tenant.id, "id": proposal.id}
    )
    session.refresh(refreshed)
    assert refreshed.status == "proposed"
    assert refreshed.decided_at is None
    assert refreshed.decided_via_token_id is None


@pytest.mark.anyio
async def test_a_token_the_company_does_not_hold_leaves_the_decider_unknown(
    session, business, monkeypatch
):
    proposal = _payment_term(session, business.tenant.id, "NET45")
    unknown = MCPAccessToken(id="mcp_not_stored", tenant_id=business.tenant.id)

    result = await _as_token(
        session,
        monkeypatch,
        unknown,
        "proposal_approve_and_execute",
        {"proposal_id": proposal.id, "approved": True},
    )

    proposal = _reload(session, proposal)
    assert proposal.status == "executed"
    assert proposal.decided_via_token_id is None
    assert result["decider"] == {"kind": "unknown"}
