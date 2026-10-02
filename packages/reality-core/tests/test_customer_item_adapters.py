"""Spec 308 FR-003: customer item numbers through the review, MCP, Web and CLI."""

import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.services.customer_item_numbers import (
    resolve_customer_item,
    set_customer_item_number,
)
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from reality.web import api as api_module
from reality.web import app as web_module


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
    schema = _schema("customer_item_number_set_propose")
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"party_id", "item_id", "customer_item_number"}
    assert (
        "remember_for_customer"
        in _schema("order_line_item_assign_propose")["properties"]
    )


def test_an_agent_proposes_and_a_person_confirms(session, business):
    tenant = business.tenant.id
    proposed = MCP_TOOL_REGISTRY["customer_item_number_set_propose"].handler(
        session,
        tenant,
        {
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "customer_item_number": "K-4711",
            "customer_item_name": "Laufrad",
        },
    )
    review = proposed["preview"]["customer_item_number"]
    assert (review["current"], review["proposed"]["item_id"]) == (
        None,
        business.item.id,
    )
    assert (
        resolve_customer_item(session, tenant, business.customer.id, "K-4711") is None
    )

    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )

    (row,) = MCP_TOOL_REGISTRY["customer_item_numbers"].handler(
        session, tenant, {"party_id": business.customer.id}
    )
    assert (row["customer_item_number"], row["customer_item_name"]) == (
        "K-4711",
        "Laufrad",
    )


def test_a_number_changed_after_its_review_is_refused(session, business):
    tenant = business.tenant.id
    lamp = core.create_item(session, tenant, "LAMP-308A", "Lamp")
    stale = create_change_proposal(
        session,
        tenant,
        "customer_item_number_set",
        {
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "customer_item_number": "K-1",
        },
    )
    set_customer_item_number(session, tenant, business.customer.id, lamp.id, "K-1", "")

    try:
        approve_and_execute_proposal(session, tenant, stale.id, confirmed=True)
    except core.InvalidOperation as error:
        assert error.code == "customer_item_number_changed_since_review"
    else:
        raise AssertionError("a stale mapping was stated")


def test_the_web_sets_reads_and_removes(session, business, monkeypatch):
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{business.tenant.id}"

    for body in (
        {
            "operation": "set",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "customer_item_number": "K-7",
        },
        {
            "operation": "remove",
            "party_id": business.customer.id,
            "customer_item_number": "K-7",
        },
    ):
        prepared = client.post(f"{prefix}/customer-item-numbers/proposals", json=body)
        assert prepared.status_code == 200, prepared.text
        confirmed = client.post(
            f"{prefix}/change-proposals/{prepared.json()['id']}/approve",
            json={"confirmed": True},
        )
        assert confirmed.status_code == 200, confirmed.text
        if body["operation"] == "set":
            rows = client.get(
                f"{prefix}/customer-item-numbers",
                params={"party_id": business.customer.id},
            ).json()["rows"]
            assert [row["customer_item_number"] for row in rows] == ["K-7"]
    assert (
        client.get(
            f"{prefix}/customer-item-numbers", params={"party_id": business.customer.id}
        ).json()["rows"]
        == []
    )
    refused = client.post(
        f"{prefix}/customer-item-numbers/proposals",
        json={
            "operation": "set",
            "party_id": business.supplier.id,
            "item_id": business.item.id,
            "customer_item_number": "X",
        },
    )
    assert refused.status_code in {400, 409, 422}, refused.text
    assert "customer_item_number_party_not_customer" in refused.text


def test_another_company_cannot_read_or_state(session, business, monkeypatch):
    set_customer_item_number(
        session, business.tenant.id, business.customer.id, business.item.id, "K-1", ""
    )
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)
    # Positive control: the company's own list is readable.
    own = client.get(f"/api/tenants/{business.tenant.id}/customer-item-numbers")
    assert len(own.json()["rows"]) == 1

    assert (
        client.get(f"/api/tenants/{other.id}/customer-item-numbers").json()["rows"]
        == []
    )
    stated = client.post(
        f"/api/tenants/{other.id}/customer-item-numbers/proposals",
        json={
            "operation": "set",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "customer_item_number": "K-2",
        },
    )
    assert stated.status_code == 404, stated.text


def test_the_cli_states_after_asking(session, business, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    tenant = business.tenant.id
    runner = CliRunner()
    command = [
        "customer-item",
        "set",
        business.customer.id,
        "K-9",
        business.item.id,
        "--name",
        "Rad",
        "--tenant",
        tenant,
    ]

    declined = runner.invoke(cli_module.app, command, input="n\n")
    assert declined.exit_code == 0, declined.output
    assert resolve_customer_item(session, tenant, business.customer.id, "K-9") is None
    assert (
        session.scalar(
            select(ChangeProposal.status).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.type == "tool:customer_item_number_set",
            )
        )
        == "rejected"
    )
    stated = runner.invoke(cli_module.app, [*command, "--yes"])
    assert stated.exit_code == 0, stated.output
    listed = runner.invoke(
        cli_module.app,
        ["customer-item", "list", "--party", business.customer.id, "--tenant", tenant],
    )
    assert json.loads(listed.output)[0]["customer_item_number"] == "K-9"


def test_an_agent_orders_by_the_customers_number(session, business):
    from reality.mcp.server import _reject_unknown_fields

    tenant = business.tenant.id
    set_customer_item_number(
        session, tenant, business.customer.id, business.item.id, "K-4711", ""
    )
    arguments = {
        "direction": "sales",
        "number": "SO-308-MCP",
        "company_party_id": business.company.id,
        "counterparty_id": business.customer.id,
        "location_id": business.location.id,
        "gross_amount": "20",
        "lines": [
            {
                "customer_item_number": "K-4711",
                "quantity": "2",
                "unit": "pcs",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
    }
    definition = MCP_TOOL_REGISTRY["order_create_propose"]
    _reject_unknown_fields(definition.input_schema, arguments)
    assert (
        "item_id"
        not in definition.input_schema["properties"]["lines"]["items"]["required"]
    )

    proposed = definition.handler(session, tenant, arguments)

    (line,) = proposed["preview"]["state"]["creation"]["lines"]
    assert (line["item_id"], line["customer_item_number"]) == (
        business.item.id,
        "K-4711",
    )
