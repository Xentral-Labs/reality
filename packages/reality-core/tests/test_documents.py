from decimal import Decimal

import pytest

from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_manual_document_with_lines,
    create_party,
    create_tenant,
)


def line(quantity="2", unit_price="10", gross_amount="20.00"):
    return {
        "quantity": quantity,
        "unit": "pcs",
        "unit_price": unit_price,
        "gross_amount": gross_amount,
    }


def record(session, business, number, lines, gross_amount):
    return create_manual_document_with_lines(
        session,
        business.tenant.id,
        "supplier_invoice",
        number,
        business.supplier.id,
        lines,
        gross_amount=gross_amount,
    )


def test_recording_requires_a_stated_total(session, business):
    # Omitting the total entirely is a signature error and unreachable from a
    # caller. What an interface can still send is an empty one.
    with pytest.raises(InvalidOperation, match="total"):
        record(session, business, "ER-1", [line()], "")

    # And the same for a line that states no amount of its own.
    with pytest.raises(InvalidOperation, match="amount"):
        record(
            session,
            business,
            "ER-2",
            [{"quantity": "2", "unit": "pcs", "unit_price": "10"}],
            "20.00",
        )


def test_stated_amounts_are_stored_verbatim(session, business):
    document, lines = record(
        session,
        business,
        "ER-3",
        [line(gross_amount="19.99"), line(quantity="1", gross_amount="9.99")],
        "29.98",
    )

    assert document.gross_amount == Decimal("29.98")
    assert [row.gross_amount for row in lines] == [
        Decimal("19.99"),
        Decimal("9.99"),
    ]


def test_total_may_differ_from_the_lines(session, business):
    # The paper says something else than the lines add up to. That difference is
    # the finding, so it is kept rather than corrected or refused.
    document, lines = record(
        session, business, "ER-4", [line(), line()], "39.95"
    )

    assert document.gross_amount == Decimal("39.95")
    assert sum(row.gross_amount for row in lines) == Decimal("40.00")


def test_line_amount_may_differ_from_quantity_times_price(session, business):
    # A rebate or a rounding convention on the source produces exactly this.
    _, lines = record(
        session,
        business,
        "ER-5",
        [line(quantity="3", unit_price="10", gross_amount="28.50")],
        "28.50",
    )

    assert lines[0].gross_amount == Decimal("28.50")
    assert lines[0].quantity * lines[0].unit_price == Decimal("30.00")


def test_zero_amounts_are_statements(session, business):
    document, lines = record(
        session,
        business,
        "ER-6",
        [line(gross_amount="0")],
        "0",
    )

    assert document.gross_amount == Decimal(0)
    assert lines[0].gross_amount == Decimal(0)


def order_line(session, business, *, direction="sales", number="SO-LINK-1"):
    """One order line to bill against, recorded the way a typed-in order is."""
    document_type = "sales_order" if direction == "sales" else "purchase_order"
    party = business.customer if direction == "sales" else business.supplier
    _, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        document_type,
        number,
        party.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit": "pcs",
                "unit_price": "9.00",
                "gross_amount": "90.00",
            }
        ],
        "90.00",
    )
    return lines[0]


def invoice_line(
    session,
    business,
    *,
    billed_id,
    direction="sales",
    number="RE-LINK-1",
    quantity="4",
):
    document_type = "sales_invoice" if direction == "sales" else "supplier_invoice"
    party = business.customer if direction == "sales" else business.supplier
    return create_manual_document_with_lines(
        session,
        business.tenant.id,
        document_type,
        number,
        party.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit": "pcs",
                "unit_price": "9.00",
                "gross_amount": "36.00",
                "billed_document_line_id": billed_id,
            }
        ],
        "36.00",
    )


def test_invoice_line_records_the_order_line_it_bills(session, business):
    agreed = order_line(session, business)

    _, billed = invoice_line(session, business, billed_id=agreed.id)

    assert billed[0].billed_document_line_id == agreed.id

    # A line that bills nothing from an order says so by holding no reference,
    # which is a statement and not a gap.
    _, freight = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_invoice",
        "RE-LINK-FREIGHT",
        business.customer.id,
        [
            {
                "description": "Freight",
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "12.00",
                "gross_amount": "12.00",
            }
        ],
        "12.00",
    )
    assert freight[0].billed_document_line_id is None


def test_invoice_line_reference_is_validated(session, business):
    agreed = order_line(session, business)

    # Another tenant's line is not reachable at all.
    foreign = create_tenant(session, "Foreign billing tenant")
    stranger = create_party(session, foreign.id, "Stranger GmbH", "customer")
    with pytest.raises(NotFound):
        create_manual_document_with_lines(
            session,
            foreign.id,
            "sales_invoice",
            "RE-FOREIGN",
            stranger.id,
            [
                {
                    "quantity": "1",
                    "unit": "pcs",
                    "unit_price": "9.00",
                    "gross_amount": "9.00",
                    "billed_document_line_id": agreed.id,
                }
            ],
            "9.00",
        )

    # A line that is not on an order promises nothing to bill against.
    _, invoice = invoice_line(session, business, billed_id=agreed.id, number="RE-A")
    with pytest.raises(InvalidOperation, match="order line"):
        invoice_line(
            session, business, billed_id=invoice[0].id, number="RE-ON-AN-INVOICE"
        )

    # A sales invoice may not bill a purchase order line, or the reverse.
    purchase = order_line(
        session, business, direction="purchase", number="PO-LINK-1"
    )
    with pytest.raises(InvalidOperation, match="side"):
        invoice_line(
            session, business, billed_id=purchase.id, number="RE-WRONG-SIDE"
        )
    with pytest.raises(InvalidOperation, match="side"):
        invoice_line(
            session,
            business,
            billed_id=agreed.id,
            direction="purchase",
            number="ER-WRONG-SIDE",
        )
