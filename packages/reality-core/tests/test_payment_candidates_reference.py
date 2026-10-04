"""A payment's stated reference makes a candidate once it names one invoice (spec 314 FR-005).

The payment arrives before its order. Once the order is invoiced, the invoice
the reference now names is offered, also when the amount differs; allocating
stays a person's decision.
"""

from datetime import UTC, datetime
from decimal import Decimal

from intake_review_support import (
    accept_normalized_payment,
    reviewed_manual_order,
    reviewed_record_sales_invoice,
)

from reality.services import core, payment_intake
from reality.services.payment_intake import NormalisedPayment, Reference

AT = datetime(2026, 9, 10, 8, tzinfo=UTC)


def _order(session, business, number, quantity="4"):
    _, _, lines, _ = reviewed_manual_order(
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
                "quantity": quantity,
                "unit_price": "25.00",
                "gross_amount": str(Decimal(quantity) * 25),
            }
        ],
        str(Decimal(quantity) * 25),
    )
    return lines[0]


def _invoice(session, business, line, quantity, number):
    return reviewed_record_sales_invoice(
        session,
        business.tenant.id,
        lines=[
            {
                "order_line_id": line.id,
                "quantity": quantity,
                "gross_amount": str(Decimal(quantity) * 25),
            }
        ],
        gross_amount=str(Decimal(quantity) * 25),
        number=number,
        effective_at=AT,
    )


def _payment(session, business, external_id, amount, order_number):
    source, _ = core.enqueue_source(
        session,
        business.tenant.id,
        "bank_statement",
        "payment",
        external_id,
        {"references": [{"type": "shop_order_number", "value": order_number}]},
    )
    _, payment, _, allocation, resolution = accept_normalized_payment(
        session,
        business.tenant.id,
        source,
        NormalisedPayment(
            party_id=business.customer.id,
            amount=Decimal(amount),
            currency="EUR",
            effective_at=AT,
            external_payment_id=external_id,
            references=(Reference(type="shop_order_number", value=order_number),),
            remittance_text="",
        ),
    )
    return payment, allocation, resolution


def _candidates(session, business, payment):
    return [
        (candidate.number, candidate.reasons)
        for candidate in payment_intake.payment_candidates(
            session, business.tenant.id, payment.id
        )
    ]


def test_a_payment_before_its_order_is_offered_the_invoice_its_reference_names(
    session, business
):
    payment, allocation, resolution = _payment(
        session, business, "stmt-314:1", "95.00", "SO-P02"
    )
    assert allocation is None
    assert resolution.reasons == ("no order SO-P02 for this customer",)
    assert _candidates(session, business, payment) == []

    line = _order(session, business, "SO-P02")
    _invoice(session, business, line, "4", "RE-P02")

    # 95 is not the open 100, so only the stated reference can name the invoice.
    assert _candidates(session, business, payment) == [
        ("RE-P02", ("stated reference names this invoice",))
    ]
    assert payment_intake.unallocated_amount(
        session, business.tenant.id, payment.id
    ) == Decimal("95.0000")


def test_a_reference_naming_several_invoices_keeps_saying_so(session, business):
    payment, _, _ = _payment(session, business, "stmt-314:2", "40.00", "SO-P02-B")
    line = _order(session, business, "SO-P02-B")
    _invoice(session, business, line, "2", "RE-P02-B1")
    _invoice(session, business, line, "2", "RE-P02-B2")

    assert _candidates(session, business, payment) == [
        ("RE-P02-B1", ("stated reference names this invoice among others",)),
        ("RE-P02-B2", ("stated reference names this invoice among others",)),
    ]
