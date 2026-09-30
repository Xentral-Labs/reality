"""One credit exposure per customer, derived at read time (spec 298 FR-001).

Open invoices plus open, not yet invoiced orders, minus available credits, in
the customer's own currency. Overdue invoices, payables and other currencies
are named; payables are never subtracted.
"""

from datetime import UTC, datetime
from decimal import Decimal

from reality.services import core
from reality.services.credit_exposure import credit_exposure

AS_OF = datetime(2026, 9, 30, 12, tzinfo=UTC)


def _customer(session, business, limit="1000", name="Limited GmbH"):
    return core.create_party(
        session,
        business.tenant.id,
        name,
        "customer",
        credit_limit=limit,
        default_currency="EUR",
        roles=["customer", "supplier"],
    )


def _invoice(session, business, party, number, amount, day, kind="sales_invoice"):
    document = core.create_document(
        session, business.tenant.id, kind, number, party.id, amount, document_date=day
    )
    if kind == "sales_invoice":
        core.post_sales_invoice(session, business.tenant.id, document.id)
    elif kind == "supplier_invoice":
        core.post_supplier_invoice(session, business.tenant.id, document.id)
    else:
        core.post_sales_credit_note(session, business.tenant.id, document.id)
    return document


def _order(session, business, party, number, quantity, price, currency="EUR"):
    gross = str(Decimal(quantity) * Decimal(price))
    _, document, lines, commitments = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        party.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit_price": price,
                "gross_amount": gross,
            }
        ],
        gross,
        currency=currency,
        document_date="2026-09-20",
    )
    return document, lines[0], commitments[0]


def test_open_invoices_orders_and_credits_make_the_exposure(session, business):
    tenant = business.tenant.id
    party = _customer(session, business)
    _invoice(session, business, party, "RE-X-1", "300.00", "2026-07-01")  # overdue
    _invoice(session, business, party, "RE-X-2", "200.00", "2026-09-30")  # due today
    _order(session, business, party, "SO-X-1", "4", "25.00")  # 100 uninvoiced
    _invoice(session, business, party, "GS-X-1", "50.00", "2026-09-10", "credit_note")
    core.record_customer_payment(
        session,
        tenant,
        party_id=party.id,
        amount="30.00",
        currency="EUR",
        payment_number="PAY-X-1",
        effective_at=AS_OF,
    )
    _invoice(session, business, party, "ER-X-1", "400.00", "2026-09-01", "supplier_invoice")

    exposure = credit_exposure(session, tenant, party.id, as_of=AS_OF)

    assert exposure["open_invoices"]["amount"] == Decimal("500.00")
    assert exposure["open_orders"]["amount"] == Decimal("100.00")
    assert exposure["available_credits"]["amount"] == Decimal("80.00")
    # The payable is named, not netted.
    assert exposure["payables"]["amount"] == Decimal("400.00")
    assert exposure["exposure"] == Decimal("520.00")
    assert [row["number"] for row in exposure["overdue_invoices"]["rows"]] == [
        "RE-X-1"
    ]
    assert exposure["overdue_invoices"]["amount"] == Decimal("300.00")
    assert (exposure["credit_limit"], exposure["over_limit"]) == (
        Decimal("1000.0000"),
        False,
    )


def test_an_order_counts_what_is_not_yet_invoiced_once(session, business):
    tenant = business.tenant.id
    party = _customer(session, business)
    _, line, commitment = _order(session, business, party, "SO-Y-1", "10", "10.00")
    assert credit_exposure(session, tenant, party.id, as_of=AS_OF)["open_orders"][
        "amount"
    ] == Decimal("100.00")

    # Four are invoiced: the invoice counts them, the order the other six.
    core.record_sales_invoice(
        session,
        tenant,
        order_line_id=line.id,
        quantity="4",
        gross_amount="40.00",
        number="RE-Y-1",
        effective_at=AS_OF,
    )
    exposure = credit_exposure(session, tenant, party.id, as_of=AS_OF)
    assert (exposure["open_invoices"]["amount"], exposure["open_orders"]["amount"]) == (
        Decimal("40.00"),
        Decimal("60.00"),
    )

    # Revised down to 7, then the rest cancelled: nothing uninvoiced remains.
    core.revise_commitment(session, tenant, commitment.id, quantity="7", note="Less")
    assert credit_exposure(session, tenant, party.id, as_of=AS_OF)["open_orders"][
        "amount"
    ] == Decimal("30.00")
    core.cancel_commitment(session, tenant, commitment.id, reason="Customer cancelled")
    assert credit_exposure(session, tenant, party.id, as_of=AS_OF)["open_orders"][
        "amount"
    ] == Decimal("0")


def test_another_currency_is_named_not_counted(session, business):
    tenant = business.tenant.id
    party = _customer(session, business)
    order, _, _ = _order(session, business, party, "SO-USD-1", "2", "50.00", "USD")

    exposure = credit_exposure(session, tenant, party.id, as_of=AS_OF)

    assert exposure["exposure"] == 0
    assert [row["document_id"] for row in exposure["not_counted"]] == [order.id]


def test_an_unpriced_shop_line_counts_nothing_and_is_named(session, business):
    tenant = business.tenant.id
    party = _customer(session, business)
    _, job = core.enqueue_shopify_order(
        session,
        tenant,
        {
            "id": 9801,
            "name": "#9801",
            "currency": "EUR",
            "total_price": "20.00",
            "created_at": "2026-09-20T10:00:00Z",
            "updated_at": "2026-09-20T10:00:00Z",
            "line_items": [
                {"id": 1, "sku": business.item.sku, "quantity": 2, "price": "10.00"},
                {"id": 2, "sku": business.item.sku, "quantity": 1},
            ],
        },
        business.company.id,
        party.id,
        business.location.id,
    )
    core.process_import_job(session, tenant, job.id)

    orders = credit_exposure(session, tenant, party.id, as_of=AS_OF)["open_orders"]

    assert orders["amount"] == Decimal("20.00")
    assert [row["uninvoiced_quantity"] for row in orders["unpriced"]] == [Decimal(1)]


def test_an_exposure_past_the_limit_is_over_it(session, business):
    tenant = business.tenant.id
    party = _customer(session, business, limit="100")
    _invoice(session, business, party, "RE-Z-1", "100.00", "2026-09-25")
    # The agreed number is allowed; only past it is over.
    assert credit_exposure(session, tenant, party.id, as_of=AS_OF)["over_limit"] is False

    _order(session, business, party, "SO-Z-1", "1", "0.01")

    exposure = credit_exposure(session, tenant, party.id, as_of=AS_OF)
    assert (exposure["over_limit"], exposure["excess"]) == (True, Decimal("0.01"))


def test_the_exposure_is_tenant_scoped(session, business):
    import pytest

    party = _customer(session, business)
    _invoice(session, business, party, "RE-T-1", "300.00", "2026-09-25")
    other = core.create_tenant(session, "Other Company")
    # Positive control: the owning company reads it.
    assert credit_exposure(session, business.tenant.id, party.id, as_of=AS_OF)[
        "open_invoices"
    ]["amount"] == Decimal("300.00")

    with pytest.raises(core.NotFound):
        credit_exposure(session, other.id, party.id, as_of=AS_OF)
