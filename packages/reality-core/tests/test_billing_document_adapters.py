"""Spec 299 FR-005: down-payment, pro-forma and final invoices and the month-end
lists behind MCP/Chat, Web and CLI, all through the shared services."""

import json
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, Document
from reality.mcp.catalog import MCP_TOOL_REGISTRY, model_tool_schemas
from reality.services import core
from reality.services.finance.accounts import initialize_accounts
from reality.tools.application import approve_and_execute_proposal
from reality.web import api as api_module
from reality.web import app as web_module


def _order(session, business, number="SO-AD"):
    initialize_accounts(session, business.tenant.id)
    _, order, lines, commitments = core.create_manual_order(
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
                "quantity": "10",
                "unit_price": "100",
                "gross_amount": "1000.00",
            }
        ],
        "1000.00",
    )
    return order, lines[0], commitments[0]


def _schema(name):
    return next(
        tool["function"]["parameters"]
        for tool in model_tool_schemas()
        if tool["function"]["name"] == name
    )


def _confirm(session, tenant, proposal_id):
    proposal = session.get(ChangeProposal, (tenant, proposal_id))
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    return approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=token, confirmed=True
    )


def _documents(session, tenant, document_type):
    session.expire_all()
    return list(
        session.scalars(
            select(Document).where(
                Document.tenant_id == tenant, Document.type == document_type
            )
        )
    )


@pytest.mark.parametrize(
    ("name", "required", "optional"),
    [
        (
            "down_payment_invoice_record_propose",
            {"order_id", "number", "gross_amount"},
            {"currency", "effective_at", "net_amount", "tax_amount"},
        ),
        (
            "proforma_invoice_record_propose",
            {"order_id", "number", "gross_amount"},
            {"currency", "document_date", "lines"},
        ),
    ],
)
def test_the_mcp_schemas_are_strict(name, required, optional):
    schema = _schema(name)

    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == required | optional
    assert set(schema["required"]) == required


def test_the_mcp_sales_invoice_schema_states_offsets():
    offsets = _schema("sales_invoice_record_propose")["properties"][
        "down_payment_offsets"
    ]

    assert offsets["items"]["additionalProperties"] is False
    assert set(offsets["items"]["required"]) == {"down_payment_document_id", "amount"}


def test_an_agent_proposes_then_a_person_confirms(session, business):
    tenant = business.tenant.id
    order, line, _ = _order(session, business)

    proposed = MCP_TOOL_REGISTRY["down_payment_invoice_record_propose"].handler(
        session,
        tenant,
        {"order_id": order.id, "number": "AR-AD", "gross_amount": "300.00"},
    )
    # Proposing records nothing.
    assert _documents(session, tenant, "down_payment_invoice") == []
    _confirm(session, tenant, proposed["proposal_id"])
    (down_payment,) = _documents(session, tenant, "down_payment_invoice")

    core.post_customer_payment(
        session, tenant, down_payment.id, "300.00", payment_number="PAY-AD"
    )
    final = MCP_TOOL_REGISTRY["sales_invoice_record_propose"].handler(
        session,
        tenant,
        {
            "order_line_id": line.id,
            "quantity": "10",
            "gross_amount": "1000.00",
            "number": "RE-AD",
            "down_payment_offsets": [
                {"down_payment_document_id": down_payment.id, "amount": "300.00"}
            ],
        },
    )
    _confirm(session, tenant, final["proposal_id"])
    (invoice,) = _documents(session, tenant, "sales_invoice")
    assert core.open_invoice_amount(session, tenant, invoice.id) == Decimal("700.00")

    proforma = MCP_TOOL_REGISTRY["proforma_invoice_record_propose"].handler(
        session,
        tenant,
        {"order_id": order.id, "number": "PF-AD", "gross_amount": "1000.00"},
    )
    _confirm(session, tenant, proforma["proposal_id"])
    assert len(_documents(session, tenant, "proforma_invoice")) == 1


def test_an_agent_reads_the_month_end_lists(session, business):
    tenant = business.tenant.id
    _, line, _ = _order(session, business)
    core.record_sales_invoice(session, tenant, line.id, "5", "500.00", "RE-ME-AD")

    lists = MCP_TOOL_REGISTRY["month_end_billing"].handler(session, tenant, {})

    assert [row["order_line_id"] for row in lists["billed_not_shipped"]] == [line.id]
    assert lists["shipped_not_billed"] == []


