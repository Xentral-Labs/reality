from __future__ import annotations

import base64
import hashlib
from dataclasses import replace
from datetime import timedelta

import httpx
import pytest
from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    SourceRecord,
    TenantMembership,
    now,
)
from reality.db.mcp_authorization import MCPClientGrant
from reality.mcp.catalog import MCP_TOOL_REGISTRY, dispatch_mcp_tool
from reality.mcp.principal import MCPPrincipal
from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_manual_order,
    create_tenant,
)
from reality.services.mcp_authorization import (
    approve_interaction,
    company_grants,
    create_interaction,
    deny_interaction,
    eligible_tools,
    exchange_code,
    personal_grants,
    resolve_client_metadata,
    resolve_interactive_principal,
    revoke_company_grant,
    revoke_grant,
    revoke_personal_grant,
    rotate_refresh_token,
)


def _challenge(verifier: str) -> str:
    return (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )


def _interaction(session, verifier: str = "v" * 64):
    return create_interaction(
        session,
        client_id="https://client.example/metadata.json",
        client_metadata={"client_name": "Example client"},
        redirect_uri="https://client.example/callback",
        resource="https://mcp.example/",
        requested_scopes=["reality:read"],
        code_challenge=_challenge(verifier),
        state="opaque",
    )


def _issued_credential(session, business, scheduled_owner, tool="exceptions_list"):
    verifier = "v" * 64
    interaction = _interaction(session, verifier)
    grant, code = approve_interaction(
        session,
        interaction.id,
        user_id=scheduled_owner.id,
        tenant_id=business.tenant.id,
        allowed_tools=[tool],
    )
    issued = exchange_code(
        session,
        code=code,
        client_id=interaction.client_id,
        redirect_uri=interaction.redirect_uri,
        resource=interaction.resource,
        code_verifier=verifier,
    )
    return grant, issued


def test_authorization_code_is_single_use_and_credentials_are_hashed(
    session, business, scheduled_owner
):
    verifier = "v" * 64
    interaction = _interaction(session, verifier)
    selected = eligible_tools(interaction)[0]
    grant, code = approve_interaction(
        session,
        interaction.id,
        user_id=scheduled_owner.id,
        tenant_id=business.tenant.id,
        allowed_tools=[selected],
    )

    issued = exchange_code(
        session,
        code=code,
        client_id=interaction.client_id,
        redirect_uri=interaction.redirect_uri,
        resource=interaction.resource,
        code_verifier=verifier,
    )
    assert issued.access_token not in repr(session.identity_map.values())
    principal = resolve_interactive_principal(session, issued.access_token)
    assert principal is not None
    assert principal.tenant_id == business.tenant.id
    assert principal.user_id == scheduled_owner.id
    assert principal.allowed_tools == {selected}

    with pytest.raises(InvalidOperation, match="Invalid or expired"):
        exchange_code(
            session,
            code=code,
            client_id=interaction.client_id,
            redirect_uri=interaction.redirect_uri,
            resource=interaction.resource,
            code_verifier=verifier,
        )

    revoke_grant(
        session,
        tenant_id=business.tenant.id,
        grant_id=grant.id,
        actor_user_id=scheduled_owner.id,
    )
    assert resolve_interactive_principal(session, issued.access_token) is None


def test_consent_starts_without_implicit_tools_and_rejects_scope_escalation(
    session, business, scheduled_owner
):
    interaction = _interaction(session)
    assert eligible_tools(interaction)
    with pytest.raises(InvalidOperation, match="exceed"):
        approve_interaction(
            session,
            interaction.id,
            user_id=scheduled_owner.id,
            tenant_id=business.tenant.id,
            allowed_tools=["reservation_propose"],
        )


def test_denied_interaction_cannot_be_approved(session, business, scheduled_owner):
    interaction = _interaction(session)
    deny_interaction(session, interaction.id, user_id=scheduled_owner.id)
    with pytest.raises(InvalidOperation, match="unavailable"):
        approve_interaction(
            session,
            interaction.id,
            user_id=scheduled_owner.id,
            tenant_id=business.tenant.id,
            allowed_tools=[eligible_tools(interaction)[0]],
        )


