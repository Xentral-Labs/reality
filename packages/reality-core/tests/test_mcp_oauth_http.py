from __future__ import annotations

import base64
import hashlib
import json
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi.testclient import TestClient
from mcp.server.auth.provider import AccessToken
from sqlalchemy import select

from reality.db.core import AppUser, PlaygroundRun, Tenant, TenantMembership, now, uid
from reality.db.mcp_authorization import MCPAuthorizationInteraction
from reality.mcp.catalog import MCP_TOOL_NAMES
from reality.mcp.server import build_server
from reality.services import mcp_authorization as authorization_service
from reality.services.mcp_authorization import create_interaction
from reality.web import auth as auth_module
from reality.web.app import app


@pytest.fixture(autouse=True)
def clear_oauth_dependency_overrides():
    yield
    app.dependency_overrides.clear()


def _challenge(verifier: str) -> str:
    return (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )


def _overrides(session, user):
    def database():
        yield session

    app.dependency_overrides[auth_module.database_session] = database
    app.dependency_overrides[auth_module.current_user] = lambda: user


def test_authorization_metadata_advertises_only_supported_public_flows(monkeypatch):
    monkeypatch.setenv("API_URL", "https://api.example.test")
    monkeypatch.setenv("MCP_URL", "https://mcp.example.test/")
    with TestClient(app) as client:
        metadata = client.get("/.well-known/oauth-authorization-server").json()
        oidc = client.get("/.well-known/openid-configuration").json()

    assert metadata == oidc
    assert metadata["issuer"] == "https://api.example.test"
    assert metadata["response_types_supported"] == ["code"]
    assert metadata["code_challenge_methods_supported"] == ["S256"]
    assert metadata["token_endpoint_auth_methods_supported"] == ["none"]
    assert "registration_endpoint" not in metadata


def test_a_leftover_disable_setting_no_longer_switches_authorization_off(monkeypatch):
    """FR-023: interactive authorization is a permanent part of the MCP boundary.

    An existing deployment may still carry the removed setting; it must not bring the
    old 503 back.
    """
    monkeypatch.setenv("MCP_INTERACTIVE_AUTH_ENABLED", "false")
    monkeypatch.setenv("API_URL", "https://api.example.test")
    monkeypatch.setenv("MCP_URL", "https://mcp.example.test/")
    with TestClient(app) as client:
        metadata = client.get("/.well-known/oauth-authorization-server")
    assert metadata.status_code == 200
    assert metadata.json()["issuer"] == "https://api.example.test"


def test_authorization_outage_unsupported_client_and_issuer_change_fail_safely(
    session, monkeypatch
):
    before = session.query(MCPAuthorizationInteraction).count()
    monkeypatch.setenv("MCP_OAUTH_CLIENTS", "{}")
    monkeypatch.setenv("MCP_URL", "https://mcp.example.test/")
    with TestClient(app) as client:
        authorize = client.get(
            "/oauth/authorize",
            params={
                "response_type": "code",
                "client_id": "unsupported",
                "redirect_uri": "https://client.example/callback",
                "code_challenge": "c" * 43,
                "code_challenge_method": "S256",
                "resource": "https://mcp.example.test/",
                "scope": "reality:read",
            },
        )
    assert authorize.status_code == 400
    assert authorize.json()["error"] == "invalid_request"
    assert session.query(MCPAuthorizationInteraction).count() == before

    with TestClient(app) as client:
        unsupported = client.get(
            "/oauth/authorize",
            params={
                "response_type": "code",
                "client_id": "unsupported",
                "redirect_uri": "https://client.example/callback",
                "code_challenge": "c" * 43,
                "code_challenge_method": "S256",
                "resource": "https://mcp.example.test/",
                "scope": "reality:read",
            },
        )
        assert unsupported.status_code == 400
        assert unsupported.json()["error"] == "invalid_request"
        assert "token" not in unsupported.text.lower()

        monkeypatch.setenv("API_URL", "https://issuer-one.example")
        first = client.get("/.well-known/oauth-authorization-server").json()
        monkeypatch.setenv("API_URL", "https://issuer-two.example")
        second = client.get("/.well-known/oauth-authorization-server").json()
    assert first["issuer"] == "https://issuer-one.example"
    assert second["issuer"] == "https://issuer-two.example"
    assert second["authorization_endpoint"].startswith("https://issuer-two.example/")


