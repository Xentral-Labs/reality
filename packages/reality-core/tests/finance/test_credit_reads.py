"""Feature 169: available credit and payments are public business reads for agents."""

from decimal import Decimal

from reality.mcp.catalog import MCP_TOOL_NAMES
from reality.services import core
from reality.tools.application import run_read_tool


def _overpaid_invoice(session, business):
    tenant = business.tenant.id
    invoice = core.create_document(
        session, tenant, "sales_invoice", "INV-CREDIT", business.customer.id, "100"
    )
    core.post_sales_invoice(session, tenant, invoice.id)
    entries = core.record_customer_payment(
        session, tenant, business.customer.id, "120", payment_number="PAY-120"
    )
    receivable = next(e for e in entries if e.account == "accounts_receivable")
    core.allocate_settlement(
        session,
        tenant,
        receivable.id,
        core._settlement_control_entry(session, tenant, invoice.id).id,
        "100",
    )
    return invoice, entries[0].document_id


def test_available_credit_and_payments_are_readable(session, business):
    tenant = business.tenant.id
    invoice, payment_id = _overpaid_invoice(session, business)
    assert {"finance_credits", "finance_payments"} <= MCP_TOOL_NAMES

    credits = run_read_tool(
        session, tenant, "finance.credits.list", {"side": "customer"}
    )
    row = next(item for item in credits["items"] if item["document_id"] == payment_id)
    assert row["number"] == "PAY-120"
    assert (row["original"], row["used"], row["available"]) == (
        "120.0000",
        "100.0000",
        "20.0000",
    )
    assert row["party"] == business.customer.name
    assert (
        run_read_tool(session, tenant, "finance.credits.list", {"side": "supplier"})[
            "items"
        ]
        == []
    )

    payments = run_read_tool(
        session, tenant, "finance.payments.list", {"only_unallocated": True}
    )
    assert [item["payment_id"] for item in payments["items"]] == [payment_id]
    item = payments["items"][0]
    assert item["direction"] == "incoming"
    assert (item["amount"], item["allocated"], item["unallocated"]) == (
        "120.0000",
        "100.0000",
        "20.0000",
    )
    assert item["state"] == "partially_allocated"
    assert Decimal(item["unallocated"]) == Decimal(20)
    assert (
        run_read_tool(
            session, tenant, "finance.payments.list", {"direction": "outgoing"}
        )["items"]
        == []
    )
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0


def test_credit_reads_are_tenant_scoped(session, business):
    tenant = business.tenant.id
    _overpaid_invoice(session, business)
    other = core.create_tenant(session, "Other Trading")
    assert (
        run_read_tool(session, other.id, "finance.credits.list", {"side": "customer"})[
            "items"
        ]
        == []
    )
    assert run_read_tool(session, other.id, "finance.payments.list", {})["items"] == []
    assert run_read_tool(session, tenant, "finance.credits.list", {"side": "customer"})[
        "items"
    ]
