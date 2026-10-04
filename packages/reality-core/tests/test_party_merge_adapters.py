"""Spec 339 FR-005: merges behind MCP/Chat, Web and CLI, through the shared review."""

import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import PartyMerge
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _schema(name):
    return next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == name
    )


def _merges(session, tenant):
    session.expire_all()
    return list(
        session.scalars(select(PartyMerge).where(PartyMerge.tenant_id == tenant))
    )


def _client(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    return TestClient(web_module.app)


def test_the_mcp_schemas_are_strict():
    propose = _schema("party_merge_propose")
    assert propose["additionalProperties"] is False
    assert set(propose["required"]) == {
        "duplicate_party_id",
        "surviving_party_id",
        "reason",
    }
    assert _schema("party_merges")["additionalProperties"] is False


def test_an_agent_proposes_and_a_person_confirms(session, business):
    tenant = business.tenant.id
    duplicate = reviewed_create_party(session, tenant, "Müller (Gast)", "customer")

    proposed = MCP_TOOL_REGISTRY["party_merge_propose"].handler(
        session,
        tenant,
        {
            "duplicate_party_id": duplicate.id,
            "surviving_party_id": business.customer.id,
            "reason": "Guest checkout of the same customer",
        },
    )
    review = proposed["preview"]["party_merge"]
    assert (review["duplicate"]["name"], review["survivor"]["name"]) == (
        duplicate.name,
        business.customer.name,
    )
    # Nothing is merged until a person confirms.
    assert _merges(session, tenant) == []
    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )
    (read,) = MCP_TOOL_REGISTRY["party_merges"].handler(session, tenant, {})
    assert read["survivor"] == business.customer.name


def test_the_web_reads_prepares_and_confirms(session, business, monkeypatch):
    tenant = business.tenant.id
    duplicate = reviewed_create_party(session, tenant, "Müller GmbH 2", "customer")
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{tenant}"

    refused = client.post(
        f"{prefix}/parties/merge-proposals",
        json={
            "duplicate_party_id": duplicate.id,
            "surviving_party_id": duplicate.id,
            "reason": "Same",
        },
    )
    assert refused.status_code in {400, 409, 422}, refused.text
    assert "party_merge_same_party" in refused.text
    prepared = client.post(
        f"{prefix}/parties/merge-proposals",
        json={
            "duplicate_party_id": duplicate.id,
            "surviving_party_id": business.customer.id,
            "reason": "Created twice",
        },
    )
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert body["preview"]["party_merge"]["survivor"]["id"] == business.customer.id
    assert client.get(f"{prefix}/party-merges").json()["rows"] == []
    confirmed = client.post(
        f"{prefix}/change-proposals/{body['id']}/approve", json={"confirmed": True}
    )
    assert confirmed.status_code == 200, confirmed.text
    (row,) = client.get(
        f"{prefix}/party-merges", params={"party_id": business.customer.id}
    ).json()["rows"]
    assert row["duplicate_party_id"] == duplicate.id
    inspector = client.get(f"{prefix}/inspector/party/{business.customer.id}")
    assert inspector.status_code == 200, inspector.text
    titles = [section["title"] for section in inspector.json()["sections"]]
    assert "Merges" in titles


def test_another_company_cannot_read_or_merge(session, business, monkeypatch):
    duplicate = reviewed_create_party(session, business.tenant.id, "Dublette", "customer")
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)

    assert client.get(f"/api/tenants/{other.id}/party-merges").json()["rows"] == []
    foreign = client.post(
        f"/api/tenants/{other.id}/parties/merge-proposals",
        json={
            "duplicate_party_id": duplicate.id,
            "surviving_party_id": business.customer.id,
            "reason": "Same",
        },
    )
    assert foreign.status_code == 404, foreign.text
    assert _merges(session, business.tenant.id) == []


def test_the_cli_merges_lists_and_declines(session, business, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    tenant = business.tenant.id
    duplicate = reviewed_create_party(session, tenant, "Dublette", "customer")
    runner = CliRunner()
    arguments = [
        "party",
        "merge",
        duplicate.id,
        business.customer.id,
        "--reason",
        "Created twice",
        "--tenant",
        tenant,
    ]

    declined = runner.invoke(cli_module.app, arguments, input="n\n")
    assert declined.exit_code == 0, declined.output
    assert _merges(session, tenant) == []
    merged = runner.invoke(cli_module.app, [*arguments, "--yes"])
    assert merged.exit_code == 0, merged.output
    assert len(_merges(session, tenant)) == 1

    shown = runner.invoke(cli_module.app, ["party", "merges", "--tenant", tenant])
    assert shown.exit_code == 0, shown.output
    assert json.loads(shown.output)[0]["duplicate_party_id"] == duplicate.id


from intake_review_support import reviewed_create_party