def test_expired_interaction_cannot_create_a_grant(session, business, scheduled_owner):
    interaction = _interaction(session)
    interaction.expires_at = now() - timedelta(seconds=1)
    session.commit()
    with pytest.raises(InvalidOperation, match="unavailable"):
        approve_interaction(
            session,
            interaction.id,
            user_id=scheduled_owner.id,
            tenant_id=business.tenant.id,
            allowed_tools=[eligible_tools(interaction)[0]],
        )


def test_refresh_rotates_and_reuse_revokes_the_family(
    session, business, scheduled_owner
):
    verifier = "v" * 64
    interaction = _interaction(session, verifier)
    _, code = approve_interaction(
        session,
        interaction.id,
        user_id=scheduled_owner.id,
        tenant_id=business.tenant.id,
        allowed_tools=[eligible_tools(interaction)[0]],
    )
    original = exchange_code(
        session,
        code=code,
        client_id=interaction.client_id,
        redirect_uri=interaction.redirect_uri,
        resource=interaction.resource,
        code_verifier=verifier,
    )
    rotated = rotate_refresh_token(
        session,
        refresh_token=original.refresh_token,
        client_id=interaction.client_id,
    )
    assert resolve_interactive_principal(session, rotated.access_token) is not None

    with pytest.raises(InvalidOperation, match="Invalid refresh"):
        rotate_refresh_token(
            session,
            refresh_token=original.refresh_token,
            client_id=interaction.client_id,
        )
    assert resolve_interactive_principal(session, rotated.access_token) is None


@pytest.mark.parametrize("authority_loss", ["user", "membership", "company"])
def test_interactive_principal_rechecks_live_account_membership_and_company(
    session, business, scheduled_owner, authority_loss
):
    _, issued = _issued_credential(session, business, scheduled_owner)
    assert resolve_interactive_principal(session, issued.access_token) is not None

    if authority_loss == "user":
        scheduled_owner.status = "disabled"
    elif authority_loss == "membership":
        membership = (
            session.query(TenantMembership)
            .filter_by(
                tenant_id=business.tenant.id,
                user_id=scheduled_owner.id,
            )
            .one()
        )
        membership.status = "removed"
    else:
        business.tenant.archived_at = now()
    session.commit()

    assert resolve_interactive_principal(session, issued.access_token) is None


def test_code_exchange_rejects_wrong_client_and_resource(
    session, business, scheduled_owner
):
    verifier = "v" * 64
    interaction = _interaction(session, verifier)
    _, code = approve_interaction(
        session,
        interaction.id,
        user_id=scheduled_owner.id,
        tenant_id=business.tenant.id,
        allowed_tools=["exceptions_list"],
    )

    with pytest.raises(InvalidOperation, match="Invalid or expired"):
        exchange_code(
            session,
            code=code,
            client_id="https://other.example/metadata.json",
            redirect_uri=interaction.redirect_uri,
            resource=interaction.resource,
            code_verifier=verifier,
        )
    with pytest.raises(InvalidOperation, match="Invalid or expired"):
        exchange_code(
            session,
            code=code,
            client_id=interaction.client_id,
            redirect_uri=interaction.redirect_uri,
            resource="https://other-mcp.example/",
            code_verifier=verifier,
        )


def test_approval_refuses_company_without_current_membership(session, scheduled_owner):
    foreign = create_tenant(session, "Foreign company")
    interaction = _interaction(session)

    with pytest.raises(NotFound, match="Eligible company not found"):
        approve_interaction(
            session,
            interaction.id,
            user_id=scheduled_owner.id,
            tenant_id=foreign.id,
            allowed_tools=["exceptions_list"],
        )


