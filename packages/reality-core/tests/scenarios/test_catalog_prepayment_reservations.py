"""Business journey B12: a reservation waits for a prepayment that does not come."""

from datetime import timedelta
from decimal import Decimal

from conftest import record_by_id
from intake_review_support import (
    reviewed_create_payment_term,
    reviewed_manual_document_with_lines,
    reviewed_post_customer_payment,
    reviewed_record_sales_invoice,
)
from sqlalchemy import select

from reality.db.core import Commitment, Reservation
from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.fulfillment_readiness import fulfillment_readiness


def _order(session, business, number):
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
                "quantity": "6",
                "unit_price": "25",
                "gross_amount": "150",
            }
        ],
        "150",
        payment_term_code="VORKASSE",
    )
    promise = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "6",
        None,
        amount="150",
        document_id=document.id,
        document_line_id=lines[0].id,
    )
    core.reserve(session, tenant, promise.id)
    receipt = reviewed_record_sales_invoice(
        session, tenant, lines[0].id, "6", "150", f"RE-{number}"
    )
    invoice_id = next(
        row["id"] for row in receipt["records"] if row["family"] == "document"
    )
    return promise, invoice_id


def _waiting(session, business, days):
    return {
        row.record_id: row
        for row in operational_exceptions(
            session, business.tenant.id, as_of=core.now() + timedelta(days=days)
        )
        if row.class_id == "reservation_awaiting_prepayment"
    }


def test_a_reservation_waiting_for_an_unpaid_prepayment_is_put_to_a_person(
    session, business
):
    """B12: the stock is reserved, the prepayment does not come, a person decides."""
    tenant = business.tenant.id
    reviewed_create_payment_term(
        session, tenant, "VORKASSE", "Vorkasse", 0, requires_prepayment=True
    )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "12",
        to_location_id=business.location.id,
    )
    unpaid, _ = _order(session, business, "SO-B12-A")
    paid, paid_invoice = _order(session, business, "SO-B12-B")
    # The paid order is the positive control: it is ready, and nothing waits.
    reviewed_post_customer_payment(session, tenant, paid_invoice, "150")
    assert fulfillment_readiness(session, tenant, paid.id).ship_ready

    # A week later the unpaid order still holds its six; the queue says so.
    finding = _waiting(session, business, 8)[unpaid.id]
    assert set(_waiting(session, business, 8)) == {unpaid.id}
    assert finding.causal_values["reserved_quantity"] == 6
    assert finding.causal_values["unpaid_amount"] == Decimal(150)
    # Nothing was released by itself.
    reservation = session.scalar(
        select(Reservation).where(
            Reservation.tenant_id == tenant, Reservation.commitment_id == unpaid.id
        )
    )
    assert reservation.status == "active"

    # The person releases the stock; the order stays open and can be reserved later.
    core.release_reservation(session, tenant, reservation.id)

    assert unpaid.id not in _waiting(session, business, 8)
    assert record_by_id(session, Commitment, unpaid.id).status == "open"
