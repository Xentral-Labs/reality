"""Bounded, tenant-scoped summaries for the unified Inspector record register."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    Commitment,
    Document,
    DocumentLine,
    Fact,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Party,
    Reservation,
    SourceRecord,
)
from reality.services.core import InvalidOperation, get_tenant

# Ordered families are an explicit presentation order, not a derived business state.
FAMILIES = (
    (Party, "Parties"),
    (Item, "Items"),
    (Location, "Locations"),
    (SourceRecord, "Source records"),
    (Document, "Documents"),
    (DocumentLine, "Document lines"),
    (Fact, "Facts"),
    (Commitment, "Commitments"),
    (Reservation, "Reservations"),
    (Movement, "Movements"),
    (LedgerEntry, "Ledger entries"),
    (BusinessEvent, "Business events"),
)
FIELDS = (
    "id",
    "name",
    "number",
    "sku",
    "external_id",
    "predicate",
    "event_type",
    "type",
    "description",
    "value",
    "status",
    "quantity",
    "unit",
    "amount",
    "currency",
    "account",
    "source_system",
    "source_type",
    "subject_type",
    "subject_id",
    "source_record_id",
    "document_id",
    "document_line_id",
    "commitment_id",
    "item_id",
    "party_id",
    "location_id",
    "recorded_at",
    "received_at",
    "created_at",
    "observed_at",
    "occurred_at",
    "effective_at",
)


def _value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def inspector_records(
    session: Session,
    tenant_id: str,
    *,
    kind: str = "all",
    query: str = "",
    page: int = 1,
    size: int = 50,
) -> dict[str, Any]:
    """Page authoritative summaries by family then opaque ID without payload dumps."""
    get_tenant(session, tenant_id)
    if kind not in {"all", *(model.__tablename__ for model, _ in FAMILIES)}:
        raise InvalidOperation("Unknown Inspector record type.")
    if page < 1 or size not in (25, 50, 100) or len(query) > 500:
        raise InvalidOperation("Invalid Inspector register page or search.")
    definitions = []
    total = 0
    for model, label in FAMILIES:
        if kind != "all" and model.__tablename__ != kind:
            continue
        fields = [name for name in FIELDS if hasattr(model, name)]
        conditions = [model.tenant_id == tenant_id]
        if query.strip():
            pattern = (
                "%"
                + query.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
                + "%"
            )
            conditions.append(
                or_(
                    *(
                        cast(getattr(model, name), String).ilike(pattern, escape="\\")
                        for name in fields
                    )
                )
            )
        count = (
            session.scalar(select(func.count()).select_from(model).where(*conditions))
            or 0
        )
        total += count
        definitions.append((model, label, fields, conditions, count))
    pages = max(1, (total + size - 1) // size)
    number = min(page, pages)
    skip = (number - 1) * size
    items = []
    for model, label, fields, conditions, count in definitions:
        if skip >= count:
            skip -= count
            continue
        rows = session.execute(
            select(*(getattr(model, name) for name in fields))
            .where(*conditions)
            .order_by(model.id)
            .offset(skip)
            .limit(size - len(items))
        ).mappings()
        for row in rows:
            values = {name: _value(value) for name, value in row.items()}
            title = next(
                (
                    str(values[name])
                    for name in (
                        "name",
                        "number",
                        "sku",
                        "external_id",
                        "predicate",
                        "event_type",
                        "type",
                        "account",
                    )
                    if values.get(name) not in (None, "")
                ),
                str(values["id"]),
            )
            details = [
                {"label": name.replace("_", " ").title(), "value": values[name]}
                for name in (
                    "value",
                    "status",
                    "quantity",
                    "unit",
                    "amount",
                    "currency",
                    "source_system",
                    "subject_type",
                )
                if values.get(name) is not None
            ]
            items.append(
                {
                    "id": values["id"],
                    "kind": model.__tablename__,
                    "label": label,
                    "title": title,
                    "details": details,
                }
            )
        skip = 0
        if len(items) == size:
            break
    return {
        "items": items,
        "types": [
            {"kind": model.__tablename__, "label": label} for model, label in FAMILIES
        ],
        "page": {
            "number": number,
            "size": size,
            "total": total,
            "pages": pages,
            "has_previous": number > 1,
            "has_next": number < pages,
        },
    }