def _client(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    return TestClient(web_module.app)


def test_the_web_prepares_and_confirms_and_reads_the_lists(
    session, business, monkeypatch
):
    tenant = business.tenant.id
    order, line, _ = _order(session, business)
    client = _client(session, monkeypatch)
    prefix = f"/api/tenants/{tenant}"

    for tool, arguments in (
        (
            "down_payment_invoice_record",
            {"order_id": order.id, "number": "AR-W", "gross_amount": "300.00"},
        ),
        (
            "proforma_invoice_record",
            {"order_id": order.id, "number": "PF-W", "gross_amount": "1000.00"},
        ),
    ):
        prepared = client.post(
            f"{prefix}/delivery-actions/prepare",
            json={"tool": tool, "request_id": f"web-{tool}", "arguments": arguments},
        )
        assert prepared.status_code == 200, prepared.text
        preview = prepared.json()
        confirmed = client.post(
            f"{prefix}/change-proposals/{preview['id']}/approve",
            json={"confirmed": True, "review_token": preview["review"]["token"]},
        )
        assert confirmed.status_code == 200, confirmed.text
    assert len(_documents(session, tenant, "down_payment_invoice")) == 1
    assert len(_documents(session, tenant, "proforma_invoice")) == 1

    core.record_sales_invoice(session, tenant, line.id, "5", "500.00", "RE-W")
    lists = client.get(f"{prefix}/finance/month-end-billing")
    assert lists.status_code == 200, lists.text
    assert [row["order_line_id"] for row in lists.json()["billed_not_shipped"]] == [
        line.id
    ]


def test_the_web_refuses_another_companys_order(session, business, monkeypatch):
    order, _, _ = _order(session, business)
    other = core.create_tenant(session, "Other GmbH")
    client = _client(session, monkeypatch)

    foreign = client.post(
        f"/api/tenants/{other.id}/delivery-actions/prepare",
        json={
            "tool": "down_payment_invoice_record",
            "request_id": "foreign-dp",
            "arguments": {"order_id": order.id, "number": "X", "gross_amount": "1"},
        },
    )

    assert foreign.status_code == 404, foreign.text
    assert _documents(session, business.tenant.id, "down_payment_invoice") == []
    lists = client.get(f"/api/tenants/{other.id}/finance/month-end-billing")
    assert lists.status_code == 200
    assert lists.json()["billed_not_shipped"] == []


def test_the_cli_proposes_and_reads(session, business, monkeypatch):
    tenant = business.tenant.id
    order, line, _ = _order(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    runner = CliRunner()

    for command, number in (
        ("down-payment-invoice-record-propose", "AR-C"),
        ("proforma-invoice-record-propose", "PF-C"),
    ):
        proposed = runner.invoke(
            cli_module.app,
            [
                command,
                json.dumps(
                    {"order_id": order.id, "number": number, "gross_amount": "100"}
                ),
                f"cli-{number}",
                "--tenant-id",
                tenant,
            ],
        )
        assert proposed.exit_code == 0, proposed.output
        detail = json.loads(proposed.output)
        approve_and_execute_proposal(
            session,
            tenant,
            detail["id"],
            review_token=detail["review"]["token"],
            confirmed=True,
        )
    assert len(_documents(session, tenant, "down_payment_invoice")) == 1
    assert len(_documents(session, tenant, "proforma_invoice")) == 1

    core.record_sales_invoice(session, tenant, line.id, "5", "500.00", "RE-C")
    lists = runner.invoke(cli_module.app, ["month-end-billing", "--tenant-id", tenant])
    assert lists.exit_code == 0, lists.output
    assert [
        row["order_line_id"] for row in json.loads(lists.output)["billed_not_shipped"]
    ] == [line.id]


def test_the_cli_help_lists_the_billing_commands():
    result = CliRunner().invoke(cli_module.app, ["--help"])
    for command in (
        "down-payment-invoice-record-propose",
        "proforma-invoice-record-propose",
        "month-end-billing",
    ):
        assert command in result.output
