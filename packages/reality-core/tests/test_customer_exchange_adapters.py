"""Spec 293 FR-011: one reviewed exchange tool behind Web, MCP/Chat and CLI."""

import json
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, CustomerExchange
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.tools.application import approve_and_execute_proposal, run_read_tool
from reality.web import api as api_module
from reality.web import app as web_module


def returned_goods(session, business, quantity="2"):
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    commitment = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        "2026-09-10",
    )
    core.reserve(session, tenant, commitment.id)
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    goods_back = core.record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        "1",
        to_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    return commitment, goods_back


def arguments_for(business, goods_back):
    return {
        "return_movement_id": goods_back.id,
        "quantity": "1",
        "replacement_item_id": business.item.id,
        "replacement_quantity": "1",
        "reason": "Customer wants another size",
    }


def exchanges(session):
    return session.scalar(select(func.count()).select_from(CustomerExchange))


def test_the_mcp_proposal_schema_is_strict_and_names_both_return_sides():
    schema = next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == "customer_exchange_propose"
    )
    assert schema["additionalProperties"] is False
    assert {
        "return_movement_id",
        "return_announcement_id",
        "quantity",
        "replacement_item_id",
        "replacement_quantity",
        "location_id",
        "due_at",
        "reason",
    } == set(schema["properties"])
    assert set(schema["required"]) == {
        "quantity",
        "replacement_item_id",
        "replacement_quantity",
        "reason",
    }


def test_an_agent_proposes_and_a_person_confirms_the_exchange(session, business):
    commitment, goods_back = returned_goods(session, business)

    proposed = MCP_TOOL_REGISTRY["customer_exchange_propose"].handler(
        session, business.tenant.id, arguments_for(business, goods_back)
    )
    # Proposing records nothing.
    assert exchanges(session) == 0
    proposal = session.get(
        ChangeProposal, (business.tenant.id, proposed["proposal_id"])
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )

    assert exchanges(session) == 1
    read = MCP_TOOL_REGISTRY["customer_exchange"].handler(
        session, business.tenant.id, {"return_movement_id": goods_back.id}
    )
    assert read["returned_delivery_id"] == commitment.id
    assert Decimal(read["settles"]) == Decimal(1)
    shared = run_read_tool(
        session,
        business.tenant.id,
        "customer_exchange",
        {"return_movement_id": goods_back.id},
    )
    assert shared == read


def test_the_web_prepares_reviews_confirms_and_reads_an_exchange(
    session, business, monkeypatch
):
    _, goods_back = returned_goods(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)
    prefix = f"/api/tenants/{business.tenant.id}"

    prepared = client.post(
        f"{prefix}/delivery-actions/prepare",
        json={
            "tool": "customer_exchange_record",
            "request_id": "web-exchange",
            "arguments": arguments_for(business, goods_back),
        },
    )
    assert prepared.status_code == 200, prepared.text
    preview = prepared.json()
    assert preview["review"]["effect"]["money_moves"] is False
    assert exchanges(session) == 0

    confirmed = client.post(
        f"{prefix}/change-proposals/{preview['id']}/approve",
        json={"confirmed": True, "review_token": preview["review"]["token"]},
    )
    assert confirmed.status_code == 200, confirmed.text
    session.expire_all()
    exchange = session.scalars(select(CustomerExchange)).one()

    response = client.get(f"{prefix}/customer-exchanges/{exchange.id}")
    assert response.status_code == 200, response.text
    assert response.json()["replacement"]["commitment_id"] == (
        exchange.replacement_commitment_id
    )


def test_the_web_read_does_not_disclose_another_tenants_exchange(
    session, business, monkeypatch
):
    from reality.services.customer_exchanges import record_customer_exchange

    _, goods_back = returned_goods(session, business)

    exchange = record_customer_exchange(
        session, business.tenant.id, **arguments_for(business, goods_back)
    )
    other = core.create_tenant(session, "Other GmbH")
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)

    foreign = client.get(f"/api/tenants/{other.id}/customer-exchanges/{exchange.id}")
    assert foreign.status_code == 404, foreign.text
    # Positive control: the owning tenant reads it.
    own = client.get(
        f"/api/tenants/{business.tenant.id}/customer-exchanges/{exchange.id}"
    )
    assert own.status_code == 200, own.text


def test_the_cli_reads_proposes_and_confirms_an_exchange(
    session, business, monkeypatch
):
    _, goods_back = returned_goods(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    runner = CliRunner()

    proposed = runner.invoke(
        cli_module.app,
        [
            "customer-exchange-propose",
            json.dumps(arguments_for(business, goods_back)),
            "cli-exchange",
            "--tenant-id",
            business.tenant.id,
        ],
    )
    assert proposed.exit_code == 0, proposed.output
    detail = json.loads(proposed.output)
    assert detail["review"]["effect"]["money_moves"] is False
    assert exchanges(session) == 0

    confirmed = runner.invoke(
        cli_module.app,
        [
            "customer-exchange-confirm",
            detail["id"],
            detail["review"]["token"],
            "--yes",
            "--tenant-id",
            business.tenant.id,
        ],
    )
    assert confirmed.exit_code == 0, confirmed.output
    assert json.loads(confirmed.output)["verification"] == "verified"

    read = runner.invoke(
        cli_module.app,
        [
            "customer-exchange",
            "--return-movement-id",
            goods_back.id,
            "--tenant-id",
            business.tenant.id,
        ],
    )
    assert read.exit_code == 0, read.output
    assert Decimal(json.loads(read.output)["settles"]) == Decimal(1)


def test_the_cli_help_lists_the_exchange_commands():
    result = CliRunner().invoke(cli_module.app, ["--help"])
    for command in (
        "customer-exchange",
        "customer-exchange-propose",
        "customer-exchange-confirm",
    ):
        assert command in result.output
