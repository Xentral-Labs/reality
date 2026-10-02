"""Spec 307 FR-003: stock counts through the review, MCP, Web and CLI."""

import json

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, StockCount
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _stock(session, business, quantity):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )


def _counts(session, business):
    session.expire_all()
    return session.scalar(
        select(func.count())
        .select_from(StockCount)
        .where(StockCount.tenant_id == business.tenant.id)
    )


def _client(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    return TestClient(web_module.app)


def _schema(name):
    return next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == name
    )


def test_the_mcp_schema_is_strict():
    schema = _schema("stock_count_propose")
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"location_id", "lines"}
    line = schema["properties"]["lines"]["items"]
    assert line["additionalProperties"] is False
    assert set(line["required"]) == {"item_id", "counted_quantity"}


def test_an_agent_proposes_a_count_and_a_person_confirms(session, business):
    tenant = business.tenant.id
    _stock(session, business, "10")

    proposed = MCP_TOOL_REGISTRY["stock_count_propose"].handler(
        session,
        tenant,
        {
            "location_id": business.location.id,
            "note": "Shelf A",
            "lines": [{"item_id": business.item.id, "counted_quantity": "8"}],
        },
    )
    (line,) = proposed["preview"]["stock_count"]["lines"]
    assert (line["book"], line["difference"]) == ("10", "-2")
    assert _counts(session, business) == 0

    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )
    # The same confirmation again records nothing twice.
    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )

    assert _counts(session, business) == 1
    assert core.stock_at(session, tenant, business.item.id) == 8
    (row,) = MCP_TOOL_REGISTRY["stock_counts"].handler(
        session, tenant, {"location_id": business.location.id}
    )
    detail = MCP_TOOL_REGISTRY["stock_count_detail"].handler(
        session, tenant, {"stock_count_id": row["id"]}
    )
    assert [line["difference"] for line in detail["lines"]] == ["-2"]


def test_the_web_prepares_confirms_and_reads(session, business, monkeypatch):
    _stock(session, business, "10")
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{business.tenant.id}"

    prepared = client.post(
        f"{prefix}/stock-counts/proposals",
        json={
            "location_id": business.location.id,
            "lines": [{"item_id": business.item.id, "counted_quantity": "12"}],
        },
    )
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert body["preview"]["stock_count"]["lines"][0]["difference"] == "2"
    confirmed = client.post(
        f"{prefix}/change-proposals/{body['id']}/approve", json={"confirmed": True}
    )
    assert confirmed.status_code == 200, confirmed.text

    (row,) = client.get(
        f"{prefix}/stock-counts", params={"location_id": business.location.id}
    ).json()["rows"]
    detail = client.get(f"{prefix}/stock-counts/{row['id']}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["lines"][0]["counted"] == "12"
    refused = client.post(
        f"{prefix}/stock-counts/proposals",
        json={
            "location_id": business.location.id,
            "lines": [{"item_id": "itm_x", "counted_quantity": "1"}],
        },
    )
    assert refused.status_code in {400, 409, 422}, refused.text
    assert "stock_count_item_not_found" in refused.text


def test_another_company_cannot_count_or_read(session, business, monkeypatch):
    _stock(session, business, "10")
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)
    # Positive control: the company's own list is readable.
    own = client.get(f"/api/tenants/{business.tenant.id}/stock-counts")
    assert own.status_code == 200, own.text

    foreign = client.post(
        f"/api/tenants/{other.id}/stock-counts/proposals",
        json={
            "location_id": business.location.id,
            "lines": [{"item_id": business.item.id, "counted_quantity": "1"}],
        },
    )
    assert foreign.status_code in {400, 404, 422}, foreign.text
    assert client.get(f"/api/tenants/{other.id}/stock-counts").json()["rows"] == []
    assert core.stock_at(session, business.tenant.id, business.item.id) == 10


def test_the_cli_counts_after_asking(session, business, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    tenant = business.tenant.id
    _stock(session, business, "10")
    runner = CliRunner()
    command = [
        "stock-count",
        "record",
        business.location.id,
        "--line",
        f"{business.item.id}=9",
        "--tenant",
        tenant,
    ]

    declined = runner.invoke(cli_module.app, command, input="n\n")
    assert declined.exit_code == 0, declined.output
    assert _counts(session, business) == 0
    assert (
        session.scalar(
            select(ChangeProposal.status).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.type == "tool:stock_count",
            )
        )
        == "rejected"
    )

    recorded = runner.invoke(cli_module.app, [*command, "--yes"])
    assert recorded.exit_code == 0, recorded.output
    assert core.stock_at(session, tenant, business.item.id) == 9
    listed = runner.invoke(cli_module.app, ["stock-count", "list", "--tenant", tenant])
    assert listed.exit_code == 0, listed.output
    (row,) = json.loads(listed.output)
    shown = runner.invoke(
        cli_module.app, ["stock-count", "show", row["id"], "--tenant", tenant]
    )
    assert json.loads(shown.output)["lines"][0]["difference"] == "-1"
