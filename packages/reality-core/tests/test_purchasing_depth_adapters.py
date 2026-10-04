"""Spec 310 FR-003: confirmed prices, supplier terms and the match through MCP, Web and CLI."""

import json

from fastapi.testclient import TestClient
from intake_review_support import reviewed_manual_order
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.mcp.server import _reject_unknown_fields
from reality.services import core
from reality.services.supplier_item_terms import supplier_item_terms
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _client(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    return TestClient(web_module.app)


def _purchase(session, business, number="PO-310-A"):
    _, document, (line,), (promise,) = reviewed_manual_order(
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
                "unit_price": "10",
                "gross_amount": "100",
            }
        ],
        "100",
    )
    return document, line, promise


def test_the_mcp_schemas_are_strict():
    for name, required in (
        ("supplier_item_terms_set_propose", {"party_id", "item_id"}),
        ("supplier_item_terms_remove_propose", {"party_id", "item_id"}),
        ("purchase_match", {"document_id"}),
    ):
        schema = MCP_TOOL_REGISTRY[name].input_schema
        assert schema["additionalProperties"] is False, name
        assert set(schema["required"]) == required, name
    assert (
        "unit_price"
        in MCP_TOOL_REGISTRY["commitment_revise_propose"].input_schema["properties"]
    )


def test_an_agent_states_terms_and_reads_the_match(session, business):
    tenant = business.tenant.id
    arguments = {
        "party_id": business.supplier.id,
        "item_id": business.item.id,
        "minimum_quantity": "50",
        "order_multiple": "12",
    }
    definition = MCP_TOOL_REGISTRY["supplier_item_terms_set_propose"]
    _reject_unknown_fields(definition.input_schema, arguments)
    proposed = definition.handler(session, tenant, arguments)
    review = proposed["preview"]["supplier_item_terms"]
    assert (review["current"], review["proposed"]["minimum_quantity"]) == (None, "50")
    assert supplier_item_terms(session, tenant) == []

    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )

    (row,) = MCP_TOOL_REGISTRY["supplier_item_terms"].handler(
        session, tenant, {"party_id": business.supplier.id}
    )
    assert (row["minimum_quantity"], row["order_multiple"]) == ("50", "12")
    document, _, _ = _purchase(session, business)
    match = MCP_TOOL_REGISTRY["purchase_match"].handler(
        session, tenant, {"document_id": document.id}
    )
    # Nothing arrived and nothing was billed: only the receipt is missing.
    assert match["lines"][0]["differences"] == ["received_short"]


def test_the_web_states_terms_revises_a_price_and_reads_the_match(
    session, business, monkeypatch
):
    tenant = business.tenant.id
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{tenant}"
    prepared = client.post(
        f"{prefix}/supplier-item-terms/proposals",
        json={
            "operation": "set",
            "party_id": business.supplier.id,
            "item_id": business.item.id,
            "minimum_quantity": "5",
        },
    )
    assert prepared.status_code == 200, prepared.text
    confirmed = client.post(
        f"{prefix}/change-proposals/{prepared.json()['id']}/approve",
        json={"confirmed": True},
    )
    assert confirmed.status_code == 200, confirmed.text
    rows = client.get(
        f"{prefix}/supplier-item-terms", params={"item_id": business.item.id}
    ).json()["rows"]
    assert rows[0]["minimum_quantity"] == "5"

    document, _, promise = _purchase(session, business)
    revised = client.post(
        f"{prefix}/commitments/{promise.id}/revisions",
        json={"request_id": "rev-310", "unit_price": "10.5"},
    )
    assert revised.status_code == 201, revised.text
    assert revised.json()["review"]["effect"]["confirmed_unit_price"] == "10.5"
    match = client.get(f"{prefix}/purchase-orders/{document.id}/match")
    assert match.status_code == 200, match.text
    assert match.json()["lines"][0]["ordered_unit_price"] == "10"

    refused = client.post(
        f"{prefix}/supplier-item-terms/proposals",
        json={
            "operation": "set",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "minimum_quantity": "1",
        },
    )
    assert "supplier_item_terms_party_not_supplier" in refused.text


def test_another_company_cannot_read_or_state(session, business, monkeypatch):
    document, _, _ = _purchase(session, business)
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)
    # Positive control: the company's own match is readable.
    assert (
        client.get(
            f"/api/tenants/{business.tenant.id}/purchase-orders/{document.id}/match"
        ).status_code
        == 200
    )

    assert (
        client.get(
            f"/api/tenants/{other.id}/purchase-orders/{document.id}/match"
        ).status_code
        == 404
    )
    assert (
        client.get(f"/api/tenants/{other.id}/supplier-item-terms").json()["rows"] == []
    )
    stated = client.post(
        f"/api/tenants/{other.id}/supplier-item-terms/proposals",
        json={
            "operation": "set",
            "party_id": business.supplier.id,
            "item_id": business.item.id,
            "minimum_quantity": "1",
        },
    )
    assert stated.status_code == 404, stated.text


def test_the_cli_states_terms_after_asking_and_reads_the_match(
    session, business, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    tenant = business.tenant.id
    runner = CliRunner()
    command = [
        "supplier-terms",
        "set",
        business.supplier.id,
        business.item.id,
        "--minimum",
        "50",
        "--tenant",
        tenant,
    ]

    declined = runner.invoke(cli_module.app, command, input="n\n")
    assert declined.exit_code == 0, declined.output
    assert supplier_item_terms(session, tenant) == []
    assert (
        session.scalar(
            select(ChangeProposal.status).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.type == "tool:supplier_item_terms_set",
            )
        )
        == "rejected"
    )
    stated = runner.invoke(cli_module.app, [*command, "--yes"])
    assert stated.exit_code == 0, stated.output
    listed = runner.invoke(
        cli_module.app, ["supplier-terms", "list", "--tenant", tenant]
    )
    assert json.loads(listed.output)[0]["minimum_quantity"] == "50"
    document, _, _ = _purchase(session, business)
    matched = runner.invoke(
        cli_module.app, ["purchase", "match", document.id, "--tenant", tenant]
    )
    assert json.loads(matched.output)["matched"] is False
