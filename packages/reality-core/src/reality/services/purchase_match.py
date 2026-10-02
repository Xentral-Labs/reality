"""The three-way match of a purchase order, read per line (spec 310).

A line is matched when the quantity in force (ordered, or confirmed by the
supplier) was received, net of what went back, and billed, net of credits, at
the price agreed last. Otherwise the read names each difference. The answer is
derived from the promises, movements and invoice lines at read time and never
stored (DR-002); it uses the quantity and unit rules of the purchase findings,
so the two never disagree.

A cancelled line expects nothing received and nothing billed; the supplier's
cancellation charge is shown beside it and is not its goods.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Commitment, Document, DocumentLine, Item
from reality.services.core import (
    ZERO,
    InvalidOperation,
    _agreed_line_prices,
    _movement_quantities,
    _tenant_record,
    commitment_terms,
    decimal,
)


def _text(value: Decimal | None) -> str | None:
    return None if value is None else format(decimal(value).normalize(), "f")


def purchase_match(
    session: Session, tenant_id: str, document_id: str
) -> dict[str, Any]:
    """Whether each line of a purchase order is ordered = received = billed."""
    from reality.services.exceptions import (
        _billing_lines,
        _in_promise_unit,
        _invoice_lines,
        _prices_comparable,
        _quantity_in_agreed_unit,
        _referencing_document_type,
    )

    order = _tenant_record(session, Document, tenant_id, document_id)
    if order.type != "purchase_order":
        raise InvalidOperation(code="purchase_match_order_required")
    lines = list(
        session.scalars(
            select(DocumentLine)
            .where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id == order.id,
            )
            .order_by(DocumentLine.id)
        )
    )
    promises: dict[str, list[Commitment]] = {}
    for commitment in session.scalars(
        select(Commitment)
        .where(
            Commitment.tenant_id == tenant_id,
            Commitment.document_id == order.id,
            Commitment.type == "supplier_delivery",
        )
        .order_by(Commitment.id)
    ):
        promises.setdefault(commitment.document_line_id, []).append(commitment)
    terms = commitment_terms(
        session, tenant_id, [c.id for rows in promises.values() for c in rows]
    )
    movements = {
        key: value
        for commitment_id in {c.id for rows in promises.values() for c in rows}
        for key, value in _movement_quantities(
            session, tenant_id, commitment_id
        ).items()
    }
    agreed = _agreed_line_prices(session, tenant_id, lines)
    items = {
        item.id: item
        for item in session.scalars(
            select(Item).where(
                Item.tenant_id == tenant_id,
                Item.id.in_({line.item_id for line in lines if line.item_id}),
            )
        )
    }
    rows = []
    for line in lines:
        held = promises.get(line.id)
        # A line that promised no goods (freight, a service) is not matched.
        if not held:
            continue
        open_promises = [c for c in held if c.status != "cancelled"]
        cancelled = not open_promises
        ordered = sum((decimal(c.quantity) for c in held), ZERO)
        in_force = sum((terms[c.id].quantity for c in open_promises), ZERO)
        received = sum(
            (
                movements.get((c.id, "receipt"), ZERO)
                - movements.get((c.id, "supplier_return"), ZERO)
                for c in held
            ),
            ZERO,
        )
        invoices = _invoice_lines(session, tenant_id, line.id)
        credits = [
            row
            for row in _billing_lines(session, tenant_id, line.id)
            if _referencing_document_type(session, tenant_id, row)
            == "supplier_credit_note"
        ]
        charges = [
            row
            for row in _billing_lines(session, tenant_id, line.id)
            if row.line_type == "charge"
            and _referencing_document_type(session, tenant_id, row)
            == "supplier_invoice"
        ]
        billed_raw = (
            _quantity_in_agreed_unit(session, tenant_id, line, invoices)
            if invoices
            else ZERO
        )
        credited_raw = (
            _quantity_in_agreed_unit(session, tenant_id, line, credits)
            if credits
            else ZERO
        )
        differences = []
        billed = None
        if billed_raw is None or credited_raw is None:
            differences.append("units_not_comparable")
        else:
            billed, _ = _in_promise_unit(
                session, tenant_id, held[0], line, billed_raw - credited_raw
            )
            if billed is None:
                differences.append("units_not_comparable")
        expected = ZERO if cancelled else in_force
        if received < expected:
            differences.append("received_short")
        elif received > expected:
            differences.append("received_over")
        if billed is not None:
            if billed < received:
                differences.append("billed_short")
            elif billed > received:
                differences.append("billed_over")
        price = agreed.get(line.id)
        billed_prices = sorted(
            {
                decimal(row.unit_price)
                for row in invoices
                if row.unit_price is not None and _prices_comparable(row, line)
            }
        )
        if price is not None and any(value != price for value in billed_prices):
            differences.append("price_differs")
        item = items.get(line.item_id)
        rows.append(
            {
                "document_line_id": line.id,
                "item_id": line.item_id,
                "item": item.name if item else line.description,
                "sku": item.sku if item else line.sku,
                "unit": held[0].unit or line.unit,
                "ordered": _text(ordered),
                "in_force": _text(in_force),
                "received": _text(received),
                "billed": _text(billed),
                "ordered_unit_price": _text(line.unit_price),
                "agreed_unit_price": _text(price),
                "billed_unit_prices": [_text(value) for value in billed_prices],
                "price_unit": line.unit,
                "cancelled": cancelled,
                "charges": [
                    {
                        "document_line_id": row.id,
                        "document_id": row.document_id,
                        "amount": _text(row.gross_amount),
                        "description": row.description,
                    }
                    for row in charges
                ],
                "matched": not differences,
                "differences": differences,
            }
        )
    return {
        "document_id": order.id,
        "number": order.number,
        "party_id": order.party_id,
        "currency": order.currency,
        "matched": bool(rows) and all(row["matched"] for row in rows),
        "lines": rows,
    }
