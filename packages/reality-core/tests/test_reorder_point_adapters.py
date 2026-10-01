"""Spec 302 FR-004: reorder points behind MCP/Chat, Web and CLI."""

import json
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, ItemReorderPoint
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.reorder_points import set_reorder_point
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _schema(name):
    return next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == name
    )


def _points(session, tenant_id):
    session.expire_all()
    return [
        (row.item_id, row.location_id, row.reorder_point, row.reorder_quantity)
        for row in session.scalars(
            select(ItemReorderPoint).where(ItemReorderPoint.tenant_id == tenant_id)
        )
    ]


def _client(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    return TestClient(web_module.app)


def test_the_mcp_schemas_are_strict():
    point = _schema("reorder_point_set_propose")
    assert point["additionalProperties"] is False
    assert set(point["required"]) == {
        "item_id",
        "location_id",
        "reorder_point",
        "reorder_quantity",
    }
    removal = _schema("reorder_point_remove_propose")
    assert removal["additionalProperties"] is False
    assert set(removal["properties"]) == {"item_id", "location_id"}
    assert _schema("reorder_points")["additionalProperties"] is False


def test_an_agent_proposes_a_point_and_a_person_confirms(session, business):
    tenant = business.tenant.id
    arguments = {
        "item_id": business.item.id,
        "location_id": business.location.id,
        "reorder_point": "20",
        "reorder_quantity": "48",
    }

    proposed = MCP_TOOL_REGISTRY["reorder_point_set_propose"].handler(
        session, tenant, arguments
    )
    review = proposed["preview"]["reorder_point"]
    assert (review["current"], review["proposed"]) == (
        None,
        {"reorder_point": "20", "reorder_quantity": "48"},
    )
    # Nothing is stated until a person confirms.
    assert _points(session, tenant) == []

    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )
    assert _points(session, tenant) == [
        (business.item.id, business.location.id, Decimal("20.0000"), Decimal("48.0000"))
    ]

    read = MCP_TOOL_REGISTRY["reorder_points"].handler(
        session, tenant, {"item_id": business.item.id}
    )
    assert [row["reorder_point"] for row in read] == ["20"]

    # The change is reviewed against what is there now.
    changed = MCP_TOOL_REGISTRY["reorder_point_set_propose"].handler(
        session, tenant, {**arguments, "reorder_point": "30"}
    )
    assert changed["preview"]["reorder_point"]["current"] == {
        "reorder_point": "20",
        "reorder_quantity": "48",
    }
    removal = MCP_TOOL_REGISTRY["reorder_point_remove_propose"].handler(
        session,
        tenant,
        {"item_id": business.item.id, "location_id": business.location.id},
    )
    approve_and_execute_proposal(
        session, tenant, removal["proposal_id"], confirmed=True
    )
    assert _points(session, tenant) == []


def test_a_confirmation_after_the_point_changed_is_refused(session, business):
    tenant = business.tenant.id
    proposed = MCP_TOOL_REGISTRY["reorder_point_set_propose"].handler(
        session,
        tenant,
        {
            "item_id": business.item.id,
            "location_id": business.location.id,
            "reorder_point": "20",
            "reorder_quantity": "48",
        },
    )
    # Someone else states a point after the review was prepared.
    set_reorder_point(
        session, tenant, business.item.id, business.location.id, "5", "10"
    )

    try:
        approve_and_execute_proposal(
            session, tenant, proposed["proposal_id"], confirmed=True
        )
    except core.InvalidOperation as error:
        assert error.code == "reorder_point_changed_since_review"
    else:
        raise AssertionError("a stale review was executed")
    assert _points(session, tenant) == [
        (business.item.id, business.location.id, Decimal("5.0000"), Decimal("10.0000"))
    ]


def test_an_invalid_point_is_refused_before_anything_is_proposed(session, business):
    tenant = business.tenant.id
    service = core.create_item(
        session, tenant, "SRV-302", "Assembly", item_type="service"
    )
    try:
        MCP_TOOL_REGISTRY["reorder_point_set_propose"].handler(
            session,
            tenant,
            {
                "item_id": service.id,
                "location_id": business.location.id,
                "reorder_point": "1",
                "reorder_quantity": "1",
            },
        )
    except core.InvalidOperation as error:
        assert error.code == "reorder_point_item_not_stocked"
    else:
        raise AssertionError("a service item took a reorder point")
    assert (
        session.scalar(
            select(ChangeProposal).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.type == "tool:reorder_point_set",
            )
        )
        is None
    )


