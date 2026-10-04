"""Spec 309 FR-003: the company currency and foreign payments through MCP, Web and CLI."""

import json
from decimal import Decimal

from fastapi.testclient import TestClient
from intake_review_support import reviewed_record_free_supplier_invoice
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, LedgerEntry
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.mcp.server import _reject_unknown_fields
from reality.services import core
from reality.services.finance.company_currency import company_currency
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _client(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    return TestClient(web_module.app)


def _usd_invoice(session, business):

    receipt = reviewed_record_free_supplier_invoice(
        session,
        business.tenant.id,
        supplier_id=business.supplier.id,
        number="USD-ADAPTER",
        currency="USD",
        gross_amount="100",
        lines=[
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit_price": "10",
                "gross_amount": "100",
            }
        ],
        exchange_rate="0.9",
    )
    return next(row["id"] for row in receipt["records"] if row["family"] == "document")


def test_the_mcp_schemas_take_the_rate_and_the_paid_amount():
    for name, field in (
        ("supplier_invoice_post_propose", "exchange_rate"),
        ("supplier_invoice_record_propose", "exchange_rate"),
        ("supplier_invoice_free_record_propose", "exchange_rate"),
        ("supplier_payment_post_propose", "paid_amount"),
    ):
        schema = MCP_TOOL_REGISTRY[name].input_schema
        assert field in schema["properties"], name
        assert field not in schema.get("required", []), name
    schema = MCP_TOOL_REGISTRY["company_currency_set_propose"].input_schema
    assert (schema["additionalProperties"], schema["required"]) == (False, ["currency"])


def test_an_agent_states_the_company_currency_and_a_person_confirms(session, business):
    tenant = business.tenant.id
    proposed = MCP_TOOL_REGISTRY["company_currency_set_propose"].handler(
        session, tenant, {"currency": "chf"}
    )
    assert proposed["preview"]["company_currency"] == {
        "current": "EUR",
        "proposed": "CHF",
    }
    assert company_currency(session, tenant) == "EUR"

    approve_and_execute_proposal(
        session, tenant, proposed["proposal_id"], confirmed=True
    )

    read = MCP_TOOL_REGISTRY["company_currency"].handler(session, tenant, {})
    assert (read["currency"], read["has_postings"]) == ("CHF", False)


def test_an_agent_pays_a_usd_invoice_in_eur(session, business):
    tenant = business.tenant.id
    account = reviewed_create_account(
        session, tenant, code="7100", name="Kursdifferenzen", role="exchange_difference"
    )
    reviewed_set_default_account(
        session, tenant, role="exchange_difference", account_id=account["id"]
    )
    invoice = _usd_invoice(session, business)
    arguments = {"invoice_id": invoice, "amount": "100", "paid_amount": "88.50"}
    definition = MCP_TOOL_REGISTRY["supplier_payment_post_propose"]
    _reject_unknown_fields(definition.input_schema, arguments)

    proposed = definition.handler(session, tenant, arguments)

    exchange = proposed["preview"]["state"]["exchange"]
    assert (exchange["kind"], Decimal(exchange["difference"])) == (
        "gain",
        Decimal("1.5"),
    )


def test_the_web_reads_and_states_the_company_currency(session, business, monkeypatch):
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{business.tenant.id}"
    assert client.get(f"{prefix}/finance/company-currency").json()["currency"] == "EUR"

    prepared = client.post(
        f"{prefix}/finance/company-currency/proposals", json={"currency": "GBP"}
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["preview"]["company_currency"]["proposed"] == "GBP"
    confirmed = client.post(
        f"{prefix}/change-proposals/{prepared.json()['id']}/approve",
        json={"confirmed": True},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert client.get(f"{prefix}/finance/company-currency").json()["currency"] == "GBP"

    refused = client.post(
        f"{prefix}/finance/company-currency/proposals", json={"currency": "G"}
    )
    assert "company_currency_invalid" in refused.text


def test_the_web_pays_a_usd_invoice_in_eur(session, business, monkeypatch):
    tenant = business.tenant.id
    account = reviewed_create_account(
        session, tenant, code="7100", name="Kursdifferenzen", role="exchange_difference"
    )
    reviewed_set_default_account(
        session, tenant, role="exchange_difference", account_id=account["id"]
    )
    invoice = _usd_invoice(session, business)
    client = _client(session, monkeypatch)

    paid = client.post(
        f"/api/tenants/{tenant}/finance/supplier-payments",
        json={"confirmed": True, "invoice_id": invoice, "amount": "100", "paid_amount": "91.00"},
    )

    assert paid.status_code == 201, paid.text
    entries = session.scalars(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant,
            LedgerEntry.id.in_(paid.json()["ledger_entry_ids"]),
        )
    ).all()
    loss = next(entry for entry in entries if entry.account == "exchange_difference")
    assert (loss.debit_credit, loss.company_amount) == ("debit", Decimal("1.00"))


def test_another_company_cannot_state_or_read_the_currency(
    session, business, monkeypatch
):
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)
    # Positive control: the company's own read answers.
    assert (
        client.get(
            f"/api/tenants/{business.tenant.id}/finance/company-currency"
        ).status_code
        == 200
    )

    missing = client.get("/api/tenants/ten_missing/finance/company-currency")
    assert missing.status_code == 404, missing.text
    client.post(
        f"/api/tenants/{other.id}/finance/company-currency/proposals",
        json={"currency": "USD"},
    )
    assert company_currency(session, business.tenant.id) == "EUR"


def test_the_cli_shows_and_states_after_asking(session, business, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    tenant = business.tenant.id
    runner = CliRunner()
    command = ["finance", "company-currency", "set", "CHF", "--tenant", tenant]

    declined = runner.invoke(cli_module.app, command, input="n\n")
    assert declined.exit_code == 0, declined.output
    assert company_currency(session, tenant) == "EUR"
    assert (
        session.scalar(
            select(ChangeProposal.status).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.type == "tool:company_currency_set",
            )
        )
        == "rejected"
    )
    stated = runner.invoke(cli_module.app, [*command, "--yes"])
    assert stated.exit_code == 0, stated.output
    shown = runner.invoke(
        cli_module.app, ["finance", "company-currency", "show", "--tenant", tenant]
    )
    assert json.loads(shown.output)["currency"] == "CHF"


from intake_review_support import reviewed_create_account, reviewed_set_default_account
