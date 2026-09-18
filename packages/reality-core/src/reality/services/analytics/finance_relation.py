"""Registered, bounded read-time financial positions; no settlement arithmetic."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Date, Integer, Numeric, String, bindparam, column, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import TableValuedAlias

from reality.db.core import Document
from reality.services import core
from reality.services.analytics.traversal import TraversalRefused

MAX_FINANCE_DOCUMENTS = 20_000
FINANCE_TYPES = (
    "sales_invoice",
    "supplier_invoice",
    "opening_customer_debt",
    "opening_supplier_debt",
)
FINANCE_COLUMNS = {
    "open_amount": Numeric(),
    "overdue_amount": Numeric(),
    "due_date": Date(),
    "days_overdue": Integer(),
    "settlement_status": String(),
}


def relation(session: Session, tenant_id: str) -> TableValuedAlias:
    """One canonical bulk derivation, materialized only inside this read query."""
    identities = set(
        session.scalars(
            select(Document.id)
            .where(Document.tenant_id == tenant_id, Document.type.in_(FINANCE_TYPES))
            .limit(MAX_FINANCE_DOCUMENTS + 1)
        )
    )
    if len(identities) > MAX_FINANCE_DOCUMENTS:
        raise TraversalRefused(
            "Financial analysis exceeds the 20,000-document derivation limit; use the finance register.",
            "finance_limit",
        )
    moment = datetime.now(UTC)
    rows = core.aging_register(
        session, tenant_id, as_of=moment, document_ids=identities
    )
    data: list[dict[str, Any]] = []
    for row in rows:
        overdue = row["due_date"] is not None and row["due_date"] < moment.date()
        data.append(
            {
                "document_id": row["document"].id,
                "open_amount": str(row["open"]),
                "overdue_amount": str(row["open"]) if overdue else "0",
                "due_date": row["due_date"].isoformat() if row["due_date"] else None,
                "days_overdue": row["days_overdue"],
                "settlement_status": row["status"],
            }
        )
    return recordset(data)


def recordset(data: list[dict[str, Any]]) -> TableValuedAlias:
    # One bound JSON value avoids PostgreSQL's parameter-count ceiling. Decimal
    # amounts remain exact strings converted to numeric by the typed recordset.
    return (
        func.jsonb_to_recordset(bindparam("finance_rows", data, type_=JSONB))
        .table_valued(
            column("document_id", String()),
            *[column(k, v) for k, v in FINANCE_COLUMNS.items()],
        )
        .render_derived(name="finance_aging", with_types=True)
    )
