"""Spec 271 FR-003: both grant paths accept and refuse the same permission lists.

A manual company token and an interactive client grant name the same permissions.
They validated them differently: one carried a 200-name ceiling the other did not,
one answered an unknown name with a sentence and the other with a server error, and
an empty selection was a validation error on one side and a sentence on the other.
This holds the two against each other on the same inputs.
"""

from __future__ import annotations

import base64
import hashlib
import json
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from reality.db.core import AppUser, TenantMembership, now, uid
from reality.mcp.catalog import MCP_TOOL_NAMES
from reality.web import api as api_module
from reality.web import app as web_module
from reality.web import auth as auth_module

PASSWORD = "a-long-account-password"


@pytest.fixture
def owner_browser(session, business, monkeypatch):
    """A signed-in company owner, the authority both grant paths require."""
    user = AppUser(
        id=uid("usr"),
        email="owner@example.com",
        password_hash=auth_module.password_hasher.hash(PASSWORD),
        display_name="Olive Owner",
        status="active",
        email_verified_at=now(),
    )
    session.add(user)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("mem"),
            tenant_id=business.tenant.id,
            user_id=user.id,
            role="owner",
            status="active",
        )
    )
    session.commit()

    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
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
    client = TestClient(web_module.app)
    login = client.post(
        "/api/auth/login", json={"email": user.email, "password": PASSWORD}
    )
    assert login.status_code == 200
    return client


def _interactive(client, tenant_id: str, tools: list[str]):
    """Run one authorization to consent and submit `tools`."""
    verifier = "v" * 64
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    authorize = client.get(
        "/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": "client-a",
            "redirect_uri": "https://client.example/callback",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "resource": "https://mcp.example.test/",
            "scope": "reality:read reality:propose reality:confirm",
            "state": "client-state",
        },
        follow_redirects=False,
    )
    assert authorize.status_code == 303
    interaction = parse_qs(urlparse(authorize.headers["location"]).query)[
        "interaction"
    ][0]
    return client.post(
        f"/api/oauth/interactions/{interaction}/approve",
        json={
            "company_id": tenant_id,
            "allowed_tools": tools,
            "confirmed": True,
        },
        follow_redirects=False,
    )


def _manual(client, tenant_id: str, tools: list[str], name: str):
    return client.post(
        f"/api/tenants/{tenant_id}/settings/mcp/tokens",
        json={"name": name, "allowed_tools": tools},
    )


def _accepted(response) -> bool:
    return response.status_code in {201, 303}


def _detail(response) -> str:
    if _accepted(response):
        return ""
    body = response.json()
    detail = body.get("detail")
    return detail if isinstance(detail, str) else json.dumps(detail)


def test_both_paths_accept_the_complete_catalog(owner_browser, business):
    """Neither path may cap what the catalog itself allows."""
    everything = sorted(MCP_TOOL_NAMES)

    interactive = _interactive(owner_browser, business.tenant.id, everything)
    manual = _manual(owner_browser, business.tenant.id, everything, "Full access")

    assert _accepted(interactive), interactive.text
    assert _accepted(manual), manual.text
    assert sorted(manual.json()["allowed_tools"]) == everything


def test_both_paths_accept_a_duplicate_laden_list(owner_browser, business):
    """Normalization happens before judgement, so a repeat is not an extra name."""
    first, second = sorted(MCP_TOOL_NAMES)[:2]
    submitted = [first, second, first, second, first]

    interactive = _interactive(owner_browser, business.tenant.id, submitted)
    manual = _manual(owner_browser, business.tenant.id, submitted, "Duplicates")

    assert _accepted(interactive), interactive.text
    assert _accepted(manual), manual.text
    assert sorted(manual.json()["allowed_tools"]) == [first, second]


def test_both_paths_refuse_an_unknown_name_with_the_same_sentence(
    owner_browser, business
):
    interactive = _interactive(owner_browser, business.tenant.id, ["no_such_tool"])
    manual = _manual(owner_browser, business.tenant.id, ["no_such_tool"], "Unknown")

    assert not _accepted(interactive)
    assert not _accepted(manual)
    assert _detail(interactive) == _detail(manual)
    assert "no_such_tool" in _detail(interactive)


def test_both_paths_refuse_an_empty_selection_with_the_same_sentence(
    owner_browser, business
):
    interactive = _interactive(owner_browser, business.tenant.id, [])
    manual = _manual(owner_browser, business.tenant.id, [], "Empty")

    assert not _accepted(interactive)
    assert not _accepted(manual)
    assert _detail(interactive) == _detail(manual)
    assert "at least one" in _detail(interactive)


def test_the_wildcard_stays_the_one_intended_difference(owner_browser, business):
    """A manual token may hold `*`; an interactive grant must name its tools.

    This difference is deliberate — a grant records what a third-party client was
    given — so the parity this feature restores is about validation, not about what
    each credential may contain.
    """
    interactive = _interactive(owner_browser, business.tenant.id, ["*"])
    manual = _manual(owner_browser, business.tenant.id, ["*"], "Wildcard")

    assert not _accepted(interactive)
    assert _accepted(manual)
    assert manual.json()["allowed_tools"] == ["*"]