def test_cimd_metadata_change_is_revalidated_without_stale_authorization(
    session, scheduled_owner, monkeypatch
):
    monkeypatch.setenv("MCP_OAUTH_CLIENTS", "{}")
    monkeypatch.setenv("MCP_URL", "https://mcp.example.test/")
    _overrides(session, scheduled_owner)
    monkeypatch.setattr(
        authorization_service.socket,
        "getaddrinfo",
        lambda *_a, **_k: [(None, None, None, None, ("8.8.8.8", 443))],
    )
    current_redirect = "https://client.example/first"

    class MetadataResponse:
        is_redirect = False

        @property
        def content(self):
            return json.dumps(
                {
                    "client_id": "https://client.example/oauth.json",
                    "client_name": "Changing client",
                    "redirect_uris": [current_redirect],
                }
            ).encode()

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        authorization_service.httpx, "get", lambda *_a, **_k: MetadataResponse()
    )
    common = {
        "response_type": "code",
        "client_id": "https://client.example/oauth.json",
        "code_challenge": "c" * 43,
        "code_challenge_method": "S256",
        "resource": "https://mcp.example.test/",
        "scope": "reality:read",
    }
    with TestClient(app) as client:
        accepted = client.get(
            "/oauth/authorize",
            params={**common, "redirect_uri": current_redirect},
            follow_redirects=False,
        )
        current_redirect = "https://client.example/second"
        stale = client.get(
            "/oauth/authorize",
            params={**common, "redirect_uri": "https://client.example/first"},
            follow_redirects=False,
        )
        refreshed = client.get(
            "/oauth/authorize",
            params={**common, "redirect_uri": current_redirect},
            follow_redirects=False,
        )
    assert accepted.status_code == refreshed.status_code == 303
    assert stale.status_code == 400
    assert "not registered" in stale.json()["error_description"]


def test_resource_server_uses_transport_401_and_403_challenges():
    class InsufficientVerifier:
        async def verify_token(self, token: str):
            return AccessToken(
                token=token,
                client_id="client",
                scopes=["reality:propose"],
                subject="tenant",
                resource="http://localhost:8001/",
            )

    server = build_server(
        public_url="http://localhost:8001/",
        authorization_issuer="http://localhost:8000",
        token_verifier=InsufficientVerifier(),
    )
    runtime = server.streamable_http_app(
        streamable_http_path="/", stateless_http=True, json_response=True
    )
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2026-07-28",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        },
    }
    with TestClient(runtime) as client:
        missing = client.post("/", json=initialize)
        insufficient = client.post(
            "/",
            json=initialize,
            headers={
                "Authorization": "Bearer insufficient",
                "Accept": "application/json, text/event-stream",
            },
        )
    assert missing.status_code == 401
    assert "resource_metadata=" in missing.headers["www-authenticate"]
    assert insufficient.status_code == 403
    challenge = insufficient.headers["www-authenticate"]
    assert 'error="insufficient_scope"' in challenge
    assert "resource_metadata=" in challenge