def test_the_web_reads_prepares_and_confirms(session, business, monkeypatch):
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{business.tenant.id}"

    prepared = client.post(
        f"{prefix}/reorder-points/proposals",
        json={
            "operation": "set",
            "item_id": business.item.id,
            "location_id": business.location.id,
            "reorder_point": "20",
            "reorder_quantity": "48",
        },
    )
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert body["preview"]["reorder_point"]["proposed"]["reorder_quantity"] == "48"
    assert client.get(f"{prefix}/reorder-points").json()["rows"] == []

    confirmed = client.post(
        f"{prefix}/change-proposals/{body['id']}/approve", json={"confirmed": True}
    )
    assert confirmed.status_code == 200, confirmed.text
    (row,) = client.get(
        f"{prefix}/reorder-points", params={"item_id": business.item.id}
    ).json()["rows"]
    assert (row["reorder_point"], row["location"]) == ("20", business.location.name)

    refused = client.post(
        f"{prefix}/reorder-points/proposals",
        json={
            "operation": "set",
            "item_id": business.item.id,
            "location_id": business.location.id,
            "reorder_point": "20",
            "reorder_quantity": "0",
        },
    )
    assert refused.status_code in {400, 409, 422}, refused.text
    assert "reorder_point_values_invalid" in refused.text

    removed = client.post(
        f"{prefix}/reorder-points/proposals",
        json={
            "operation": "remove",
            "item_id": business.item.id,
            "location_id": business.location.id,
        },
    )
    assert removed.status_code == 200, removed.text
    assert removed.json()["preview"]["reorder_point"]["proposed"] is None


def test_another_company_cannot_read_or_change_the_points(
    session, business, monkeypatch
):
    tenant = business.tenant.id
    set_reorder_point(
        session, tenant, business.item.id, business.location.id, "20", "48"
    )
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)

    assert client.get(f"/api/tenants/{other.id}/reorder-points").json()["rows"] == []
    foreign = client.post(
        f"/api/tenants/{other.id}/reorder-points/proposals",
        json={
            "operation": "remove",
            "item_id": business.item.id,
            "location_id": business.location.id,
        },
    )
    assert foreign.status_code == 404, foreign.text
    assert len(_points(session, tenant)) == 1


def test_the_cli_lists_sets_and_removes(session, business, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    tenant = business.tenant.id
    runner = CliRunner()

    result = runner.invoke(
        cli_module.app,
        [
            "reorder-point",
            "set",
            business.item.id,
            business.location.id,
            "--point",
            "20",
            "--quantity",
            "48",
            "--tenant",
            tenant,
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    assert _points(session, tenant) == [
        (business.item.id, business.location.id, Decimal("20.0000"), Decimal("48.0000"))
    ]

    listed = runner.invoke(
        cli_module.app, ["reorder-point", "list", "--tenant", tenant]
    )
    assert listed.exit_code == 0, listed.output
    assert json.loads(listed.output)[0]["reorder_quantity"] == "48"

    # Without --yes the person is asked, and declining changes nothing.
    declined = runner.invoke(
        cli_module.app,
        [
            "reorder-point",
            "remove",
            business.item.id,
            business.location.id,
            "--tenant",
            tenant,
        ],
        input="n\n",
    )
    assert declined.exit_code == 0, declined.output
    assert len(_points(session, tenant)) == 1
    removed = runner.invoke(
        cli_module.app,
        [
            "reorder-point",
            "remove",
            business.item.id,
            business.location.id,
            "--tenant",
            tenant,
            "--yes",
        ],
    )
    assert removed.exit_code == 0, removed.output
    assert _points(session, tenant) == []


def test_an_agent_orders_from_the_entry_and_the_entry_clears(session, business):
    """FR-003: the entry's causal values fill the reviewed order; nothing else orders."""
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "12",
        to_location_id=business.location.id,
    )
    set_reorder_point(
        session, tenant, business.item.id, business.location.id, "20", "48"
    )
    price_list = core.create_price_list(
        session, tenant, "PL", "Parts", "purchase", "EUR"
    )
    core.create_price_list_entry(
        session, tenant, price_list.id, business.item.id, "1", "4.50", "pcs"
    )
    core.assign_party_price_list(session, tenant, business.supplier.id, price_list.id)

    (entry,) = [
        row
        for row in operational_exceptions(session, tenant)
        if row.class_id == "reorder_point_reached"
    ]
    values = entry.causal_values
    quantity, price = (
        Decimal(values["proposed_quantity"]),
        Decimal(values["unit_price"]),
    )
    proposed = MCP_TOOL_REGISTRY["order_create_propose"].handler(
        session,
        tenant,
        {
            "direction": "purchase",
            "number": "PO-302-AGENT",
            "company_party_id": business.company.id,
            "counterparty_id": entry.trace["supplier_id"],
            "location_id": entry.trace["location_id"],
            "currency": "EUR",
            "gross_amount": str(quantity * price),
            "lines": [
                {
                    "item_id": entry.trace["item_id"],
                    "quantity": str(quantity),
                    "unit": values["proposed_unit"],
                    "unit_price": str(price),
                    "gross_amount": str(quantity * price),
                }
            ],
        },
    )
    # Proposing orders nothing: the entry is still there.
    assert any(
        row.class_id == "reorder_point_reached"
        for row in operational_exceptions(session, tenant)
    )
    proposal = session.get(ChangeProposal, (tenant, proposed["proposal_id"]))
    review = json.loads(proposal.input)["_delivery_review"]
    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=review["token"], confirmed=True
    )
    assert not any(
        row.class_id == "reorder_point_reached"
        for row in operational_exceptions(session, tenant)
    )
