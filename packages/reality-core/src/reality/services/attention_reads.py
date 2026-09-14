"""Read-only investigation over the stored exceptions projection and live explanations.

The register, the per-class summary and the class filter read the rows the background
refresh keeps in the `exceptions` projection (feature 179) together with that generation's
freshness, in one PostgreSQL snapshot. They derive nothing, refresh nothing and write
nothing. Explaining a single finding stays live: it walks causes and current records, and
says so when a stored finding has cleared since the generation was calculated.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import case, cast, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from reality.catalogs import load_operational_exception_catalog
from reality.db.core import Commitment, Item, Party, ProjectionRow, Tenant
from reality.services.core import NotFound, get_tenant
from reality.services.exceptions import (
    CLASS_ORDER,
    SEVERITY_ORDER,
    explain_operational_exception,
)
from reality.services.projections import (
    EXCEPTIONS,
    _read_without_flush,
    projection_metadata,
    projection_state_expressions,
)


class FindingCleared(NotFound):
    """A finding the stored generation still lists no longer derives from current records."""

    code = "finding_cleared"

    def __init__(self, completed_at: str | None) -> None:
        super().__init__("This finding has cleared since the last calculation.")
        self.completed_at = completed_at


def _targets(
    session: Session, tenant_id: str, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    identities = [
        row["record_id"] for row in rows if row["record_type"] == "commitment"
    ]
    party_id = case(
        (Commitment.type == "supplier_delivery", Commitment.from_party_id),
        else_=Commitment.to_party_id,
    )
    references = list(
        session.execute(
            select(Commitment.id, Commitment.type, Party.name, Item.name)
            .outerjoin(Party, (Party.tenant_id == tenant_id) & (Party.id == party_id))
            .outerjoin(
                Item, (Item.tenant_id == tenant_id) & (Item.id == Commitment.item_id)
            )
            .where(
                Commitment.tenant_id == tenant_id,
                Commitment.id.in_(identities),
                Commitment.type.in_(["customer_delivery", "supplier_delivery"]),
            )
        )
    )
    deliveries = {row[0] for row in references if row[1] == "customer_delivery"}
    labels = {
        row[0]: " · ".join(value for value in row[2:] if value) for row in references
    }
    supported = {
        "commitment",
        "document",
        "document_line",
        "party",
        "item",
        "location",
        "movement",
        "reservation",
        "fact",
        "ledger_entry",
        "source_record",
    }
    return [
        {
            **row,
            "context": labels.get(row["record_id"])
            if row["record_type"] == "commitment"
            else None,
            "target": {
                "kind": row["record_type"]
                if row["record_type"] in supported
                else "exception",
                "id": row["record_id"]
                if row["record_type"] in supported
                else row["id"],
                "delivery_id": row["record_id"]
                if row["record_type"] == "commitment" and row["record_id"] in deliveries
                else None,
            },
        }
        for row in rows
    ]


def _class_ids() -> list[str]:
    return [entry["id"] for entry in load_operational_exception_catalog().classes]


def _canonical(row: dict[str, Any]) -> tuple[Any, ...]:
    # A generation written before the builder recorded positions orders by the same
    # severity and class rank the derivation uses; the record id keeps it stable.
    position = row.get("position")
    return (
        position is None,
        position or 0,
        SEVERITY_ORDER.get(row.get("severity", ""), len(SEVERITY_ORDER)),
        CLASS_ORDER.get(row.get("class_id", ""), len(CLASS_ORDER)),
        str(row.get("record_id", "")),
    )


@_read_without_flush
def stored_exceptions(
    session: Session, tenant_id: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The stored exception rows in canonical order and the freshness of that generation.

    Rows and checkpoint come from one PostgreSQL snapshot, so a refresh that lands between
    them cannot mix two generations. No builder runs here: a company without a completed
    generation gets no rows and the state `uninitialized`, which is not an empty queue.
    """
    get_tenant(session, tenant_id)
    payloads = (
        select(ProjectionRow.payload)
        .where(
            ProjectionRow.tenant_id == tenant_id,
            ProjectionRow.projection_name == EXCEPTIONS,
        )
        .subquery()
    )
    items = select(func.json_agg(cast(payloads.c.payload, JSONB))).scalar_subquery()
    values = (
        session.execute(
            select(
                items.label("items"),
                *(
                    expression.label(key)
                    for key, expression in projection_state_expressions(
                        tenant_id, EXCEPTIONS
                    ).items()
                ),
            ).where(Tenant.id == tenant_id)
        )
        .mappings()
        .first()
    )
    if values is None:
        raise NotFound("Tenant not found.")
    rows = sorted(values["items"] or [], key=_canonical)
    return rows, projection_metadata(EXCEPTIONS, values)


def attention_summary(session: Session, tenant_id: str) -> dict[str, Any]:
    """Count the stored findings per catalog class.

    Every class in the catalog is listed, in catalog order, so a class with nothing open
    reports zero rather than disappearing. The counts belong to the generation the
    metadata describes.
    """
    rows, metadata = stored_exceptions(session, tenant_id)
    counts = {class_id: 0 for class_id in _class_ids()}
    for row in rows:
        counts[row["class_id"]] = counts.get(row["class_id"], 0) + 1
    return {
        "classes": [
            {"class_id": class_id, "open": open_count}
            for class_id, open_count in counts.items()
        ],
        "total": len(rows),
        "observed_at": metadata["completed_at"],
        "metadata": metadata,
    }


def attention_register(
    session: Session,
    tenant_id: str,
    *,
    query: str = "",
    severity: str = "",
    class_id: str = "",
    page: int = 1,
    size: int = 50,
) -> dict[str, Any]:
    if severity and severity not in SEVERITY_ORDER:
        raise ValueError("Unknown exception severity.")
    if class_id and class_id not in _class_ids():
        raise ValueError("Unknown exception class.")
    rows, metadata = stored_exceptions(session, tenant_id)
    needle = query.strip().casefold()
    rows = [
        row
        for row in rows
        if (not severity or row["severity"] == severity)
        and (not class_id or row["class_id"] == class_id)
        and (
            not needle
            or any(
                needle in str(row[key]).casefold()
                for key in ("id", "class_id", "title", "impact", "record_id")
            )
        )
    ]
    size = max(1, min(size, 100))
    total = len(rows)
    pages = max(1, (total + size - 1) // size)
    page = max(1, min(page, pages))
    return {
        "items": _targets(session, tenant_id, rows[(page - 1) * size : page * size]),
        "page": {
            "number": page,
            "size": size,
            "total": total,
            "pages": pages,
            "has_previous": page > 1,
            "has_next": page < pages,
        },
        "observed_at": metadata["completed_at"],
        "metadata": metadata,
    }


def attention_detail(session: Session, tenant_id: str, identity: str) -> dict[str, Any]:
    """Explain one finding live; a stored finding that no longer derives says so."""
    get_tenant(session, tenant_id)
    observed = datetime.now(UTC)
    try:
        detail = explain_operational_exception(
            session, tenant_id, identity, as_of=observed
        )
    except NotFound:
        rows, metadata = stored_exceptions(session, tenant_id)
        if any(row["id"] == identity for row in rows):
            raise FindingCleared(metadata["completed_at"]) from None
        raise
    entry = next(
        entry
        for entry in load_operational_exception_catalog().classes
        if entry["id"] == detail["class_id"]
    )
    return {
        **_targets(session, tenant_id, [detail])[0],
        "guidance": entry["clears_through"],
        "observed_at": observed,
    }