def test_authorize_consent_exchange_and_revoke_http_contract(
    session, business, scheduled_owner, monkeypatch
):
    verifier = "v" * 64
    monkeypatch.setenv("API_URL", "https://api.example.test")
    monkeypatch.setenv("APP_URL", "https://app.example.test")
    monkeypatch.setenv("MCP_URL", "https://mcp.example.test/")
    monkeypatch.setenv(
        "MCP_OAUTH_CLIENTS",
        json.dumps(
            {
                "client-a": {
                    "client_name": "Client A",
                    "redirect_uris": ["https://client.example/callback"],
                }
            }
        ),
    )
    _overrides(session, scheduled_owner)

    with TestClient(app) as client:
        authorize = client.get(
            "/oauth/authorize",
            params={
                "response_type": "code",
                "client_id": "client-a",
                "redirect_uri": "https://client.example/callback",
                "code_challenge": _challenge(verifier),
                "code_challenge_method": "S256",
                "resource": "https://mcp.example.test/",
                "scope": "reality:read",
                "state": "client-state",
            },
            follow_redirects=False,
        )
        assert authorize.status_code == 303
        location = authorize.headers["location"]
        assert location.startswith(
            "https://app.example.test/oauth/authorize?interaction="
        )
        interaction_id = parse_qs(urlparse(location).query)["interaction"][0]

        view = client.get(f"/api/oauth/interactions/{interaction_id}")
        assert view.status_code == 200
        body = view.json()
        assert body["client"]["name"] == "Client A"
        assert body["selected_tools"] == [
            tool["name"] for tool in body["eligible_tools"]
        ]
        assert body["companies"] == [
            {
                "id": business.tenant.id,
                "name": business.tenant.name,
                "role": "owner",
                "ready": True,
            }
        ]
        tool = body["eligible_tools"][0]["name"]

        approval = client.post(
            f"/api/oauth/interactions/{interaction_id}/approve",
            json={
                "company_id": business.tenant.id,
                "allowed_tools": [tool],
                "confirmed": True,
            },
            follow_redirects=False,
        )
        assert approval.status_code == 303
        callback = urlparse(approval.headers["location"])
        callback_values = parse_qs(callback.query)
        assert callback_values["state"] == ["client-state"]
        assert callback_values["iss"] == ["https://api.example.test"]

        tokens = client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": callback_values["code"][0],
                "client_id": "client-a",
                "redirect_uri": "https://client.example/callback",
                "code_verifier": verifier,
                "resource": "https://mcp.example.test/",
            },
        )
        assert tokens.status_code == 200
        issued = tokens.json()
        assert issued["token_type"] == "Bearer"
        assert issued["expires_in"] == 900
        assert issued["scope"] == "reality:read"

        revoked = client.post("/oauth/revoke", data={"token": issued["access_token"]})
        assert revoked.status_code == 200


def test_browser_decisions_expose_only_same_origin_completion_path(
    session, business, scheduled_owner, monkeypatch
):
    monkeypatch.setenv("API_URL", "https://api.example.test")
    monkeypatch.setenv(
        "MCP_OAUTH_CLIENTS",
        json.dumps(
            {
                "client-a": {
                    "client_name": "Client A",
                    "redirect_uris": ["https://client.example/callback"],
                }
            }
        ),
    )
    _overrides(session, scheduled_owner)
    interaction = create_interaction(
        session,
        client_id="client-a",
        client_metadata={"client_name": "Client A"},
        redirect_uri="https://client.example/callback",
        resource="https://mcp.example.test/",
        requested_scopes=["reality:read"],
        code_challenge="c" * 43,
        state="opaque-state",
    )

    with TestClient(app, base_url="https://api.example.test") as client:
        approval = client.post(
            f"/api/oauth/interactions/{interaction.id}/approve",
            headers={"Accept": "application/json"},
            json={
                "company_id": business.tenant.id,
                "allowed_tools": ["exceptions_list"],
                "confirmed": True,
            },
        )
        assert approval.status_code == 200
        assert approval.json() == {
            "completion_path": f"/oauth/complete/{interaction.id}"
        }
        assert "code" not in approval.text
        assert "client.example" not in approval.text

        completion = client.get(
            approval.json()["completion_path"], follow_redirects=False
        )

    assert completion.status_code == 303
    callback = urlparse(completion.headers["location"])
    assert callback.netloc == "client.example"
    assert parse_qs(callback.query)["state"] == ["opaque-state"]
    assert "reality_oauth_completion=" in completion.headers["set-cookie"]