def test_principal_intersects_frozen_tools_with_current_scope_and_catalog(
    session, business, scheduled_owner, monkeypatch
):
    grant, issued = _issued_credential(session, business, scheduled_owner)
    principal = resolve_interactive_principal(session, issued.access_token)
    assert principal is not None
    assert principal.allowed_tools == {"exceptions_list"}
    assert not principal.permits("inventory_read")

    catalog_growth = replace(
        MCP_TOOL_REGISTRY["exceptions_list"], name="future_read_tool"
    )
    monkeypatch.setitem(MCP_TOOL_REGISTRY, catalog_growth.name, catalog_growth)
    principal = resolve_interactive_principal(session, issued.access_token)
    assert principal is not None
    assert not principal.permits(catalog_growth.name)

    stored_grant = session.get(MCPClientGrant, (business.tenant.id, grant.id))
    assert stored_grant is not None
    stored_grant.scopes = ["reality:propose"]
    session.commit()
    assert resolve_interactive_principal(session, issued.access_token) is None


def test_manual_and_interactive_reads_preserve_trace_and_cross_tenant_not_found(
    session, business, scheduled_owner
):
    source, document, lines, commitments = create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "MCP-TRACE-1",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit": "pcs",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
        "20",
    )
    interactive = MCPPrincipal(
        "interactive",
        "credential_1",
        "grant_1",
        scheduled_owner.id,
        business.tenant.id,
        "client_1",
        frozenset({"reality:read"}),
        frozenset({"order_explain"}),
    )
    manual = MCPPrincipal(
        "manual",
        "manual_1",
        None,
        None,
        business.tenant.id,
        "manual_1",
        frozenset({"reality:read", "reality:tool:order_explain"}),
        frozenset({"order_explain"}),
    )
    arguments = {"order_reference": document.id}

    interactive_result = dispatch_mcp_tool(
        session, interactive, "order_explain", arguments
    )
    manual_result = dispatch_mcp_tool(session, manual, "order_explain", arguments)

    interactive_observed = interactive_result["metadata"].pop("observed_at")
    manual_observed = manual_result["metadata"].pop("observed_at")
    assert interactive_observed and manual_observed
    assert interactive_result == manual_result
    assert interactive_result["source"]["source_record_id"] == source.id
    assert interactive_result["document_lines"][0]["id"] == lines[0].id
    assert interactive_result["fulfillment"]["document_id"] == document.id
    assert commitments[0].document_id == document.id
    assert commitments[0].document_line_id == lines[0].id
    assert session.get(SourceRecord, (business.tenant.id, source.id)) is source
    assert session.get(Document, (business.tenant.id, document.id)) is document
    assert session.get(DocumentLine, (business.tenant.id, lines[0].id)) is lines[0]
    assert (
        session.get(Commitment, (business.tenant.id, commitments[0].id))
        is commitments[0]
    )

    foreign = create_tenant(session, "Foreign MCP trace")
    foreign_principal = MCPPrincipal(
        "interactive",
        "credential_foreign",
        "grant_foreign",
        scheduled_owner.id,
        foreign.id,
        "client_foreign",
        frozenset({"reality:read"}),
        frozenset({"order_explain"}),
    )
    with pytest.raises(NotFound):
        dispatch_mcp_tool(session, foreign_principal, "order_explain", arguments)


def test_grant_inventory_reconsent_distinct_company_redaction_and_isolated_revoke(
    session, business, scheduled_owner
):
    second = create_tenant(session, "Second company", _commit=False)
    session.add(
        TenantMembership(
            id="tmb_second_grant",
            tenant_id=second.id,
            user_id=scheduled_owner.id,
            role="owner",
            status="active",
        )
    )
    session.commit()

    first, first_issued = _issued_credential(session, business, scheduled_owner)
    replacement_interaction = _interaction(session)
    replacement, _ = approve_interaction(
        session,
        replacement_interaction.id,
        user_id=scheduled_owner.id,
        tenant_id=business.tenant.id,
        allowed_tools=["exceptions_list"],
    )
    distinct_interaction = _interaction(session)
    distinct, _ = approve_interaction(
        session,
        distinct_interaction.id,
        user_id=scheduled_owner.id,
        tenant_id=second.id,
        allowed_tools=["exceptions_list"],
    )

    personal = personal_grants(session, scheduled_owner.id)
    assert {item["id"] for item in personal} == {first.id, replacement.id, distinct.id}
    assert (
        next(item for item in personal if item["id"] == first.id)["effective_state"]
        == "revoked"
    )
    assert (
        next(item for item in personal if item["id"] == replacement.id)[
            "effective_state"
        ]
        == "active"
    )
    assert all("token" not in repr(item).lower() for item in personal)
    assert resolve_interactive_principal(session, first_issued.access_token) is None

    company = company_grants(session, business.tenant.id, scheduled_owner.id)
    assert {item["id"] for item in company} == {first.id, replacement.id}
    assert all(item["authorized_by"]["id"] == scheduled_owner.id for item in company)
    with pytest.raises(NotFound):
        revoke_company_grant(
            session, business.tenant.id, distinct.id, scheduled_owner.id
        )

    revoke_personal_grant(session, replacement.id, scheduled_owner.id)
    revoke_personal_grant(session, replacement.id, scheduled_owner.id)
    assert (
        next(
            item
            for item in personal_grants(session, scheduled_owner.id)
            if item["id"] == replacement.id
        )["effective_state"]
        == "revoked"
    )
    assert (
        next(
            item
            for item in personal_grants(session, scheduled_owner.id)
            if item["id"] == distinct.id
        )["effective_state"]
        == "active"
    )


