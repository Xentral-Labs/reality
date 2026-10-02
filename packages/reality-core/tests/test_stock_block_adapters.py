"""Spec 304 FR-001/FR-004, spec 316 FR-006: blocked stock behind every adapter."""

import json
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, StockBlock
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.stock_blocks import block_stock, stock_blocks
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
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


def _blocks(session, business, status="active"):
    session.expire_all()
    return [
        (Decimal(row["open_quantity"]), row["reason_code"], row["status"])
        for row in reversed(stock_blocks(session, business.tenant.id, status=status))
    ]


def _schema(name):
    return next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == name
    )


def _client(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    return TestClient(web_module.app)


def test_the_mcp_schemas_are_strict():
    block = _schema("stock_block_propose")
    assert block["additionalProperties"] is False
    assert block["properties"]["reason_code"]["enum"] == [
        "quality",
        "damage",
        "expiry",
        "inspection",
    ]
    for name in ("stock_block_release_propose", "stock_block_scrap_propose"):
        schema = _schema(name)
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == {"block_id", "reason"}
    assert "blocked_quantity" in _schema("movement_create_propose")["properties"]


def test_a_reviewed_receipt_blocks_the_damaged_part(session, business):
    tenant = business.tenant.id
    proposal = prepare_delivery_action(
        session,
        tenant,
        "movement_create",
        {
            "movement_type": "receipt",
            "item_id": business.item.id,
            "quantity": "20",
            "to_location_id": business.location.id,
            "blocked_quantity": "5",
            "block_reason": "damage",
        },
        request_id="r304-damage",
    )
    review = json.loads(proposal.input)["_delivery_review"]
    assert review["effect"] == {"received": "20", "blocked": "5"}
    assert _blocks(session, business) == []

    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=review["token"], confirmed=True
    )
    assert core.stock_at(session, tenant, business.item.id) == 20
    assert _blocks(session, business) == [(Decimal("5.0000"), "damage", "active")]
    (block,) = session.scalars(select(StockBlock).where(StockBlock.tenant_id == tenant))
    assert block.receipt_movement_id is not None


def test_a_receipt_cannot_block_more_than_it_brings(session, business):
    try:
        prepare_delivery_action(
            session,
            business.tenant.id,
            "movement_create",
            {
                "movement_type": "receipt",
                "item_id": business.item.id,
                "quantity": "20",
                "to_location_id": business.location.id,
                "blocked_quantity": "21",
                "block_reason": "inspection",
            },
            request_id="r304-over",
        )
    except core.InvalidOperation as error:
        assert error.code == "stock_block_exceeds_receipt"
    else:
        raise AssertionError("a receipt blocked more than it received")


def test_a_package_receipt_blocks_everything_for_inspection(session, business):
    tenant = business.tenant.id
    proposal = create_change_proposal(
        session,
        tenant,
        "shipment_receive",
        {
            "purpose": "supplier_delivery",
            "counterparty_id": business.supplier.id,
            "tracking_number": "QC-1",
            "movements": [
                {
                    "item_id": business.item.id,
                    "to_location_id": business.location.id,
                    "quantity": "12",
                    "blocked_quantity": "12",
                    "block_reason": "inspection",
                }
            ],
        },
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=token, confirmed=True
    )

    assert core.stock_at(session, tenant, business.item.id) == 12
    assert _blocks(session, business) == [(Decimal("12.0000"), "inspection", "active")]


def test_an_agent_blocks_releases_and_scraps_and_a_person_confirms(session, business):
    tenant = business.tenant.id
    _stock(session, business, "20")

    proposed = MCP_TOOL_REGISTRY["stock_block_propose"].handler(
        session,
        tenant,
        {
            "item_id": business.item.id,
            "location_id": business.location.id,
            "quantity": "5",
            "reason_code": "quality",
        },
    )
    preview = proposed["preview"]["stock_block"]
    assert (preview["free_before"], preview["free_after"]) == ("20", "15")
    assert _blocks(session, business) == []
    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )
    (block,) = session.scalars(select(StockBlock).where(StockBlock.tenant_id == tenant))

    released = MCP_TOOL_REGISTRY["stock_block_release_propose"].handler(
        session, tenant, {"block_id": block.id, "quantity": "2", "reason": "passed QC"}
    )
    approve_and_execute_proposal(
        session, tenant, released["proposal_id"], confirmed=True
    )
    assert _blocks(session, business) == [(Decimal(3), "quality", "active")]

    # The same block, still stating 5, now has 3 open (spec 316).
    scrapped = MCP_TOOL_REGISTRY["stock_block_scrap_propose"].handler(
        session, tenant, {"block_id": block.id, "reason": "cracked"}
    )
    approve_and_execute_proposal(
        session, tenant, scrapped["proposal_id"], confirmed=True
    )
    assert _blocks(session, business) == []
    assert core.stock_at(session, tenant, business.item.id) == 17
    (read,) = MCP_TOOL_REGISTRY["stock_blocks"].handler(
        session, tenant, {"status": "resolved"}
    )
    assert (read["id"], read["quantity"], read["open_quantity"]) == (block.id, "5", "0")
    assert [(row["kind"], row["quantity"]) for row in read["resolutions"]] == [
        ("release", "2"),
        ("scrap", "3"),
    ]
    assert MCP_TOOL_REGISTRY["stock_blocks"].handler(session, tenant, {}) == []
    with pytest.raises(core.InvalidOperation) as refused:
        MCP_TOOL_REGISTRY["stock_blocks"].handler(
            session, tenant, {"status": "released"}
        )
    assert refused.value.code == "stock_block_status_unsupported"