def test_personal_and_company_grant_inventory_revoke_and_redact(
    session, business, scheduled_owner, monkeypatch
):
    verifier = "v" * 64
    _overrides(session, scheduled_owner)
    interaction = create_interaction(
        session,
        client_id="client-a",
        client_metadata={
            "client_name": "Client A",
            "client_uri": "https://client.example",
        },
        redirect_uri="https://client.example/callback",
        resource="https://mcp.example.test/",
        requested_scopes=["reality:read"],
        code_challenge=_challenge(verifier),
        state="opaque-state",
    )
    grant, code = authorization_service.approve_interaction(
        session,
        interaction.id,
        user_id=scheduled_owner.id,
        tenant_id=business.tenant.id,
        allowed_tools=["exceptions_list"],
    )
    issued = authorization_service.exchange_code(
        session,
        code=code,
        client_id=interaction.client_id,
        redirect_uri=interaction.redirect_uri,
        resource=interaction.resource,
        code_verifier=verifier,
    )

    with TestClient(app) as client:
        personal = client.get("/api/auth/mcp-grants")
        company = client.get(f"/api/tenants/{business.tenant.id}/settings/mcp/grants")
        assert personal.status_code == company.status_code == 200
        assert personal.json()["grants"][0]["id"] == grant.id
        assert company.json()["grants"][0]["authorized_by"]["id"] == scheduled_owner.id
        exposed = personal.text + company.text
        assert issued.access_token not in exposed
        assert issued.refresh_token not in exposed
        assert "token_prefix" not in exposed

        assert (
            client.post(
                f"/api/auth/mcp-grants/{grant.id}/revoke",
                json={"confirmed": False},
            ).status_code
            == 400
        )
        assert (
            client.post(
                f"/api/tenants/ten_unknown/settings/mcp/grants/{grant.id}/revoke",
                json={"confirmed": True},
            ).status_code
            == 404
        )
        revoked = client.post(
            f"/api/auth/mcp-grants/{grant.id}/revoke",
            json={"confirmed": True},
        )
        assert revoked.status_code == 204
        assert (
            client.post(
                f"/api/auth/mcp-grants/{grant.id}/revoke",
                json={"confirmed": True},
            ).status_code
            == 204
        )
        assert (
            client.get("/api/auth/mcp-grants").json()["grants"][0]["effective_state"]
            == "revoked"
        )

    assert (
        authorization_service.resolve_interactive_principal(
            session, issued.access_token
        )
        is None
    )


def test_authorize_rejects_redirect_resource_and_pkce_mismatch(monkeypatch):
    monkeypatch.setenv("MCP_URL", "https://mcp.example.test/")
    monkeypatch.setenv(
        "MCP_OAUTH_CLIENTS",
        json.dumps(
            {
                "client-a": {
                    "client_name": "Client A",
                    "redirect_uris": ["https://client.example/callback"],
                }
            }
        ),
    )
    base = {
        "response_type": "code",
        "client_id": "client-a",
        "redirect_uri": "https://evil.example/callback",
        "code_challenge": "invalid",
        "code_challenge_method": "plain",
        "resource": "https://other.example/",
        "scope": "reality:read",
    }
    with TestClient(app) as client:
        response = client.get("/oauth/authorize", params=base)
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"


