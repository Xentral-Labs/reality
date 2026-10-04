"""Spec 296 FR-005: one reviewed item assignment behind Web, MCP/Chat and CLI."""

import json

from fastapi.testclient import TestClient
from intake_review_support import accept_import_job
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, DocumentLine
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _order_with_unknown_item(session, business):
    _, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        {
            "id": 9101,
            "name": "#9101",
            "currency": "EUR",
            "total_price": "50.00",
            "created_at": "2026-09-01T10:00:00Z",
            "line_items": [
                {"id": 91, "sku": "BIKE-LIGHT", "quantity": 1, "price": "10.00"},
                {"id": 92, "sku": "HELMET-M", "quantity": 4, "price": "10.00"},
            ],
        },
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    accept_import_job(session, business.tenant.id, job.id)
    line = session.scalars(
        select(DocumentLine).where(
            DocumentLine.tenant_id == business.tenant.id,
            DocumentLine.sku == "HELMET-M",
        )
    ).one()
    item = core.create_item(session, business.tenant.id, "HELMET-M-01", "Helmet M")
    return line, item


def _assigned(session, line):
    session.expire_all()
    return session.get(DocumentLine, (line.tenant_id, line.id)).item_id


def test_the_mcp_proposal_schema_is_strict():
    schema = next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == "order_line_item_assign_propose"
    )
    assert schema["additionalProperties"] is False
    # Spec 308 adds the optional remember-for-customer flag.
    assert set(schema["properties"]) == {
        "document_line_id",
        "item_id",
        "remember_for_customer",
    }
    assert set(schema["required"]) == {"document_line_id", "item_id"}


def test_an_agent_proposes_and_a_person_confirms_the_assignment(session, business):
    line, item = _order_with_unknown_item(session, business)

    proposed = MCP_TOOL_REGISTRY["order_line_item_assign_propose"].handler(
        session,
        business.tenant.id,
        {"document_line_id": line.id, "item_id": item.id},
    )
    # Proposing assigns nothing.
    assert _assigned(session, line) is None
    proposal = session.get(
        ChangeProposal, (business.tenant.id, proposed["proposal_id"])
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )

    assert _assigned(session, line) == item.id


def test_the_web_prepares_and_confirms_an_assignment(session, business, monkeypatch):
    line, item = _order_with_unknown_item(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)
    prefix = f"/api/tenants/{business.tenant.id}"

    prepared = client.post(
        f"{prefix}/delivery-actions/prepare",
        json={
            "tool": "order_line_item_assign",
            "request_id": "web-assign",
            "arguments": {"document_line_id": line.id, "item_id": item.id},
        },
    )
    assert prepared.status_code == 200, prepared.text
    preview = prepared.json()
    assert preview["review"]["effect"]["money_moves"] is False
    assert _assigned(session, line) is None

    confirmed = client.post(
        f"{prefix}/change-proposals/{preview['id']}/approve",
        json={"confirmed": True, "review_token": preview["review"]["token"]},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert _assigned(session, line) == item.id


def test_the_web_refuses_another_companys_line(session, business, monkeypatch):
    line, item = _order_with_unknown_item(session, business)
    other = core.create_tenant(session, "Other GmbH")
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)

    foreign = client.post(
        f"/api/tenants/{other.id}/delivery-actions/prepare",
        json={
            "tool": "order_line_item_assign",
            "request_id": "foreign-assign",
            "arguments": {"document_line_id": line.id, "item_id": item.id},
        },
    )
    assert foreign.status_code == 404, foreign.text
    assert _assigned(session, line) is None


def test_the_cli_proposes_and_confirms_an_assignment(session, business, monkeypatch):
    line, item = _order_with_unknown_item(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    runner = CliRunner()

    proposed = runner.invoke(
        cli_module.app,
        [
            "order-line-item-assign-propose",
            json.dumps({"document_line_id": line.id, "item_id": item.id}),
            "cli-assign",
            "--tenant-id",
            business.tenant.id,
        ],
    )
    assert proposed.exit_code == 0, proposed.output
    detail = json.loads(proposed.output)
    assert _assigned(session, line) is None

    confirmed = runner.invoke(
        cli_module.app,
        [
            "order-line-item-assign-confirm",
            detail["id"],
            detail["review"]["token"],
            "--yes",
            "--tenant-id",
            business.tenant.id,
        ],
    )
    assert confirmed.exit_code == 0, confirmed.output
    assert json.loads(confirmed.output)["verification"] == "verified"
    assert _assigned(session, line) == item.id


def test_the_cli_help_lists_the_assignment_commands():
    result = CliRunner().invoke(cli_module.app, ["--help"])
    for command in ("order-line-item-assign-propose", "order-line-item-assign-confirm"):
        assert command in result.output
