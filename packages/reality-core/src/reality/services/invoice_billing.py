"""What a party can be invoiced for now, grouped by order (spec 283 FR-006).

Nothing here is a new rule. What was delivered is what the customer kept (shipped
less returned) or what the company still holds (received less sent back), read
through the same movement path as every exception class; what was billed is the
reversal-aware billing availability the invoice entry itself validates against.
A position is billable by the smaller of "delivered and not yet billed" and
"still billable on the order line", so the list never offers what the entry
would refuse.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    LedgerEntry,
    LedgerReversal,
    Party,
)
from reality.services import core

ZERO = Decimal(0)
MAX_LIMIT = 200

_DIRECTIONS = {
    "sales": (
        "sales_order",
        "sales_invoice",
        "customer_delivery",
        "shipment",
        "return",
    ),
    "purchase": (
        "purchase_order",
        "supplier_invoice",
        "supplier_delivery",
        "receipt",
        "supplier_return",
    ),
}


def _candidate_lines(
    session: Session,
    tenant_id: str,
    order_type: str,
    invoice_type: str,
    party_id: str,
    currency: str,
) -> list[DocumentLine]:
    """Order lines that may still be billable, without reading them one by one.

    A line whose referencing invoice quantity already reaches its own quantity is
    fully billed, unless one of those invoices was reversed; only those two cases
    are left for the exact per-line reading. Fully billed history therefore costs
    one query, however long it is.
    """
    invoice = select(Document.id).where(
        Document.tenant_id == tenant_id, Document.type == invoice_type
    )
    billed = (
        select(
            DocumentLine.billed_document_line_id.label("line_id"),
            func.sum(DocumentLine.quantity).label("quantity"),
        )
        .where(
            DocumentLine.tenant_id == tenant_id,
            DocumentLine.document_id.in_(invoice),
            DocumentLine.billed_document_line_id.is_not(None),
        )
        .group_by(DocumentLine.billed_document_line_id)
        .subquery()
    )
    reversed_invoices = (
        select(LedgerEntry.document_id)
        .join(
            LedgerReversal,
            (LedgerReversal.tenant_id == LedgerEntry.tenant_id)
            & (
                LedgerReversal.original_posting_group_id == LedgerEntry.posting_group_id
            ),
        )
        .where(LedgerEntry.tenant_id == tenant_id)
    )
    touched_by_reversal = select(DocumentLine.billed_document_line_id).where(
        DocumentLine.tenant_id == tenant_id,
        DocumentLine.document_id.in_(reversed_invoices),
    )
    return list(
        session.scalars(
            select(DocumentLine)
            .join(
                Document,
                (Document.tenant_id == DocumentLine.tenant_id)
                & (Document.id == DocumentLine.document_id),
            )
            .outerjoin(billed, billed.c.line_id == DocumentLine.id)
            .where(
                DocumentLine.tenant_id == tenant_id,
                Document.type == order_type,
                Document.party_id == party_id,
                Document.currency == currency,
                (func.coalesce(billed.c.quantity, 0) < DocumentLine.quantity)
                | DocumentLine.id.in_(touched_by_reversal),
            )
            .order_by(
                Document.document_date.asc().nulls_last(),
                Document.number,
                Document.id,
                DocumentLine.id,
            )
        )
    )


def billable_positions(
    session: Session,
    tenant_id: str,
    *,
    direction: str,
    party_id: str,
    currency: str,
    limit: int = MAX_LIMIT,
) -> dict[str, Any]:
    """List a party's order positions that can be invoiced now, grouped by order."""
    if direction not in _DIRECTIONS:
        raise core.InvalidOperation("Direction must be sales or purchase.")
    if not 1 <= limit <= MAX_LIMIT:
        raise core.InvalidOperation(f"The limit must be between 1 and {MAX_LIMIT}.")
    party = core._tenant_record(session, Party, tenant_id, party_id)
    order_type, invoice_type, promise_type, delivered_type, returned_type = _DIRECTIONS[
        direction
    ]
    orders: dict[str, dict[str, Any]] = {}
    total = 0
    for line in _candidate_lines(
        session, tenant_id, order_type, invoice_type, party.id, currency
    ):
        promise = session.scalar(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_line_id == line.id,
                Commitment.type == promise_type,
            )
        )
        if promise is None:
            continue
        delivered = core.movement_quantity(
            session, tenant_id, promise.id, delivered_type
        ) - core.movement_quantity(session, tenant_id, promise.id, returned_type)
        if delivered <= ZERO:
            continue
        billing = core._order_line_billing(session, tenant_id, line.id)
        billable = min(delivered - billing["invoiced"], billing["remaining"])
        if billable <= ZERO:
            continue
        total += 1
        if total > limit:
            continue
        if line.document_id not in orders:
            document = core._tenant_record(
                session, Document, tenant_id, line.document_id
            )
            orders[line.document_id] = {
                "id": document.id,
                "number": document.number,
                "document_date": document.document_date,
                "positions": [],
            }
        orders[line.document_id]["positions"].append(
            {
                "order_line_id": line.id,
                "label": billing["label"],
                "unit": line.unit,
                "ordered": billing["ordered"],
                "delivered": delivered,
                "invoiced": billing["invoiced"],
                "remaining": billing["remaining"],
                "billable": billable,
                "unit_price": line.unit_price,
                "order_line_amount": line.gross_amount,
            }
        )
    return {
        "direction": direction,
        "party": {"id": party.id, "name": party.name},
        "currency": currency,
        "limit": limit,
        "total": total,
        "orders": list(orders.values()),
    }