def test_authorize_accepts_exact_pre_registered_and_cimd_clients(
    session, scheduled_owner, monkeypatch
):
    monkeypatch.setenv("MCP_URL", "https://mcp.example.test/")
    monkeypatch.setenv(
        "MCP_OAUTH_CLIENTS",
        json.dumps(
            {
                "registered-client": {
                    "client_name": "Registered Client",
                    "redirect_uris": ["https://registered.example/callback"],
                }
            }
        ),
    )
    _overrides(session, scheduled_owner)
    common = {
        "response_type": "code",
        "code_challenge": "c" * 43,
        "code_challenge_method": "S256",
        "resource": "https://mcp.example.test/",
        "scope": "reality:read",
    }

    public = [(None, None, None, None, ("8.8.8.8", 443))]
    monkeypatch.setattr(
        authorization_service.socket, "getaddrinfo", lambda *_a, **_k: public
    )

    class MetadataResponse:
        is_redirect = False
        content = json.dumps(
            {
                "client_id": "https://client.example/oauth.json",
                "client_name": "CIMD Client",
                "redirect_uris": ["https://client.example/callback"],
            }
        ).encode()

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        authorization_service.httpx, "get", lambda *_a, **_k: MetadataResponse()
    )

    with TestClient(app) as client:
        registered = client.get(
            "/oauth/authorize",
            params={
                **common,
                "client_id": "registered-client",
                "redirect_uri": "https://registered.example/callback",
            },
            follow_redirects=False,
        )
        cimd = client.get(
            "/oauth/authorize",
            params={
                **common,
                "client_id": "https://client.example/oauth.json",
                "redirect_uri": "https://client.example/callback",
            },
            follow_redirects=False,
        )

    assert registered.status_code == 303
    assert cimd.status_code == 303


@pytest.mark.parametrize(
    ("failure", "client_id", "expected"),
    [
        ("insecure", "http://client.example/oauth.json", "valid CIMD"),
        ("private", "https://client.example/oauth.json", "not public"),
        ("redirect", "https://client.example/oauth.json", "redirects"),
        ("oversize", "https://client.example/oauth.json", "size limit"),
        ("timeout", "https://client.example/oauth.json", "unavailable"),
        ("rebind", "https://client.example/oauth.json", "changed during fetch"),
    ],
)
def test_authorize_rejects_unsafe_cimd_without_creating_interaction(
    session,
    scheduled_owner,
    monkeypatch,
    failure,
    client_id,
    expected,
):
    monkeypatch.setenv("MCP_URL", "https://mcp.example.test/")
    monkeypatch.setenv("MCP_OAUTH_CLIENTS", "{}")
    _overrides(session, scheduled_owner)
    public = [(None, None, None, None, ("8.8.8.8", 443))]
    rebound = [(None, None, None, None, ("1.1.1.1", 443))]
    private = [(None, None, None, None, ("127.0.0.1", 443))]
    addresses = iter([public, rebound]) if failure == "rebind" else None
    monkeypatch.setattr(
        authorization_service.socket,
        "getaddrinfo",
        lambda *_a, **_k: (
            next(addresses)
            if addresses is not None
            else (private if failure == "private" else public)
        ),
    )

    class MetadataResponse:
        is_redirect = failure == "redirect"
        content = (
            b"x" * (authorization_service.MAX_CLIENT_METADATA_BYTES + 1)
            if failure == "oversize"
            else json.dumps(
                {
                    "client_id": client_id,
                    "client_name": "CIMD Client",
                    "redirect_uris": ["https://client.example/callback"],
                }
            ).encode()
        )

        def raise_for_status(self):
            return None

    def fetch(*_args, **_kwargs):
        if failure == "timeout":
            raise httpx.ReadTimeout("bounded")
        return MetadataResponse()

    monkeypatch.setattr(authorization_service.httpx, "get", fetch)
    before = session.query(MCPAuthorizationInteraction).count()
    with TestClient(app) as client:
        response = client.get(
            "/oauth/authorize",
            params={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": "https://client.example/callback",
                "code_challenge": "c" * 43,
                "code_challenge_method": "S256",
                "resource": "https://mcp.example.test/",
                "scope": "reality:read",
            },
            follow_redirects=False,
        )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"
    assert expected in response.json()["error_description"]
    assert session.query(MCPAuthorizationInteraction).count() == before


