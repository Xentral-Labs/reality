"""Spec 306 FR-003: delivery rules through the review, MCP, Web and CLI."""

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from intake_review_support import reviewed_manual_order
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, SourceRecord
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.services.delivery_rules import effective_delivery_rule, state_delivery_rule
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from reality.web import api as api_module
from reality.web import app as web_module


def _order(session, business, number="SO-306-A"):
    _, document, _, _ = reviewed_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
        "20",
        requested_delivery_at=datetime(2026, 10, 20, tzinfo=UTC),
    )
    return document


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


def test_the_mcp_schema_is_strict():
    schema = _schema("delivery_rule_set_propose")
    assert schema["additionalProperties"] is False
    assert schema["properties"]["rule"]["enum"] == [
        "partial_allowed",
        "ship_complete",
        "no_backorders",
    ]
    assert set(schema["required"]) == {"rule", "reason"}


def test_an_agent_proposes_and_a_person_confirms(session, business):
    tenant = business.tenant.id
    document = _order(session, business)

    proposed = MCP_TOOL_REGISTRY["delivery_rule_set_propose"].handler(
        session,
        tenant,
        {
            "party_id": business.customer.id,
            "rule": "ship_complete",
            "reason": "Customer refuses partial deliveries",
        },
    )
    review = proposed["preview"]["delivery_rule"]
    assert (review["current"], review["proposed"]["rule"]) == (None, "ship_complete")
    assert review["orders"] == [
        {
            "document_id": document.id,
            "number": "SO-306-A",
            "now": "partial_allowed",
            "after": "ship_complete",
        }
    ]
    assert effective_delivery_rule(session, tenant, document.id)["rule"] == (
        "partial_allowed"
    )

    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )
    # The same confirmation again states nothing twice.
    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )

    read = MCP_TOOL_REGISTRY["delivery_rules"].handler(
        session, tenant, {"document_id": document.id}
    )
    assert (read["effective"]["rule"], read["effective"]["source"]) == (
        "ship_complete",
        "customer",
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == "internal_delivery_rule",
            )
        )
        == 1
    )


def test_executing_the_same_confirmation_again_states_nothing(session, business):
    tenant = business.tenant.id
    proposal = create_change_proposal(
        session,
        tenant,
        "delivery_rule_set",
        {"party_id": business.customer.id, "rule": "ship_complete", "reason": "Once"},
    )
    for _ in range(2):
        state_delivery_rule(
            session,
            tenant,
            "ship_complete",
            "Once",
            party_id=business.customer.id,
            action_id=proposal.id,
            _expected=None,
        )

    assert (
        session.scalar(
            select(func.count())
            .select_from(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == "internal_delivery_rule",
            )
        )
        == 1
    )


def test_a_rule_changed_after_its_review_is_refused(session, business):
    tenant = business.tenant.id
    stale = create_change_proposal(
        session,
        tenant,
        "delivery_rule_set",
        {
            "party_id": business.customer.id,
            "rule": "ship_complete",
            "reason": "First",
        },
    )
    state_delivery_rule(
        session, tenant, "no_backorders", "Meanwhile", party_id=business.customer.id
    )

    try:
        approve_and_execute_proposal(session, tenant, stale.id, confirmed=True)
    except core.InvalidOperation as error:
        assert error.code == "delivery_rule_changed_since_review"
    else:
        raise AssertionError("a stale delivery rule was stated")


def test_the_web_reads_prepares_and_confirms(session, business, monkeypatch):
    document = _order(session, business)
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{business.tenant.id}"

    prepared = client.post(
        f"{prefix}/delivery-rules/proposals",
        json={
            "document_id": document.id,
            "rule": "no_backorders",
            "reason": "Stated on the order",
        },
    )
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    confirmed = client.post(
        f"{prefix}/change-proposals/{body['id']}/approve", json={"confirmed": True}
    )
    assert confirmed.status_code == 200, confirmed.text

    read = client.get(f"{prefix}/delivery-rules", params={"document_id": document.id})
    assert read.status_code == 200, read.text
    assert (read.json()["effective"]["rule"], read.json()["effective"]["source"]) == (
        "no_backorders",
        "order",
    )
    refused = client.post(
        f"{prefix}/delivery-rules/proposals",
        json={"party_id": business.supplier.id, "rule": "ship_complete", "reason": "x"},
    )
    assert refused.status_code in {400, 409, 422}, refused.text
    assert "delivery_rule_party_not_customer" in refused.text


def test_another_company_cannot_read_or_state(session, business, monkeypatch):
    document = _order(session, business)
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)
    # Positive control: the same client reads its own company's order.
    own = client.get(
        f"/api/tenants/{business.tenant.id}/delivery-rules",
        params={"document_id": document.id},
    )
    assert own.status_code == 200, own.text
    prefix = f"/api/tenants/{other.id}"

    read = client.get(f"{prefix}/delivery-rules", params={"document_id": document.id})
    assert read.status_code == 404, read.text
    stated = client.post(
        f"{prefix}/delivery-rules/proposals",
        json={"party_id": business.customer.id, "rule": "ship_complete", "reason": "x"},
    )
    assert stated.status_code == 404, stated.text
    assert effective_delivery_rule(session, business.tenant.id, document.id)[
        "rule"
    ] == ("partial_allowed")


def test_the_cli_states_after_asking(session, business, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    tenant = business.tenant.id
    document = _order(session, business)
    runner = CliRunner()
    command = [
        "delivery-rule",
        "set",
        "ship_complete",
        "--reason",
        "Asked by phone",
        "--party",
        business.customer.id,
        "--tenant",
        tenant,
    ]

    declined = runner.invoke(cli_module.app, command, input="n\n")
    assert declined.exit_code == 0, declined.output
    assert effective_delivery_rule(session, tenant, document.id)["rule"] == (
        "partial_allowed"
    )
    assert (
        session.scalar(
            select(ChangeProposal.status).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.type == "tool:delivery_rule_set",
            )
        )
        == "rejected"
    )

    stated = runner.invoke(cli_module.app, [*command, "--yes"])
    assert stated.exit_code == 0, stated.output
    session.expire_all()
    assert effective_delivery_rule(session, tenant, document.id)["rule"] == (
        "ship_complete"
    )
    shown = runner.invoke(
        cli_module.app,
        ["delivery-rule", "show", "--order", document.id, "--tenant", tenant],
    )
    assert shown.exit_code == 0, shown.output
    assert json.loads(shown.output)["effective"]["source"] == "customer"
