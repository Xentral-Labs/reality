"""The month-end billing lists (spec 299 FR-001, SC-003).

Goods shipped and not yet invoiced, and invoices ahead of the goods. Both lists
are the findings at one instant, filtered: they cannot disagree with what the
exception queue reports for the same moment.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Document, DocumentLine
from reality.services import core
from reality.services.exceptions import operational_exceptions

LISTS = {
    "shipped_not_billed": "unbilled_quantity",
    "billed_not_shipped": "unshipped_quantity",
}


def month_end_billing(
    session: Session, tenant_id: str, *, as_of: datetime | str | None = None
) -> dict[str, Any]:
    """Shipped-not-billed and billed-not-shipped order lines at `as_of`."""
    moment = core.utc_datetime(as_of) or core.now()
    findings = [
        row
        for row in operational_exceptions(session, tenant_id, as_of=moment)
        if row.class_id in LISTS
    ]
    line_ids = {row.record_id for row in findings}
    lines = {
        line.id: line
        for line in session.scalars(
            select(DocumentLine).where(
                DocumentLine.tenant_id == tenant_id, DocumentLine.id.in_(line_ids)
            )
        )
    }
    orders = {
        document.id: document
        for document in session.scalars(
            select(Document).where(
                Document.tenant_id == tenant_id,
                Document.id.in_({line.document_id for line in lines.values()}),
            )
        )
    }
    result: dict[str, Any] = {"as_of": moment.isoformat(), **{key: [] for key in LISTS}}
    for row in findings:
        line = lines.get(row.record_id)
        order = orders.get(line.document_id) if line else None
        values = row.causal_values
        result[row.class_id].append(
            {
                "exception_id": row.id,
                "order_id": order.id if order else row.trace.get("document_id"),
                "order_number": order.number if order else None,
                "party_id": order.party_id if order else None,
                "order_line_id": row.record_id,
                "item_id": line.item_id if line else None,
                "sku": line.sku if line else None,
                "quantity": str(values[LISTS[row.class_id]]),
                "unit": values.get("unit"),
                "values": {key: str(value) for key, value in values.items()},
            }
        )
    for rows in (result[key] for key in LISTS):
        rows.sort(key=lambda row: (row["order_number"] or "", row["order_line_id"]))
    return result