def test_consent_includes_only_ready_sandbox_memberships(
    session, business, scheduled_owner, monkeypatch
):
    sandbox = Tenant(id=uid("ten"), name="Practice", purpose="playground")
    session.add(sandbox)
    session.flush()
    session.add(
        TenantMembership(
            id="tmb_sandbox_oauth",
            tenant_id=sandbox.id,
            user_id=scheduled_owner.id,
            role="owner",
            status="active",
        )
    )
    session.add(
        PlaygroundRun(
            id=uid("pgr"),
            tenant_id=sandbox.id,
            owner_user_id=scheduled_owner.id,
            preset_key="trading",
            preset_version=1,
            lesson_key="order-stock",
            lesson_version=1,
            client_request_key=uid("request"),
            sandbox_kind="practice",
            status="active",
            ready_at=now(),
        )
    )
    session.commit()
    monkeypatch.setenv("MCP_URL", "https://mcp.example.test/")
    monkeypatch.setenv(
        "MCP_OAUTH_CLIENTS",
        json.dumps(
            {
                "client-a": {
                    "client_name": "Client A",
                    "redirect_uris": ["https://client.example/callback"],
                }
            }
        ),
    )
    _overrides(session, scheduled_owner)
    with TestClient(app) as client:
        authorize = client.get(
            "/oauth/authorize",
            params={
                "response_type": "code",
                "client_id": "client-a",
                "redirect_uri": "https://client.example/callback",
                "code_challenge": _challenge("v" * 64),
                "code_challenge_method": "S256",
                "resource": "https://mcp.example.test/",
                "scope": "reality:read",
            },
            follow_redirects=False,
        )
        interaction_id = parse_qs(urlparse(authorize.headers["location"]).query)[
            "interaction"
        ][0]
        companies = client.get(f"/api/oauth/interactions/{interaction_id}").json()[
            "companies"
        ]
    assert {company["id"] for company in companies} == {
        business.tenant.id,
        sandbox.id,
    }


def test_interaction_expiry_denial_same_name_companies_and_account_switch(
    session, business, scheduled_owner, monkeypatch
):
    monkeypatch.setenv("API_URL", "https://api.example.test")
    interaction = create_interaction(
        session,
        client_id="client-a",
        client_metadata={
            "client_name": "Client A",
            "redirect_uris": ["https://client.example/callback"],
        },
        redirect_uri="https://client.example/callback",
        resource="https://mcp.example.test/",
        requested_scopes=["reality:read"],
        code_challenge=_challenge("v" * 64),
        state="opaque",
    )
    same_name = Tenant(id=uid("ten"), name=business.tenant.name)
    session.add(same_name)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("tmb"),
            tenant_id=same_name.id,
            user_id=scheduled_owner.id,
            role="member",
            status="active",
        )
    )
    session.commit()
    _overrides(session, scheduled_owner)
    with TestClient(app) as client:
        view = client.get(f"/api/oauth/interactions/{interaction.id}")
        assert view.status_code == 200
        companies = view.json()["companies"]
        assert [company["name"] for company in companies].count(
            business.tenant.name
        ) == 2
        assert len({company["id"] for company in companies}) == 2

        other = AppUser(
            id=uid("usr"),
            email=f"{uid('mail')}@example.test",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        session.add(other)
        session.commit()
        app.dependency_overrides[auth_module.current_user] = lambda: other
        assert (
            client.get(f"/api/oauth/interactions/{interaction.id}").status_code == 404
        )
        app.dependency_overrides[auth_module.current_user] = lambda: scheduled_owner

        denial = client.post(
            f"/api/oauth/interactions/{interaction.id}/deny",
            json={"confirmed": True},
            follow_redirects=False,
        )
        assert denial.status_code == 303
        assert parse_qs(urlparse(denial.headers["location"]).query)["error"] == [
            "access_denied"
        ]

    expired = create_interaction(
        session,
        client_id="client-a",
        client_metadata={"client_name": "Client A"},
        redirect_uri="https://client.example/callback",
        resource="https://mcp.example.test/",
        requested_scopes=["reality:read"],
        code_challenge=_challenge("v" * 64),
    )
    expired.expires_at = now() - timedelta(seconds=1)
    session.commit()
    _overrides(session, scheduled_owner)
    with TestClient(app) as client:
        response = client.get(f"/api/oauth/interactions/{expired.id}")
    assert response.status_code == 200
    assert response.json()["status"] == "expired"


def _consent_interaction(client, *, scope: str, verifier: str = "v" * 64) -> str:
    """Drive the authorize redirect and return the pending interaction's id."""
    authorize = client.get(
        "/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": "client-a",
            "redirect_uri": "https://client.example/callback",
            "code_challenge": _challenge(verifier),
            "code_challenge_method": "S256",
            "resource": "https://mcp.example.test/",
            "scope": scope,
            "state": "client-state",
        },
        follow_redirects=False,
    )
    assert authorize.status_code == 303
    location = authorize.headers["location"]
    return parse_qs(urlparse(location).query)["interaction"][0]