def test_a_release_after_the_block_changed_is_refused(session, business):
    tenant = business.tenant.id
    _stock(session, business, "20")
    block = block_stock(
        session, tenant, business.item.id, business.location.id, "5", "quality"
    )
    stale = create_change_proposal(
        session, tenant, "stock_block_release", {"block_id": block.id, "reason": "ok"}
    )
    # Someone else releases part of it first.
    from reality.services.stock_blocks import release_stock_block

    release_stock_block(session, tenant, block.id, "1", reason="partial")

    try:
        approve_and_execute_proposal(session, tenant, stale.id, confirmed=True)
    except core.InvalidOperation as error:
        assert error.code == "stock_block_changed_since_review"
    else:
        raise AssertionError("a stale release was executed")


def test_the_web_lists_prepares_and_confirms(session, business, monkeypatch):
    _stock(session, business, "20")
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{business.tenant.id}"

    prepared = client.post(
        f"{prefix}/stock-blocks/proposals",
        json={
            "operation": "block",
            "item_id": business.item.id,
            "location_id": business.location.id,
            "quantity": "5",
            "reason_code": "damage",
        },
    )
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert body["preview"]["stock_block"]["free_after"] == "15"
    confirmed = client.post(
        f"{prefix}/change-proposals/{body['id']}/approve", json={"confirmed": True}
    )
    assert confirmed.status_code == 200, confirmed.text
    (row,) = client.get(f"{prefix}/stock-blocks").json()["rows"]
    assert (row["quantity"], row["reason_code"]) == ("5", "damage")

    refused = client.post(
        f"{prefix}/stock-blocks/proposals",
        json={
            "operation": "block",
            "item_id": business.item.id,
            "location_id": business.location.id,
            "quantity": "16",
            "reason_code": "damage",
        },
    )
    assert refused.status_code in {400, 409, 422}, refused.text
    assert "stock_block_exceeds_available" in refused.text


def test_another_company_cannot_touch_the_blocks(session, business, monkeypatch):
    _stock(session, business, "20")
    block = block_stock(
        session,
        business.tenant.id,
        business.item.id,
        business.location.id,
        "5",
        "quality",
    )
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)

    assert client.get(f"/api/tenants/{other.id}/stock-blocks").json()["rows"] == []
    foreign = client.post(
        f"/api/tenants/{other.id}/stock-blocks/proposals",
        json={"operation": "release", "block_id": block.id, "reason": "mine"},
    )
    assert foreign.status_code == 404, foreign.text
    assert _blocks(session, business) == [(Decimal("5.0000"), "quality", "active")]


def test_the_cli_blocks_and_releases(session, business, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    tenant = business.tenant.id
    _stock(session, business, "20")
    runner = CliRunner()

    result = runner.invoke(
        cli_module.app,
        [
            "stock-block",
            "block",
            business.item.id,
            business.location.id,
            "5",
            "--reason",
            "inspection",
            "--tenant",
            tenant,
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    (row,) = json.loads(
        runner.invoke(cli_module.app, ["stock-block", "list", "--tenant", tenant]).output
    )
    declined = runner.invoke(
        cli_module.app,
        ["stock-block", "release", row["id"], "--reason", "passed", "--tenant", tenant],
        input="n\n",
    )
    assert declined.exit_code == 0, declined.output
    assert _blocks(session, business) == [(Decimal("5.0000"), "inspection", "active")]
    assert (
        session.scalar(
            select(ChangeProposal.status).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.type == "tool:stock_block_release",
            )
        )
        == "rejected"
    )
    released = runner.invoke(
        cli_module.app,
        [
            "stock-block",
            "release",
            row["id"],
            "--reason",
            "passed",
            "--tenant",
            tenant,
            "--yes",
        ],
    )
    assert released.exit_code == 0, released.output
    assert _blocks(session, business) == []
