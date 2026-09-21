"""The two movement references reach every adapter (spec 099 FR-005, spec 082).

`record_movement` has accepted `resolves_movement_id` since spec 082 and
`return_announcement_id` since spec 099. The adapters lagged: the MCP schema
did not name the announcement, the web endpoint accepted both fields and
passed neither on, and the CLI had no flag for either. An agent could
therefore never fulfil an announcement, and `announced_return_not_arrived`
kept reporting parcels that had arrived. These tests pin each adapter.
"""

import json
from datetime import UTC, datetime

from conftest import record_by_id
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import Movement, ReturnAnnouncement
from reality.mcp.catalog import model_tool_schemas
from reality.services.core import (
    announce_customer_return,
    create_commitment,
    record_movement,
)
from reality.tools.application import confirm_tool, propose_tool
from reality.web import api as api_module
from reality.web import app as web_module

SHIPPED_AT = datetime(2026, 8, 20, 12, tzinfo=UTC)
ARRIVED_AT = datetime(2026, 8, 28, 12, tzinfo=UTC)


def announced_delivery(session, business, quantity=5):
    """A shipped customer delivery with an open announcement for all of it."""
    tenant_id = business.tenant.id
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        50,
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        datetime(2026, 8, 15, 12, tzinfo=UTC),
    )
    record_movement(
        session,
        tenant_id,
        "shipment",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
        occurred_at=SHIPPED_AT,
    )
    announcement = announce_customer_return(
        session, tenant_id, commitment.id, quantity, reference="RMA-CUSTOMER-1"
    )
    return commitment, announcement


def test_the_movement_tool_schema_names_both_references():
    schemas = {s["function"]["name"]: s["function"] for s in model_tool_schemas()}
    properties = schemas["movement_create_propose"]["parameters"]["properties"]
    assert {"resolves_movement_id", "return_announcement_id"} <= set(properties)


def test_an_agent_fulfils_an_announcement_through_the_proposal_boundary(
    session, business
):
    commitment, announcement = announced_delivery(session, business)
    proposal = propose_tool(
        session,
        business.tenant.id,
        "movement_create",
        {
            "movement_type": "return",
            "item_id": business.item.id,
            "quantity": "5",
            "to_location_id": business.location.id,
            "commitment_id": commitment.id,
            "return_announcement_id": announcement.id,
            "occurred_at": ARRIVED_AT.isoformat(),
        },
    )
    review = json.loads(proposal.input).get("_delivery_review")
    executed = confirm_tool(
        session,
        business.tenant.id,
        proposal.id,
        review_token=review["token"] if review else None,
        confirmed=True,
    )
    assert executed.status == "executed"
    session.expire_all()
    assert (
        record_by_id(session, ReturnAnnouncement, announcement.id).status == "fulfilled"
    )
    arrived = session.scalar(
        select(Movement).where(Movement.return_announcement_id == announcement.id)
    )
    assert arrived is not None and arrived.commitment_id == commitment.id


def test_the_web_api_carries_both_references(session, business, monkeypatch):
    commitment, announcement = announced_delivery(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)
    prefix = f"/api/tenants/{business.tenant.id}"

    back = client.post(
        f"{prefix}/movements",
        json={
            "type": "return",
            "item_id": business.item.id,
            "quantity": "5",
            "to_location_id": business.location.id,
            "commitment_id": commitment.id,
            "return_announcement_id": announcement.id,
            "occurred_at": ARRIVED_AT.isoformat(),
        },
    )
    assert back.status_code == 201, back.text
    assert back.json()["return_announcement_id"] == announcement.id
    session.expire_all()
    assert (
        record_by_id(session, ReturnAnnouncement, announcement.id).status == "fulfilled"
    )

    restocked = client.post(
        f"{prefix}/movements",
        json={
            "type": "transfer",
            "item_id": business.item.id,
            "quantity": "5",
            "from_location_id": business.location.id,
            "to_location_id": business.location.id,
            "resolves_movement_id": back.json()["id"],
        },
    )
    assert restocked.status_code == 201, restocked.text
    assert restocked.json()["resolves_movement_id"] == back.json()["id"]

    listed = {row["id"]: row for row in client.get(f"{prefix}/movements").json()}
    assert listed[back.json()["id"]]["return_announcement_id"] == announcement.id
    assert listed[restocked.json()["id"]]["resolves_movement_id"] == back.json()["id"]


def test_the_web_api_still_refuses_a_foreign_announcement(
    session, business, monkeypatch
):
    commitment, _ = announced_delivery(session, business)
    other, foreign = announced_delivery(session, business, quantity=2)
    assert other.id != commitment.id
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)
    response = client.post(
        f"/api/tenants/{business.tenant.id}/movements",
        json={
            "type": "return",
            "item_id": business.item.id,
            "quantity": "1",
            "to_location_id": business.location.id,
            "commitment_id": commitment.id,
            "return_announcement_id": foreign.id,
        },
    )
    assert response.status_code == 400, response.text
    assert "own delivery" in response.text


def test_the_cli_carries_both_references(session, business, monkeypatch):
    commitment, announcement = announced_delivery(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    runner = CliRunner()

    back = runner.invoke(
        cli_module.app,
        [
            "movement",
            "record",
            "return",
            business.item.id,
            "5",
            "--tenant",
            business.tenant.id,
            "--to-location-id",
            business.location.id,
            "--commitment-id",
            commitment.id,
            "--return-announcement-id",
            announcement.id,
        ],
    )
    assert back.exit_code == 0, back.output
    session.expire_all()
    assert (
        record_by_id(session, ReturnAnnouncement, announcement.id).status == "fulfilled"
    )
    arrived = session.scalar(
        select(Movement).where(Movement.return_announcement_id == announcement.id)
    )
    restock = runner.invoke(
        cli_module.app,
        [
            "movement",
            "record",
            "transfer",
            business.item.id,
            "5",
            "--tenant",
            business.tenant.id,
            "--from-location-id",
            business.location.id,
            "--to-location-id",
            business.location.id,
            "--resolves-movement-id",
            arrived.id,
        ],
    )
    assert restock.exit_code == 0, restock.output
    session.expire_all()
    resolving = session.scalar(
        select(Movement).where(Movement.resolves_movement_id == arrived.id)
    )
    assert resolving is not None