def _consent_environment(monkeypatch) -> None:
    monkeypatch.setenv("API_URL", "https://api.example.test")
    monkeypatch.setenv("APP_URL", "https://app.example.test")
    monkeypatch.setenv("MCP_URL", "https://mcp.example.test/")
    monkeypatch.setenv(
        "MCP_OAUTH_CLIENTS",
        json.dumps(
            {
                "client-a": {
                    "client_name": "Client A",
                    "redirect_uris": ["https://client.example/callback"],
                }
            }
        ),
    )


@pytest.mark.parametrize(
    "scope",
    [
        "reality:read",
        "reality:read reality:propose",
        "reality:read reality:propose reality:confirm",
    ],
)
def test_approval_accepts_every_eligible_tool_however_large_the_catalog(
    session, business, scheduled_owner, monkeypatch, scope
):
    """Spec 271 FR-001/FR-006/FR-007: the default selection must stay submittable.

    The expected size is read from the catalog, so this fails the moment any layer
    reintroduces a bound the catalog has outgrown.
    """
    from reality.db.mcp_authorization import MCPClientGrant

    _consent_environment(monkeypatch)
    _overrides(session, scheduled_owner)

    with TestClient(app) as client:
        interaction_id = _consent_interaction(client, scope=scope)
        body = client.get(f"/api/oauth/interactions/{interaction_id}").json()
        selected = body["selected_tools"]
        approval = client.post(
            f"/api/oauth/interactions/{interaction_id}/approve",
            json={
                "company_id": business.tenant.id,
                "allowed_tools": selected,
                "confirmed": True,
            },
            follow_redirects=False,
        )

    assert approval.status_code == 303, approval.text
    assert selected == [tool["name"] for tool in body["eligible_tools"]]
    grant = session.scalars(
        select(MCPClientGrant).where(MCPClientGrant.tenant_id == business.tenant.id)
    ).one()
    assert sorted(grant.allowed_tools) == sorted(selected)
    if scope.count("reality:") == 3:
        assert len(selected) == len(MCP_TOOL_NAMES)


