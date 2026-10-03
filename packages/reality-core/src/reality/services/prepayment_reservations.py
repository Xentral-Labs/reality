"""Stock reserved for an order whose prepayment has not arrived (spec 348).

A prepayment order may be reserved before it is paid, and the reserved stock is
then withheld from every other order. Nothing releases it by itself: a person
decides whether to chase the payment or to release the reservation. This read
names the promises whose reservation has waited longer than the floor for a
prepayment that is still open, derived at read time and never stored.

Whether the prepayment is paid is the shared readiness decision of spec 275; it
is asked once per waiting order, never per line or per reservation, and only for
orders whose reservation has already waited past the floor.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import Commitment, Document, PaymentTerm, Reservation
from reality.services.core import utc_datetime

ZERO = Decimal(0)
# A week is the shortest span after which stock waiting on a payment is a
# question for a person; matched to the other "forgotten" floors of the queue.
PREPAYMENT_RESERVATION_FLOOR = timedelta(days=7)


def reservations_awaiting_prepayment(
    session: Session, tenant_id: str, as_of: datetime
) -> list[dict[str, Any]]:
    """Promises whose stock has waited past the floor for an unpaid prepayment."""
    from reality.services.fulfillment_readiness import fulfillment_readiness

    as_of = utc_datetime(as_of)
    rows = session.execute(
        select(
            Commitment.id,
            Commitment.document_id,
            Commitment.item_id,
            Commitment.unit,
            Document.number,
            Document.party_id,
            Document.currency,
            func.sum(Reservation.quantity),
            func.min(Reservation.reserved_at),
        )
        .join(
            Commitment,
            (Commitment.tenant_id == Reservation.tenant_id)
            & (Commitment.id == Reservation.commitment_id),
        )
        .join(
            Document,
            (Document.tenant_id == Commitment.tenant_id)
            & (Document.id == Commitment.document_id),
        )
        .join(
            PaymentTerm,
            (PaymentTerm.tenant_id == Document.tenant_id)
            & (PaymentTerm.id == Document.payment_term_id),
        )
        .where(
            Reservation.tenant_id == tenant_id,
            Reservation.status == "active",
            Reservation.reserved_at <= as_of,
            Commitment.type == "customer_delivery",
            Commitment.status == "open",
            Document.type == "sales_order",
            PaymentTerm.requires_prepayment.is_(True),
        )
        .group_by(
            Commitment.id,
            Commitment.document_id,
            Commitment.item_id,
            Commitment.unit,
            Document.number,
            Document.party_id,
            Document.currency,
        )
        .having(
            func.min(Reservation.reserved_at) <= as_of - PREPAYMENT_RESERVATION_FLOOR
        )
        .order_by(Document.number, Commitment.id)
    ).all()
    unpaid: dict[str, Decimal | None] = {}
    result = []
    for (
        commitment_id,
        order_id,
        item_id,
        unit,
        number,
        party_id,
        currency,
        reserved,
        since,
    ) in rows:
        if order_id not in unpaid:
            # The prepayment is the order's, so one promise of it answers for all.
            readiness = fulfillment_readiness(session, tenant_id, commitment_id)
            unpaid[order_id] = (
                Decimal(readiness.remaining_amount)
                if "prepayment_attribution_ambiguous" not in readiness.blocker_codes
                and Decimal(readiness.remaining_amount) > ZERO
                else None
            )
        remaining = unpaid[order_id]
        if remaining is None:
            continue
        since = utc_datetime(since)
        result.append(
            {
                "commitment_id": commitment_id,
                "order_id": order_id,
                "order_number": number,
                "party_id": party_id,
                "item_id": item_id,
                "unit": unit,
                "reserved_quantity": Decimal(reserved),
                "reserved_since": since,
                "waiting_days": (as_of - since).days,
                "unpaid_amount": remaining,
                "currency": currency,
            }
        )
    return result
