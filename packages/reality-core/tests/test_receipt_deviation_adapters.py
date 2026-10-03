"""Spec 338 FR-007: deviations behind MCP/Chat, Web and CLI, through the shared review."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import CommitmentSubstitute
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.mcp.server import _reject_unknown_fields
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


def _purchase(session, business, number="PO-338-A"):
    _, _, _, (promise,) = core.create_manual_order(
        session,
        business.tenant.id,
        "purchase",
        number,
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit_price": "5",
                "gross_amount": "50",
            }
        ],
        "50",
    )
    return promise


def _substitutes(session, tenant):
    session.expire_all()
    return list(
        session.scalars(
            select(CommitmentSubstitute).where(CommitmentSubstitute.tenant_id == tenant)
        )
    )


def test_the_mcp_schemas_carry_the_new_fields_strictly():
    accept = _schema("commitment_substitute_accept_propose")
    assert accept["additionalProperties"] is False
    assert set(accept["required"]) == {"commitment_id", "item_id", "reason"}
    notice = _schema("shipment_notice_record_propose")
    advised = notice["properties"]["advised"]["items"]
    assert advised["additionalProperties"] is False
    assert set(advised["required"]) == {"commitment_id", "quantity"}
    receive = {
        branch["properties"]["purpose"]["const"]: branch
        for branch in _schema("shipment_receive_propose")["oneOf"]
    }
    purchase = receive["supplier_delivery"]
    assert "shipment_id" in purchase["properties"]
    movement = purchase["properties"]["movements"]["items"]["properties"]
    assert {"beyond_order", "meant_for_commitment_id"} <= set(movement)
    dispatch = {
        branch["properties"]["purpose"]["const"]: branch
        for branch in _schema("shipment_dispatch_propose")["oneOf"]
    }
    returned = dispatch["supplier_return"]["properties"]["movements"]["items"]
    # Only a receipt can bring in a surplus.
    assert "beyond_order" not in returned["properties"]
    assert "meant_for_commitment_id" in returned["properties"]


def test_an_agent_proposes_a_substitute_and_a_person_confirms(session, business):
    tenant = business.tenant.id
    successor = core.create_item(session, tenant, "BIKE-LIGHT-2", "Bike light v2")
    promise = _purchase(session, business)
    definition = MCP_TOOL_REGISTRY["commitment_substitute_accept_propose"]
    arguments = {
        "commitment_id": promise.id,
        "item_id": successor.id,
        "reason": "Successor model",
    }
    _reject_unknown_fields(definition.input_schema, arguments)

    proposed = definition.handler(session, tenant, arguments)

    assert proposed["requires_confirmation"] is True
    assert not _substitutes(session, tenant)
    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )
    (row,) = _substitutes(session, tenant)
    assert (row.commitment_id, row.item_id) == (promise.id, successor.id)


def test_an_agent_advises_and_receives_beyond_order(session, business):
    tenant = business.tenant.id
    promise = _purchase(session, business, "PO-338-B")
    notice = {
        "direction": "inbound",
        "purpose": "supplier_delivery",
        "counterparty_id": business.supplier.id,
        "advised": [{"commitment_id": promise.id, "quantity": "12"}],
    }
    definition = MCP_TOOL_REGISTRY["shipment_notice_record_propose"]
    _reject_unknown_fields(definition.input_schema, notice)
    proposed = definition.handler(session, tenant, notice)
    assert proposed["proposal_id"]
    receipt = {
        "purpose": "supplier_delivery",
        "counterparty_id": business.supplier.id,
        "movements": [
            {
                "commitment_id": promise.id,
                "item_id": business.item.id,
                "to_location_id": business.location.id,
                "quantity": "12",
                "beyond_order": True,
            }
        ],
    }
    receive = MCP_TOOL_REGISTRY["shipment_receive_propose"]
    _reject_unknown_fields(receive.input_schema, receipt)
    assert receive.handler(session, tenant, receipt)["proposal_id"]


def test_the_web_and_the_cli_accept_a_substitute(session, business, monkeypatch):
    tenant = business.tenant.id
    successor = core.create_item(session, tenant, "BIKE-LIGHT-2", "Bike light v2")
    other = core.create_item(session, tenant, "BIKE-LIGHT-3", "Bike light v3")
    promise = _purchase(session, business, "PO-338-C")
    session.commit()
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)

    response = client.post(
        f"/api/tenants/{tenant}/purchase-substitutes/proposals",
        json={"commitment_id": promise.id, "item_id": successor.id, "reason": "v2"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["preview"]["substitute"]["substitute_item"]["id"] == successor.id
    refused = client.post(
        f"/api/tenants/{tenant}/purchase-substitutes/proposals",
        json={"commitment_id": promise.id, "item_id": business.item.id, "reason": "x"},
    )
    assert refused.status_code == 400

    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    result = CliRunner().invoke(
        cli_module.app,
        [
            "purchase",
            "substitute",
            promise.id,
            other.id,
            "--reason",
            "v3 as well",
            "--tenant",
            tenant,
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    # The web proposal waits for its confirmation; the CLI confirmed its own.
    assert [row.item_id for row in _substitutes(session, tenant)] == [other.id]