def test_a_refused_approval_names_its_cause_and_keeps_the_interaction_pending(
    session, business, scheduled_owner, monkeypatch
):
    """Spec 271 FR-004/FR-005: an unknown name answered 500 before this."""
    _consent_environment(monkeypatch)
    _overrides(session, scheduled_owner)

    with TestClient(app) as client:
        interaction_id = _consent_interaction(client, scope="reality:read")
        known = client.get(f"/api/oauth/interactions/{interaction_id}").json()[
            "selected_tools"
        ][0]

        unknown = client.post(
            f"/api/oauth/interactions/{interaction_id}/approve",
            json={
                "company_id": business.tenant.id,
                "allowed_tools": ["no_such_tool"],
                "confirmed": True,
            },
            follow_redirects=False,
        )
        empty = client.post(
            f"/api/oauth/interactions/{interaction_id}/approve",
            json={
                "company_id": business.tenant.id,
                "allowed_tools": [],
                "confirmed": True,
            },
            follow_redirects=False,
        )
        out_of_scope = client.post(
            f"/api/oauth/interactions/{interaction_id}/approve",
            json={
                "company_id": business.tenant.id,
                "allowed_tools": ["order_create_propose"],
                "confirmed": True,
            },
            follow_redirects=False,
        )
        still_pending = session.get(MCPAuthorizationInteraction, interaction_id).status
        # Positive control: the same interaction still accepts a valid selection.
        accepted = client.post(
            f"/api/oauth/interactions/{interaction_id}/approve",
            json={
                "company_id": business.tenant.id,
                "allowed_tools": [known],
                "confirmed": True,
            },
            follow_redirects=False,
        )

    assert unknown.status_code == 400
    assert "no_such_tool" in unknown.json()["detail"]
    # The browser only shows `detail` when it is a sentence, not a validation list.
    assert isinstance(unknown.json()["detail"], str)
    assert empty.status_code == 400
    assert "at least one" in empty.json()["detail"]
    assert out_of_scope.status_code == 409
    assert isinstance(out_of_scope.json()["detail"], str)
    assert "scopes" in out_of_scope.json()["detail"]
    assert still_pending == "pending"
    assert accepted.status_code == 303


def test_approval_normalizes_before_it_judges(
    session, business, scheduled_owner, monkeypatch
):
    """Spec 271 FR-002: duplicates and legacy aliases must not be counted as extra."""
    from reality.db.mcp_authorization import MCPClientGrant
    from reality.mcp.catalog import LEGACY_TOOL_NAMES

    _consent_environment(monkeypatch)
    _overrides(session, scheduled_owner)

    with TestClient(app) as client:
        interaction_id = _consent_interaction(client, scope="reality:read")
        eligible = client.get(f"/api/oauth/interactions/{interaction_id}").json()[
            "selected_tools"
        ]
        alias = next(
            (old for old, new in LEGACY_TOOL_NAMES.items() if new in eligible), None
        )
        submitted = [eligible[0], eligible[0], *([alias] if alias else [])]
        approval = client.post(
            f"/api/oauth/interactions/{interaction_id}/approve",
            json={
                "company_id": business.tenant.id,
                "allowed_tools": submitted,
                "confirmed": True,
            },
            follow_redirects=False,
        )

    assert approval.status_code == 303, approval.text
    grant = session.scalars(
        select(MCPClientGrant).where(MCPClientGrant.tenant_id == business.tenant.id)
    ).one()
    expected = {eligible[0]} | ({LEGACY_TOOL_NAMES[alias]} if alias else set())
    assert set(grant.allowed_tools) == expected
    assert len(grant.allowed_tools) == len(expected)


def test_a_wildcard_is_still_refused_for_an_interactive_grant(
    session, business, scheduled_owner, monkeypatch
):
    """Deleting the length bound must not read as relaxing what a grant may hold."""
    _consent_environment(monkeypatch)
    _overrides(session, scheduled_owner)

    with TestClient(app) as client:
        interaction_id = _consent_interaction(client, scope="reality:read")
        known = client.get(f"/api/oauth/interactions/{interaction_id}").json()[
            "selected_tools"
        ][0]
        wildcard = client.post(
            f"/api/oauth/interactions/{interaction_id}/approve",
            json={
                "company_id": business.tenant.id,
                "allowed_tools": ["*"],
                "confirmed": True,
            },
            follow_redirects=False,
        )
        # Positive control: the explicit equivalent is accepted.
        explicit = client.post(
            f"/api/oauth/interactions/{interaction_id}/approve",
            json={
                "company_id": business.tenant.id,
                "allowed_tools": [known],
                "confirmed": True,
            },
            follow_redirects=False,
        )

    assert wildcard.status_code == 409
    assert explicit.status_code == 303
