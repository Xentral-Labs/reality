"""Spec 348: stock reserved for an order whose prepayment has not arrived."""

from datetime import timedelta
from decimal import Decimal

from intake_review_support import (
    reviewed_cancel_commitment,
    reviewed_create_payment_term,
    reviewed_manual_document_with_lines,
    reviewed_post_customer_payment,
    reviewed_record_sales_invoice,
    reviewed_release_reservation,
    reviewed_reserve,
)
from sqlalchemy import select

from reality.db.core import Reservation
from reality.services import core
from reality.services.exceptions import operational_exceptions

CLASS = "reservation_awaiting_prepayment"


def _terms(session, business):
    tenant = business.tenant.id
    reviewed_create_payment_term(session, tenant, "NET14", "Net 14", 14)
    reviewed_create_payment_term(
        session, tenant, "PREPAY", "Pay before dispatch", 0, requires_prepayment=True
    )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "50",
        to_location_id=business.location.id,
    )


def _order(session, business, number, term, *, reserve=True):
    tenant = business.tenant.id
    document, lines = reviewed_manual_document_with_lines(
        session,
        tenant,
        "sales_order",
        number,
        business.customer.id,
        [
            {
                "sku": business.item.sku,
                "item_id": business.item.id,
                "quantity": "10",
                "unit_price": "10",
                "gross_amount": "100",
            }
        ],
        "100",
        payment_term_code=term,
    )
    commitment = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "10",
        None,
        amount="100",
        document_id=document.id,
        document_line_id=lines[0].id,
    )
    if reserve:
        reviewed_reserve(session, tenant, commitment.id)
    return document, lines[0], commitment


def _invoice(session, business, line, number):
    receipt = reviewed_record_sales_invoice(
        session, business.tenant.id, line.id, "10", "100", number
    )
    return next(row["id"] for row in receipt["records"] if row["family"] == "document")


def _findings(session, business, days=8):
    as_of = core.now() + timedelta(days=days)
    return {
        row.record_id: row
        for row in operational_exceptions(session, business.tenant.id, as_of=as_of)
        if row.class_id == CLASS
    }


def test_stock_reserved_for_an_unpaid_prepayment_is_reported_after_a_week(
    session, business
):
    _terms(session, business)
    _, line, waiting = _order(session, business, "SO-PRE-1", "PREPAY")
    _invoice(session, business, line, "INV-PRE-1")
    # Positive controls: an ordinary order and an unreserved prepayment order.
    _order(session, business, "SO-NET-1", "NET14")
    _, _, unreserved = _order(session, business, "SO-PRE-2", "PREPAY", reserve=False)

    # Inside the week nothing is reported yet.
    assert waiting.id not in _findings(session, business, days=6)

    findings = _findings(session, business)
    assert set(findings) == {waiting.id}
    finding = findings[waiting.id]
    assert finding.causal_values["reserved_quantity"] == Decimal(10)
    assert finding.causal_values["unpaid_amount"] == Decimal(100)
    assert finding.causal_values["waiting_days"] == 8
    assert finding.causal_values["threshold_days"] == 7
    assert "for order SO-PRE-1" in finding.impact
    assert unreserved.id not in findings
    # Nothing was released by the read.
    assert (
        session.scalar(
            select(Reservation.status).where(Reservation.commitment_id == waiting.id)
        )
        == "active"
    )


def test_payment_release_or_cancellation_clears_it(session, business):
    tenant = business.tenant.id
    _terms(session, business)
    _, paid_line, paid = _order(session, business, "SO-PRE-PAID", "PREPAY")
    paid_invoice = _invoice(session, business, paid_line, "INV-PRE-PAID")
    _, released_line, released = _order(session, business, "SO-PRE-REL", "PREPAY")
    _invoice(session, business, released_line, "INV-PRE-REL")
    _, cancelled_line, cancelled = _order(session, business, "SO-PRE-CAN", "PREPAY")
    _invoice(session, business, cancelled_line, "INV-PRE-CAN")
    assert {paid.id, released.id, cancelled.id} <= set(_findings(session, business))

    reviewed_post_customer_payment(session, tenant, paid_invoice, "100")
    reservation = session.scalar(
        select(Reservation).where(Reservation.commitment_id == released.id)
    )
    reviewed_release_reservation(session, tenant, reservation.id)
    reviewed_cancel_commitment(session, tenant, cancelled.id, reason="Customer withdrew")

    assert not {paid.id, released.id, cancelled.id} & set(_findings(session, business))


def test_a_part_payment_still_waits_and_names_what_is_unpaid(session, business):
    tenant = business.tenant.id
    _terms(session, business)
    _, line, waiting = _order(session, business, "SO-PRE-PART", "PREPAY")
    invoice = _invoice(session, business, line, "INV-PRE-PART")

    reviewed_post_customer_payment(session, tenant, invoice, "80")

    finding = _findings(session, business)[waiting.id]
    assert finding.causal_values["unpaid_amount"] == Decimal(20)


def test_another_company_sees_nothing(session, business):
    _terms(session, business)
    _, line, waiting = _order(session, business, "SO-PRE-ISO", "PREPAY")
    _invoice(session, business, line, "INV-PRE-ISO")
    other = core.create_tenant(session, "Other GmbH")

    assert waiting.id in _findings(session, business)
    assert not [
        row
        for row in operational_exceptions(
            session, other.id, as_of=core.now() + timedelta(days=8)
        )
        if row.class_id == CLASS
    ]
