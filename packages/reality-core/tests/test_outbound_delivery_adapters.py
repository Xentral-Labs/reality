"""Spec 334 FR-006: planned deliveries through the review, MCP, Web and CLI."""

import json

from fastapi.testclient import TestClient
from intake_review_support import reviewed_reserve
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, OutboundDelivery
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _promise(session, business, quantity="4"):
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    promise = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        None,
    )
    reviewed_reserve(session, tenant, promise.id)
    return promise


def _deliveries(session, business):
    session.expire_all()
    return session.scalar(
        select(func.count())
        .select_from(OutboundDelivery)
        .where(OutboundDelivery.tenant_id == business.tenant.id)
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


def test_the_mcp_schemas_are_strict():
    plan = _schema("outbound_delivery_plan_propose")
    assert plan["additionalProperties"] is False
    assert set(plan["required"]) == {"customer_id", "lines"}
    assert plan["properties"]["address"]["additionalProperties"] is False
    assert set(plan["properties"]["slot"]["required"]) == {"from", "until"}
    pick = _schema("outbound_delivery_pick_propose")
    assert set(pick["properties"]["lines"]["items"]["required"]) == {
        "commitment_id",
        "quantity",
    }
    put_back = _schema("outbound_delivery_put_back_propose")
    assert "to_location_id" in put_back["properties"]["lines"]["items"]["required"]


def test_an_agent_plans_picks_and_dispatches(session, business):
    tenant = business.tenant.id
    promise = _promise(session, business)
    staging = reviewed_create_location(session, tenant, "Packing zone")

    proposed = MCP_TOOL_REGISTRY["outbound_delivery_plan_propose"].handler(
        session,
        tenant,
        {
            "customer_id": business.customer.id,
            "address": {"street": "Hafenstr. 1", "city": "Hamburg"},
            "staging_location_id": staging.id,
            "lines": [{"commitment_id": promise.id, "quantity": "4"}],
        },
    )
    assert proposed["preview"]["outbound_delivery"]["lines"][0]["may_plan"] == "4"
    assert _deliveries(session, business) == 0
    approve_and_execute_proposal(session, tenant, proposed["proposal_id"], confirmed=True)
    # The same confirmation again plans nothing twice.
    approve_and_execute_proposal(session, tenant, proposed["proposal_id"], confirmed=True)
    assert _deliveries(session, business) == 1

    (row,) = MCP_TOOL_REGISTRY["outbound_deliveries"].handler(session, tenant, {})
    picked = MCP_TOOL_REGISTRY["outbound_delivery_pick_propose"].handler(
        session,
        tenant,
        {
            "outbound_delivery_id": row["id"],
            "lines": [{"commitment_id": promise.id, "quantity": "4"}],
        },
    )
    approve_and_execute_proposal(session, tenant, picked["proposal_id"], confirmed=True)
    detail = MCP_TOOL_REGISTRY["outbound_delivery_detail"].handler(
        session, tenant, {"outbound_delivery_id": row["id"]}
    )
    assert detail["state"] == "picked"

    from reality.mcp.server import _reject_unknown_fields

    definition = MCP_TOOL_REGISTRY["shipment_dispatch_propose"]
    _reject_unknown_fields(definition.input_schema, detail["dispatch"])
    dispatched = definition.handler(session, tenant, detail["dispatch"])
    assert dispatched["proposal_id"]


def test_the_web_prepares_confirms_and_reads(session, business, monkeypatch):
    tenant = business.tenant.id
    promise = _promise(session, business)
    staging = reviewed_create_location(session, tenant, "Packing zone")
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{tenant}"

    prepared = client.post(
        f"{prefix}/outbound-deliveries/proposals",
        json={
            "customer_id": business.customer.id,
            "slot": {
                "from": "2026-10-08T08:00:00+00:00",
                "until": "2026-10-08T10:00:00+00:00",
            },
            "staging_location_id": staging.id,
            "lines": [{"commitment_id": promise.id, "quantity": "4"}],
        },
    )
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert body["preview"]["outbound_delivery"]["slot"]["until"].startswith("2026-10-08T10")
    confirmed = client.post(
        f"{prefix}/change-proposals/{body['id']}/approve", json={"confirmed": True}
    )
    assert confirmed.status_code == 200, confirmed.text

    (row,) = client.get(f"{prefix}/outbound-deliveries").json()["rows"]
    revised = client.post(
        f"{prefix}/outbound-deliveries/{row['id']}/revisions",
        json={"address": {"city": "Bremen"}},
    )
    assert revised.status_code == 200, revised.text
    client.post(
        f"{prefix}/change-proposals/{revised.json()['id']}/approve",
        json={"confirmed": True},
    )
    picked = client.post(
        f"{prefix}/outbound-deliveries/{row['id']}/picks",
        json={"lines": [{"commitment_id": promise.id, "quantity": "4"}]},
    )
    assert picked.status_code == 200, picked.text
    client.post(
        f"{prefix}/change-proposals/{picked.json()['id']}/approve",
        json={"confirmed": True},
    )
    detail = client.get(f"{prefix}/outbound-deliveries/{row['id']}").json()
    assert (detail["state"], detail["address"]) == ("picked", {"city": "Bremen"})
    assert len(detail["statements"]) == 2
    refused = client.post(
        f"{prefix}/outbound-deliveries/{row['id']}/picks",
        json={"lines": [{"commitment_id": promise.id, "quantity": "1"}]},
    )
    assert refused.status_code in {400, 409, 422}, refused.text
    assert "outbound_delivery_pick_beyond_planned" in refused.text
    core.cancel_commitment(session, tenant, promise.id, reason="Customer cancelled")
    put_back = client.post(
        f"{prefix}/outbound-deliveries/{row['id']}/put-backs",
        json={
            "lines": [
                {
                    "commitment_id": promise.id,
                    "quantity": "4",
                    "to_location_id": business.location.id,
                }
            ]
        },
    )
    assert put_back.status_code == 200, put_back.text
    client.post(
        f"{prefix}/change-proposals/{put_back.json()['id']}/approve",
        json={"confirmed": True},
    )
    session.expire_all()
    assert core.stock_at(session, tenant, business.item.id, staging.id) == 0


def test_another_company_cannot_plan_or_read(session, business, monkeypatch):
    promise = _promise(session, business)
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)
    # Positive control: the company's own list is readable.
    own = client.get(f"/api/tenants/{business.tenant.id}/outbound-deliveries")
    assert own.status_code == 200, own.text

    foreign = client.post(
        f"/api/tenants/{other.id}/outbound-deliveries/proposals",
        json={
            "customer_id": business.customer.id,
            "lines": [{"commitment_id": promise.id, "quantity": "1"}],
        },
    )
    assert foreign.status_code in {400, 404, 422}, foreign.text
    assert (
        client.get(f"/api/tenants/{other.id}/outbound-deliveries").json()["rows"] == []
    )
    assert _deliveries(session, business) == 0


def test_the_cli_plans_after_asking(session, business, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    tenant = business.tenant.id
    promise = _promise(session, business)
    runner = CliRunner()
    command = [
        "outbound-delivery",
        "plan",
        business.customer.id,
        "--line",
        f"{promise.id}=3",
        "--address",
        '{"city": "Hamburg"}',
        "--tenant",
        tenant,
    ]

    declined = runner.invoke(cli_module.app, command, input="n\n")
    assert declined.exit_code == 0, declined.output
    assert _deliveries(session, business) == 0
    assert (
        session.scalar(
            select(ChangeProposal.status).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.type == "tool:outbound_delivery_plan",
            )
        )
        == "rejected"
    )

    planned = runner.invoke(cli_module.app, [*command, "--yes"])
    assert planned.exit_code == 0, planned.output
    assert _deliveries(session, business) == 1
    listed = runner.invoke(
        cli_module.app, ["outbound-delivery", "list", "--tenant", tenant]
    )
    (row,) = json.loads(listed.output)
    shown = runner.invoke(
        cli_module.app, ["outbound-delivery", "show", row["id"], "--tenant", tenant]
    )
    assert json.loads(shown.output)["lines"][0]["planned"] == "3"


from intake_review_support import reviewed_create_location
