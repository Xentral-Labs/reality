"""Spec 305 FR-004: serving backorders and available-to-promise behind MCP, Web and CLI."""

import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal
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


def _promise(session, business, quantity, due):
    return core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        due,
    )


def _reserved(session, business, promise):
    session.expire_all()
    return core.commitment_terms(session, business.tenant.id, [promise.id])[
        promise.id
    ].reserved


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


def test_the_mcp_schemas_are_strict():
    serve = _schema("backorders_serve_propose")
    assert serve["additionalProperties"] is False
    assert set(serve["required"]) == {"item_id", "location_id"}
    line = serve["properties"]["lines"]["items"]
    assert line["additionalProperties"] is False
    assert set(line["required"]) == {"commitment_id", "quantity"}
    assert _schema("available_to_promise")["required"] == ["item_id"]


def test_an_agent_proposes_and_a_person_confirms(session, business):
    tenant = business.tenant.id
    first = _promise(session, business, "3", "2026-10-15")
    _promise(session, business, "3", "2026-10-16")
    _stock(session, business, "4")

    proposed = MCP_TOOL_REGISTRY["backorders_serve_propose"].handler(
        session,
        tenant,
        {"item_id": business.item.id, "location_id": business.location.id},
    )
    lines = proposed["preview"]["backorder_serving"]["lines"]
    assert [line["quantity"] for line in lines] == ["3", "1"]
    assert _reserved(session, business, first) == 0

    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )
    assert _reserved(session, business, first) == 3

    answer = MCP_TOOL_REGISTRY["available_to_promise"].handler(
        session, tenant, {"item_id": business.item.id}
    )
    assert answer["now"]["reserved"] == "4"


def test_the_web_prepares_confirms_and_answers(session, business, monkeypatch):
    first = _promise(session, business, "3", "2026-10-15")
    second = _promise(session, business, "3", "2026-10-16")
    _stock(session, business, "4")
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{business.tenant.id}"

    prepared = client.post(
        f"{prefix}/backorders/proposals",
        json={
            "item_id": business.item.id,
            "location_id": business.location.id,
            "lines": [
                {"commitment_id": first.id, "quantity": "1"},
                {"commitment_id": second.id, "quantity": "3"},
            ],
        },
    )
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert body["preview"]["backorder_serving"]["reserving"] == "4"
    confirmed = client.post(
        f"{prefix}/change-proposals/{body['id']}/approve", json={"confirmed": True}
    )
    assert confirmed.status_code == 200, confirmed.text
    assert (
        _reserved(session, business, first),
        _reserved(session, business, second),
    ) == (1, 3)

    answer = client.get(f"{prefix}/items/{business.item.id}/available-to-promise")
    assert answer.status_code == 200, answer.text
    assert answer.json()["now"]["free"] == "-2"

    refused = client.post(
        f"{prefix}/backorders/proposals",
        json={"item_id": business.item.id, "location_id": business.location.id},
    )
    assert refused.status_code in {400, 409, 422}, refused.text
    assert "backorder_serving_nothing_to_serve" in refused.text


def test_another_company_cannot_serve_or_read(session, business, monkeypatch):
    promise = _promise(session, business, "3", "2026-10-15")
    _stock(session, business, "3")
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)

    foreign = client.post(
        f"/api/tenants/{other.id}/backorders/proposals",
        json={"item_id": business.item.id, "location_id": business.location.id},
    )
    assert foreign.status_code in {400, 404, 422}, foreign.text
    read = client.get(
        f"/api/tenants/{other.id}/items/{business.item.id}/available-to-promise"
    )
    assert read.status_code == 404, read.text
    assert _reserved(session, business, promise) == 0


def test_the_cli_serves_after_asking(session, business, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    tenant = business.tenant.id
    promise = _promise(session, business, "3", "2026-10-15")
    _stock(session, business, "3")
    runner = CliRunner()
    command = [
        "backorders",
        "serve",
        business.item.id,
        business.location.id,
        "--line",
        f"{promise.id}=2",
        "--tenant",
        tenant,
    ]

    declined = runner.invoke(cli_module.app, command, input="n\n")
    assert declined.exit_code == 0, declined.output
    assert _reserved(session, business, promise) == 0
    assert (
        session.scalar(
            select(ChangeProposal.status).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.type == "tool:backorders_serve",
            )
        )
        == "rejected"
    )

    served = runner.invoke(cli_module.app, [*command, "--yes"])
    assert served.exit_code == 0, served.output
    assert _reserved(session, business, promise) == 2

    promised = runner.invoke(
        cli_module.app, ["backorders", "promise", business.item.id, "--tenant", tenant]
    )
    assert promised.exit_code == 0, promised.output
    assert json.loads(promised.output)["now"]["reserved"] == "2"
