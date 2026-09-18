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


def aging_rows(
    session: Session,
    tenant_id: str,
    *,
    moment: datetime,
    document_ids: set[str],
    cache: dict[Any, Any] | None = None,
) -> list[dict[str, Any]]:
    """The aging register, computed once per request for one set of documents.

    Party balances rest on the same register as the open items do, so a question
    reaching both used to derive it twice. The key is the exact set asked for,
    because a smaller set is not a valid answer for a larger one.
    """
    key = ("finance.aging", moment, frozenset(document_ids))
    if cache is not None and key in cache:
        return cache[key]
    rows = core.aging_register(
        session, tenant_id, as_of=moment, document_ids=document_ids
    )
    if cache is not None:
        cache[key] = rows
    return rows


def relation(
    session: Session,
    tenant_id: str,
    *,
    identities: set[str] | None = None,
    cache: dict[Any, Any] | None = None,
) -> TableValuedAlias:
    """One canonical bulk derivation, materialized only inside this read query."""
    candidates = select(Document.id).where(
        Document.tenant_id == tenant_id, Document.type.in_(FINANCE_TYPES)
    )
    if identities is not None:
        candidates = candidates.where(Document.id.in_(identities))
    documents = set(session.scalars(candidates.limit(MAX_FINANCE_DOCUMENTS + 1)))
    if len(documents) > MAX_FINANCE_DOCUMENTS:
        raise TraversalRefused(
            "Financial analysis exceeds the 20,000-document derivation limit; use the finance register.",
            "finance_limit",
        )
    moment = datetime.now(UTC)
    rows = aging_rows(
        session, tenant_id, moment=moment, document_ids=documents, cache=cache
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
