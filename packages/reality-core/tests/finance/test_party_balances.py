"""Feature 170: one row per party and currency with open, overdue, credit and balance."""

from datetime import UTC, datetime
from decimal import Decimal

from reality.mcp.catalog import MCP_TOOL_NAMES
from reality.services import core
from reality.services.finance.balances import party_balances
from reality.tools.application import run_read_tool

AS_OF = datetime(2026, 9, 1, 12, tzinfo=UTC)


def _invoice(
    session,
    business,
    number,
    amount,
    *,
    party=None,
    currency="EUR",
    date="2026-08-01",
    term="",
):
    document = core.create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        number,
        party or business.customer.id,
        amount,
        currency=currency,
        document_date=date,
        payment_term_code=term,
    )
    core.post_sales_invoice(session, business.tenant.id, document.id)
    return document


def _pay(session, business, invoice, paid, allocate, *, party=None, number=None):
    tenant = business.tenant.id
    entries = core.record_customer_payment(
        session, tenant, party or business.customer.id, paid, payment_number=number
    )
    receivable = next(e for e in entries if e.account == "accounts_receivable")
    core.allocate_settlement(
        session,
        tenant,
        receivable.id,
        core._settlement_control_entry(session, tenant, invoice.id).id,
        allocate,
    )
    return receivable


def _rows(result, currency=None):
    return [r for r in result["items"] if currency is None or r["currency"] == currency]


def test_party_rows_sum_open_items_and_credits(session, business):
    tenant = business.tenant.id
    paid = _invoice(session, business, "INV-A", "100")
    _pay(session, business, paid, "100", "100", number="PAY-A")
    partial = _invoice(session, business, "INV-B", "200")
    _pay(session, business, partial, "50", "50", number="PAY-B")
    over = _invoice(session, business, "INV-C", "300")
    _pay(session, business, over, "320", "300", number="PAY-C")
    note = core.create_document(
        session, tenant, "credit_note", "CN-1", business.customer.id, "40"
    )
    core.post_sales_credit_note(session, tenant, note.id)
    _invoice(session, business, "INV-USD", "500", currency="USD")
    other = core.create_party(session, tenant, "Zweit GmbH", "customer")
    settled = _invoice(session, business, "INV-Z", "70", party=other.id)
    _pay(session, business, settled, "70", "70", party=other.id, number="PAY-Z")

    result = party_balances(session, tenant, side="customer", as_of=AS_OF)
    assert {r["party"] for r in result["items"]} == {business.customer.name}
    eur = _rows(result, "EUR")[0]
    assert (eur["open"], eur["credit"], eur["balance"]) == (
        "150.0000",
        "60.0000",
        "90.0000",
    )
    assert (eur["open_count"], eur["credit_count"]) == (1, 2)
    assert eur["oldest_due_date"] == "2026-08-01"
    usd = _rows(result, "USD")[0]
    assert (usd["open"], usd["credit"], usd["balance"]) == ("500.0000", "0", "500.0000")
    assert {t["currency"] for t in result["totals"]} == {"EUR", "USD"}
    assert party_balances(session, tenant, side="supplier", as_of=AS_OF)["items"] == []


def test_overdue_follows_original_due_date_and_as_of(session, business):
    tenant = business.tenant.id
    core.create_payment_term(session, tenant, "NET14", "Net 14", 14)
    _invoice(session, business, "INV-DUE", "100", date="2026-08-01", term="NET14")
    _invoice(session, business, "INV-NODATE", "30", date="")

    early = party_balances(
        session, tenant, side="customer", as_of=datetime(2026, 8, 10, tzinfo=UTC)
    )
    row = early["items"][0]
    assert (row["open"], row["overdue"]) == ("130.0000", "0")
    assert row["oldest_due_date"] == "2026-08-15"

    late = party_balances(session, tenant, side="customer", as_of=AS_OF)["items"][0]
    assert (late["open"], late["overdue"]) == ("130.0000", "100.0000")
    assert late["open_count"] == 2


def test_credit_only_lists_each_party_once(session, business):
    tenant = business.tenant.id
    one = _invoice(session, business, "INV-1", "100")
    _pay(session, business, one, "110", "100", number="PAY-1")
    two = _invoice(session, business, "INV-2", "100")
    receivable = _pay(session, business, two, "125", "100", number="PAY-2")
    note = core.create_document(
        session, tenant, "credit_note", "CN-2", business.customer.id, "15"
    )
    core.post_sales_credit_note(session, tenant, note.id)
    other = core.create_party(session, tenant, "Nur Offen GmbH", "customer")
    _invoice(session, business, "INV-O", "80", party=other.id)

    result = party_balances(
        session, tenant, side="customer", as_of=AS_OF, credit_only=True
    )
    assert [r["party"] for r in result["items"]] == [business.customer.name]
    assert (result["items"][0]["credit"], result["items"][0]["credit_count"]) == (
        "50.0000",
        3,
    )
    assert (
        len(party_balances(session, tenant, side="customer", as_of=AS_OF)["items"]) == 2
    )

    three = _invoice(session, business, "INV-3", "25")
    core.allocate_settlement(
        session,
        tenant,
        receivable.id,
        core._settlement_control_entry(session, tenant, three.id).id,
        "25",
    )
    after = party_balances(
        session, tenant, side="customer", as_of=AS_OF, credit_only=True
    )["items"][0]
    assert (after["credit"], after["credit_count"]) == ("25.0000", 2)


def test_tool_matches_view_and_is_tenant_scoped(session, business):
    tenant = business.tenant.id
    over = _invoice(session, business, "INV-T", "100")
    _pay(session, business, over, "120", "100", number="PAY-T")
    assert "finance_party_balances" in MCP_TOOL_NAMES

    view = party_balances(session, tenant, side="customer")["items"]
    tool = run_read_tool(
        session, tenant, "finance.party_balances.list", {"side": "customer"}
    )
    assert tool["items"] == view
    assert tool["count"] == 1
    assert Decimal(tool["items"][0]["credit"]) == Decimal(20)
    assert tool["items"][0]["balance"] == "-20.0000"

    other = core.create_tenant(session, "Other Trading")
    assert (
        run_read_tool(
            session, other.id, "finance.party_balances.list", {"side": "customer"}
        )["items"]
        == []
    )
    supplier = run_read_tool(
        session, tenant, "finance.party_balances.list", {"side": "supplier"}
    )
    assert supplier["items"] == []
