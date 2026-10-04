"""Spec 297 FR-004: one returned-payment command behind Web, MCP/Chat and CLI."""

import json

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import PaymentReturn
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _paid(session, business, number="RE-297-A"):
    tenant = business.tenant.id
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        number,
        business.customer.id,
        "100",
        document_date="2026-09-01",
    )
    core.post_sales_invoice(session, tenant, invoice.id)
    entry = core.post_customer_payment(
        session, tenant, invoice.id, "100", payment_number=f"PAY-{number}"
    )[0]
    return invoice, entry.document_id


def _arguments(payment_id):
    return {
        "payment_document_id": payment_id,
        "kind": "chargeback",
        "returned_on": "2026-10-02",
        "reason": "Card not present fraud",
        "reference": "dp_1",
    }


def _returns(session):
    return session.scalar(select(func.count()).select_from(PaymentReturn))


def test_the_mcp_schema_is_strict_and_names_its_fields():
    schema = next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == "finance_payment_return_propose"
    )
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {
        "payment_document_id",
        "kind",
        "returned_on",
        "reason",
        "reference",
        "fee_amount",
        "fee_bearer",
    }
    assert set(schema["required"]) == {
        "payment_document_id",
        "kind",
        "returned_on",
        "reason",
    }


def test_an_agent_proposes_and_a_person_confirms_the_return(session, business):
    tenant = business.tenant.id
    invoice, payment = _paid(session, business)

    proposed = MCP_TOOL_REGISTRY["finance_payment_return_propose"].handler(
        session, tenant, _arguments(payment)
    )
    assert proposed["next_step"]["required_principal"] == "authenticated_active_owner"
    assert _returns(session) == 0
    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )

    listed = MCP_TOOL_REGISTRY["finance_payment_returns"].handler(session, tenant, {})
    (row,) = listed
    detail = MCP_TOOL_REGISTRY["finance_payment_return"].handler(
        session, tenant, {"return_id": row["id"]}
    )
    assert detail["reopened"][0]["invoice_id"] == invoice.id
    assert core.open_invoice_amount(session, tenant, invoice.id) == 100


def test_the_web_proposes_and_reads_a_return(session, business, monkeypatch):
    tenant = business.tenant.id
    invoice, payment = _paid(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)
    prefix = f"/api/tenants/{tenant}"

    prepared = client.post(
        f"{prefix}/finance/commercial/proposals",
        json={"tool": "finance.payment.return", "arguments": _arguments(payment)},
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["preview"]["payment_return"]["reopened"][0][
        "invoice_id"
    ] == (invoice.id)
    approve_and_execute_proposal(session, tenant, prepared.json()["id"], confirmed=True)

    listed = client.get(f"{prefix}/finance/payment-returns")
    assert listed.status_code == 200, listed.text
    (row,) = listed.json()["items"]
    detail = client.get(f"{prefix}/finance/payment-returns/{row['id']}")
    assert detail.json()["kind"] == "chargeback"

    other = core.create_tenant(session, "Other GmbH")
    foreign = client.get(f"/api/tenants/{other.id}/finance/payment-returns/{row['id']}")
    assert foreign.status_code == 404, foreign.text


def test_the_cli_proposes_and_reads_a_return(session, business, monkeypatch):
    tenant = business.tenant.id
    _, payment = _paid(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    runner = CliRunner()

    proposed = runner.invoke(
        cli_module.app,
        [
            "finance-payment-return-propose",
            json.dumps(_arguments(payment)),
            "--tenant-id",
            tenant,
        ],
    )
    assert proposed.exit_code == 0, proposed.output
    assert _returns(session) == 0
    approve_and_execute_proposal(
        session, tenant, json.loads(proposed.output)["id"], confirmed=True
    )

    listed = runner.invoke(
        cli_module.app, ["finance-payment-returns", "--tenant-id", tenant]
    )
    assert listed.exit_code == 0, listed.output
    assert len(json.loads(listed.output)) == 1


def test_the_cli_help_lists_the_return_commands():
    result = CliRunner().invoke(cli_module.app, ["--help"])
    for command in ("finance-payment-return-propose", "finance-payment-returns"):
        assert command in result.output