def test_cimd_requires_public_https_exact_identity_and_bounded_document(monkeypatch):
    client_id = "https://client.example/oauth.json"
    addresses = [(None, None, None, None, ("8.8.8.8", 443))]
    monkeypatch.setattr("socket.getaddrinfo", lambda *_args, **_kwargs: addresses)

    document = (
        b'{"client_id":"https://client.example/oauth.json",'
        b'"client_name":"Client","redirect_uris":["https://client.example/cb"]}'
    )
    client = resolve_client_metadata(client_id, environ={}, fetch=lambda _url: document)
    assert client.redirect_uris == ("https://client.example/cb",)

    with pytest.raises(InvalidOperation, match="valid CIMD"):
        resolve_client_metadata("http://client.example/oauth.json", environ={})
    with pytest.raises(InvalidOperation, match="identity"):
        resolve_client_metadata(
            client_id,
            environ={},
            fetch=lambda _url: document.replace(
                b"client.example/oauth", b"other.example/oauth"
            ),
        )
    with pytest.raises(InvalidOperation, match="size"):
        resolve_client_metadata(
            client_id, environ={}, fetch=lambda _url: b"x" * (64 * 1024 + 1)
        )


def test_cimd_rejects_private_addresses_and_dns_rebinding(monkeypatch):
    client_id = "https://client.example/oauth.json"
    private = [(None, None, None, None, ("127.0.0.1", 443))]
    monkeypatch.setattr("socket.getaddrinfo", lambda *_args, **_kwargs: private)
    with pytest.raises(InvalidOperation, match="not public"):
        resolve_client_metadata(client_id, environ={}, fetch=lambda _url: b"{}")

    calls = iter(
        [
            [(None, None, None, None, ("8.8.8.8", 443))],
            [(None, None, None, None, ("1.1.1.1", 443))],
        ]
    )
    monkeypatch.setattr("socket.getaddrinfo", lambda *_args, **_kwargs: next(calls))
    document = (
        b'{"client_id":"https://client.example/oauth.json",'
        b'"client_name":"Client","redirect_uris":["https://client.example/cb"]}'
    )
    with pytest.raises(InvalidOperation, match="changed"):
        resolve_client_metadata(client_id, environ={}, fetch=lambda _url: document)


def test_cimd_rejects_redirects_and_fetch_timeouts(monkeypatch):
    client_id = "https://client.example/oauth.json"
    public = [(None, None, None, None, ("8.8.8.8", 443))]
    monkeypatch.setattr("socket.getaddrinfo", lambda *_args, **_kwargs: public)

    class Redirect:
        is_redirect = True

    monkeypatch.setattr(httpx, "get", lambda *_args, **_kwargs: Redirect())
    with pytest.raises(InvalidOperation, match="redirects"):
        resolve_client_metadata(client_id, environ={})

    def timeout(*_args, **_kwargs):
        raise httpx.ReadTimeout("bounded")

    monkeypatch.setattr(httpx, "get", timeout)
    with pytest.raises(InvalidOperation, match="unavailable"):
        resolve_client_metadata(client_id, environ={})
