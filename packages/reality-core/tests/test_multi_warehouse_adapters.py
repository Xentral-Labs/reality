"""Spec 303 FR-004: several warehouses behind MCP/Chat, Web and CLI."""

import json
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, Reservation
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.services.delivery_actions import delivery_proposal_detail
from reality.services.exceptions import operational_exceptions
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _setup(session, business):
    munich = reviewed_create_location(session, business.tenant.id, "Munich")
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "40",
        to_location_id=munich.id,
    )
    promise = core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "4",
        "2026-10-10",
    )
    return munich, promise


def _reserved(session, business, promise):
    session.expire_all()
    return [
        (row.location_id, row.quantity)
        for row in session.scalars(
            select(Reservation).where(
                Reservation.tenant_id == business.tenant.id,
                Reservation.commitment_id == promise.id,
                Reservation.status == "active",
            )
        )
    ]


def _client(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    return TestClient(web_module.app)


def _finding(session, business, promise):
    return next(
        row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == "stock_in_another_location" and row.record_id == promise.id
    )


def test_the_mcp_reservation_schema_carries_the_location():
    schema = next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == "reservation_propose"
    )
    assert schema["additionalProperties"] is False
    assert "location_id" in schema["properties"]
    assert schema["required"] == ["commitment_id"]


def test_an_agent_reserves_where_the_finding_points(session, business):
    tenant = business.tenant.id
    munich, promise = _setup(session, business)
    where = _finding(session, business, promise).trace["locations"][0]

    proposed = MCP_TOOL_REGISTRY["reservation_propose"].handler(
        session,
        tenant,
        {
            "commitment_id": promise.id,
            "location_id": where["location_id"],
            "quantity": where["proposed"],
        },
    )
    proposal = session.get(ChangeProposal, (tenant, proposed["proposal_id"]))
    review = json.loads(proposal.input)["_delivery_review"]
    assert review["state"]["inventory"]["location_id"] == munich.id
    assert _reserved(session, business, promise) == []

    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=review["token"], confirmed=True
    )
    assert _reserved(session, business, promise) == [(munich.id, Decimal("4.0000"))]


def test_an_agent_prepares_the_transfer_the_finding_proposes(session, business):
    tenant = business.tenant.id
    munich, promise = _setup(session, business)
    where = _finding(session, business, promise).trace["locations"][0]

    proposed = MCP_TOOL_REGISTRY["movement_create_propose"].handler(
        session,
        tenant,
        {
            "movement_type": "transfer",
            "item_id": business.item.id,
            "quantity": where["proposed"],
            "from_location_id": where["location_id"],
            "to_location_id": business.location.id,
        },
    )
    proposal = session.get(ChangeProposal, (tenant, proposed["proposal_id"]))
    review = json.loads(proposal.input)["_delivery_review"]
    # The transfer is reviewed where it takes stock from, and moves only stock.
    assert review["effect"] == {"transferred": "4"}
    assert review["state"]["inventory"]["location_id"] == munich.id
    assert core.stock_at(session, tenant, business.item.id, business.location.id) == 0

    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=review["token"], confirmed=True
    )
    assert core.stock_at(session, tenant, business.item.id, business.location.id) == 4
    assert core.stock_at(session, tenant, business.item.id, munich.id) == 36
    assert _reserved(session, business, promise) == []
    assert delivery_proposal_detail(session, tenant, proposal.id)["verification"] == (
        "verified"
    )


def test_the_web_reserves_elsewhere_and_refuses_a_place_without_stock(
    session, business, monkeypatch
):
    munich, promise = _setup(session, business)
    transit = reviewed_create_location(session, business.tenant.id, "In transit")
    transit.allows_stock = False
    session.commit()
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{business.tenant.id}"

    prepared = client.post(
        f"{prefix}/delivery-actions/prepare",
        json={
            "tool": "reserve",
            "request_id": "web-303",
            "arguments": {"commitment_id": promise.id, "location_id": munich.id},
        },
    )
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    confirmed = client.post(
        f"{prefix}/change-proposals/{body['id']}/approve",
        json={"confirmed": True, "review_token": body["review"]["token"]},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert _reserved(session, business, promise) == [(munich.id, Decimal("4.0000"))]

    refused = client.post(
        f"{prefix}/delivery-actions/prepare",
        json={
            "tool": "reserve",
            "request_id": "web-303-transit",
            "arguments": {"commitment_id": promise.id, "location_id": transit.id},
        },
    )
    assert refused.status_code in {400, 409, 422}, refused.text
    assert "reservation_location_not_stock" in refused.text


def test_another_company_cannot_reserve_into_the_promise(
    session, business, monkeypatch
):
    munich, promise = _setup(session, business)
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)

    foreign = client.post(
        f"/api/tenants/{other.id}/delivery-actions/prepare",
        json={
            "tool": "reserve",
            "request_id": "foreign-303",
            "arguments": {"commitment_id": promise.id, "location_id": munich.id},
        },
    )
    assert foreign.status_code == 404, foreign.text
    assert _reserved(session, business, promise) == []


def test_the_cli_reserves_at_a_named_warehouse(session, business, monkeypatch):
    munich, promise = _setup(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)

    result = CliRunner().invoke(
        cli_module.app,
        [
            "commitment",
            "reserve",
            promise.id,
            "--tenant",
            business.tenant.id,
            "--location-id",
            munich.id,
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    assert _reserved(session, business, promise) == [(munich.id, Decimal("4.0000"))]


from intake_review_support import reviewed_create_location
