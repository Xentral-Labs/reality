"""Read-only investigation over the stored exceptions projection and live explanations.

The register, the per-class summary and the class filter read the rows the background
refresh keeps in the `exceptions` projection (feature 179) together with that generation's
freshness, in one PostgreSQL snapshot. They derive nothing, refresh nothing and write
nothing. Explaining a single finding stays live: it walks causes and current records, and
says so when a stored finding has cleared since the generation was calculated.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Integer, case, cast, func, literal, literal_column, select
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
    cost_finding_prerequisite,
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
    """The derivation's own order, from the keys the row carries.

    `(severity, class rank, sort_at, record_id)` is what `operational_exceptions`
    sorts by, and the row now carries every part of it. Rows written before that —
    generations that stored a `position` and no `sort_at` — order by the rest, which
    is where they already agreed; within a class they fall back on the record id, as
    they did before this reader could see a date at all.
    """
    return (
        SEVERITY_ORDER.get(row.get("severity", ""), len(SEVERITY_ORDER)),
        CLASS_ORDER.get(row.get("class_id", ""), len(CLASS_ORDER)),
        row.get("sort_at") or "9999-12-31T23:59:59+00:00",
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
    cost_basis = cost_finding_prerequisite(session, tenant_id, protect=True)
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
    metadata = projection_metadata(EXCEPTIONS, values)
    metadata["cost_basis"] = cost_basis
    return rows, metadata


@_read_without_flush
def attention_summary(session: Session, tenant_id: str) -> dict[str, Any]:
    """Count the stored findings per catalog class.

    Every class in the catalog is listed, in catalog order, so a class with nothing open
    reports zero rather than disappearing. The counts belong to the generation the
    metadata describes.
    """
    get_tenant(session, tenant_id)
    cost_basis = cost_finding_prerequisite(session, tenant_id, protect=True)
    payload = cast(ProjectionRow.payload, JSONB)
    grouped = (
        select(
            payload["class_id"].astext.label("class_id"),
            func.count().label("open"),
        )
        .where(
            ProjectionRow.tenant_id == tenant_id,
            ProjectionRow.projection_name == EXCEPTIONS,
        )
        .group_by(literal_column("class_id"))
        .subquery()
    )
    counts = select(
        func.coalesce(
            func.jsonb_object_agg(grouped.c.class_id, grouped.c.open),
            cast(literal("{}"), JSONB),
        )
    ).scalar_subquery()
    values = (
        session.execute(
            select(
                counts.label("counts"),
                *(
                    expression.label(key)
                    for key, expression in projection_state_expressions(
                        tenant_id, EXCEPTIONS
                    ).items()
                ),
            ).where(Tenant.id == tenant_id)
        )
        .mappings()
        .one()
    )
    metadata = projection_metadata(EXCEPTIONS, values)
    metadata["cost_basis"] = cost_basis
    stored_counts = values["counts"] or {}
    counts = {class_id: 0 for class_id in _class_ids()}
    counts.update({class_id: int(count) for class_id, count in stored_counts.items()})
    return {
        "classes": [
            {"class_id": class_id, "open": open_count}
            for class_id, open_count in counts.items()
        ],
        "total": sum(counts.values()),
        "observed_at": metadata["completed_at"],
        "metadata": metadata,
    }


@_read_without_flush
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
    get_tenant(session, tenant_id)
    cost_basis = cost_finding_prerequisite(session, tenant_id, protect=True)
    needle = query.strip().casefold()
    size = max(1, min(size, 100))
    requested_page = max(1, page)
    payload = cast(ProjectionRow.payload, JSONB)
    filters = [
        ProjectionRow.tenant_id == tenant_id,
        ProjectionRow.projection_name == EXCEPTIONS,
    ]
    if severity:
        filters.append(payload["severity"].astext == severity)
    if class_id:
        filters.append(payload["class_id"].astext == class_id)
    if needle:
        searchable = func.lower(
            func.concat_ws(
                " ",
                payload["id"].astext,
                payload["class_id"].astext,
                payload["title"].astext,
                payload["impact"].astext,
                payload["record_id"].astext,
            )
        )
        filters.append(searchable.contains(needle))
    total = (
        select(func.count())
        .select_from(ProjectionRow)
        .where(*filters)
        .scalar_subquery()
    )
    pages = func.greatest(1, func.ceil(total / size))
    selected_page = func.least(requested_page, pages)
    page_rows = (
        select(payload.label("payload"))
        .where(*filters)
        .order_by(
            cast(payload["position"].astext, Integer).asc().nulls_last(),
            payload["severity"].astext,
            payload["class_id"].astext,
            payload["record_id"].astext,
        )
        .limit(size)
        .offset(cast((selected_page - 1) * size, Integer))
        .subquery()
    )
    items = select(func.json_agg(page_rows.c.payload)).scalar_subquery()
    values = (
        session.execute(
            select(
                items.label("items"),
                total.label("total"),
                cast(pages, Integer).label("pages"),
                cast(selected_page, Integer).label("page"),
                *(
                    expression.label(key)
                    for key, expression in projection_state_expressions(
                        tenant_id, EXCEPTIONS
                    ).items()
                ),
            ).where(Tenant.id == tenant_id)
        )
        .mappings()
        .one()
    )
    metadata = projection_metadata(EXCEPTIONS, values)
    metadata["cost_basis"] = cost_basis
    rows = values["items"] or []
    page = values["page"]
    pages = values["pages"]
    total_count = values["total"]
    return {
        "items": _targets(session, tenant_id, rows),
        "page": {
            "number": page,
            "size": size,
            "total": total_count,
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
        stored = next((row for row in rows if row["id"] == identity), None)
        if stored and stored["class_id"] in {
            "missing_acquisition_cost",
            "unassigned_cost_component",
            "stale_cost_review",
            "negative_actual_db1",
        }:
            detail = {**stored, "raw_source": None}
            observed = metadata["completed_at"]
        elif stored:
            raise FindingCleared(metadata["completed_at"]) from None
        else:
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
