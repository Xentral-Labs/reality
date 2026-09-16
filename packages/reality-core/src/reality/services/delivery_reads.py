"""Bounded, tenant-scoped delivery observations shared by tools and web."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    Commitment,
    CommitmentHold,
    CommitmentRevision,
    Document,
    DocumentLine,
    Item,
    Location,
    Movement,
    MovementCorrection,
    Party,
    Reservation,
)
from reality.db.query_order import query_order
from reality.services.core import (
    HOLD_REASONS,
    InvalidOperation,
    NotFound,
    active_party_delivery_hold,
    active_reserved,
    stock_at,
)


def effective_value(field: str):
    column = getattr(CommitmentRevision, field)
    latest = (
        select(column)
        .where(
            CommitmentRevision.tenant_id == Commitment.tenant_id,
            CommitmentRevision.commitment_id == Commitment.id,
            column.is_not(None),
        )
        .order_by(CommitmentRevision.stated_at.desc(), CommitmentRevision.id.desc())
        .limit(1)
        .correlate(Commitment)
        .scalar_subquery()
    )
    return func.coalesce(latest, getattr(Commitment, field))


def fulfillment_expressions():
    reserved = (
        select(func.coalesce(func.sum(Reservation.quantity), 0))
        .where(
            Reservation.tenant_id == Commitment.tenant_id,
            Reservation.commitment_id == Commitment.id,
            Reservation.status == "active",
        )
        .correlate(Commitment)
        .scalar_subquery()
    )
    recorded_fulfillment = (
        select(func.coalesce(func.sum(Movement.quantity), 0))
        .where(
            Movement.tenant_id == Commitment.tenant_id,
            Movement.commitment_id == Commitment.id,
            or_(
                and_(
                    Commitment.type == "customer_delivery", Movement.type == "shipment"
                ),
                and_(
                    Commitment.type == "supplier_delivery", Movement.type == "receipt"
                ),
            ),
        )
        .correlate(Commitment)
        .scalar_subquery()
    )
    reversed_fulfillment = (
        select(func.coalesce(func.sum(Movement.quantity), 0))
        .select_from(MovementCorrection)
        .join(Movement, Movement.id == MovementCorrection.original_movement_id)
        .where(
            MovementCorrection.tenant_id == Commitment.tenant_id,
            Movement.tenant_id == Commitment.tenant_id,
            Movement.commitment_id == Commitment.id,
            or_(
                and_(
                    Commitment.type == "customer_delivery", Movement.type == "shipment"
                ),
                and_(
                    Commitment.type == "supplier_delivery", Movement.type == "receipt"
                ),
            ),
        )
        .correlate(Commitment)
        .scalar_subquery()
    )
    fulfilled = recorded_fulfillment - reversed_fulfillment
    remaining = effective_value("quantity") - fulfilled
    open_quantity = case((remaining > 0, remaining), else_=0)
    return reserved, fulfilled, open_quantity


def _query(tenant_id: str, commitment_type: str = "customer_delivery"):
    party_id = (
        Commitment.from_party_id
        if commitment_type == "supplier_delivery"
        else Commitment.to_party_id
    )
    reserved, fulfilled, remaining = fulfillment_expressions()
    return (
        select(
            Commitment,
            Party.name.label("party"),
            Item.name.label("item"),
            Item.unit,
            Location.name.label("location"),
            effective_value("quantity").label("promised"),
            effective_value("due_at").label("due_at"),
            reserved.label("reserved"),
            fulfilled.label("fulfilled"),
            remaining.label("open"),
        )
        .outerjoin(
            Party,
            and_(
                Party.tenant_id == Commitment.tenant_id,
                Party.id == party_id,
            ),
        )
        .outerjoin(
            Item,
            and_(Item.tenant_id == Commitment.tenant_id, Item.id == Commitment.item_id),
        )
        .outerjoin(
            Location,
            and_(
                Location.tenant_id == Commitment.tenant_id,
                Location.id == Commitment.location_id,
            ),
        )
        .where(Commitment.tenant_id == tenant_id, Commitment.type == commitment_type)
    )


def _row(row) -> dict[str, Any]:
    commitment = row[0]
    return {
        "id": commitment.id,
        "tenant_id": commitment.tenant_id,
        "document_id": commitment.document_id,
        "document_line_id": commitment.document_line_id,
        "type": commitment.type,
        "party_id": (
            commitment.from_party_id
            if commitment.type == "supplier_delivery"
            else commitment.to_party_id
        ),
        "counterparty": row.party,
        "item_id": commitment.item_id,
        "item": row.item,
        "unit": row.unit,
        "location_id": commitment.location_id,
        "location": row.location,
        "promised": str(row.promised),
        "due_at": row.due_at,
        "reserved": str(row.reserved),
        "fulfilled": str(row.fulfilled),
        "open": str(row.open),
        "status": commitment.status,
    }


def delivery_work(
    session: Session,
    tenant_id: str,
    *,
    page: int = 1,
    size: int = 50,
    query: str = "",
    status: str = "open",
    commitment_type: str = "customer_delivery",
    document_id: str = "",
    sort: str = "",
    sort_direction: str = "asc",
) -> dict[str, Any]:
    if status not in {"open", "all"}:
        raise InvalidOperation("Delivery status must be open or all.")
    if commitment_type not in {"customer_delivery", "supplier_delivery"}:
        raise InvalidOperation(
            "Delivery type must be customer_delivery or supplier_delivery."
        )
    base = _query(tenant_id, commitment_type)
    if document_id:
        line_document = (
            select(DocumentLine.document_id)
            .where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.id == Commitment.document_line_id,
            )
            .correlate(Commitment)
            .scalar_subquery()
        )
        base = base.where(
            func.coalesce(line_document, Commitment.document_id) == document_id
        )
    if status == "open":
        base = base.where(Commitment.status == "open", fulfillment_expressions()[2] > 0)
    if query.strip():
        pattern = f"%{query.strip()}%"
        base = base.where(
            or_(
                Commitment.id.ilike(pattern),
                Party.name.ilike(pattern),
                Item.name.ilike(pattern),
            )
        )
    total = int(session.scalar(select(func.count()).select_from(base.subquery())) or 0)
    size = max(1, min(size, 100))
    pages = max(1, (total + size - 1) // size)
    page = max(1, min(page, pages))
    rows = session.execute(
        base.order_by(
            *query_order(
                sort,
                sort_direction,
                {
                    "id": Commitment.id,
                    "counterparty": Party.name,
                    "item": Item.name,
                    "due_at": effective_value("due_at"),
                    "open": fulfillment_expressions()[2],
                    "status": Commitment.status,
                },
                Commitment.id,
                (
                    effective_value("due_at").asc().nulls_last(),
                    Commitment.id,
                ),
            )
        )
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return {
        "items": [_row(row) for row in rows],
        "page": {
            "number": page,
            "size": size,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_previous": page > 1,
        },
        "scope": {
            "tenant_id": tenant_id,
            "query": query,
            "status": status,
            "commitment_type": commitment_type,
            "document_id": document_id,
        },
        "observed_at": datetime.now(UTC),
    }


def delivery_case(
    session: Session, tenant_id: str, commitment_id: str, *, before: int | None = None
) -> dict[str, Any]:
    kind = session.scalar(
        select(Commitment.type).where(
            Commitment.tenant_id == tenant_id, Commitment.id == commitment_id
        )
    )
    if kind not in {"customer_delivery", "supplier_delivery"}:
        raise NotFound("Delivery not found.")
    row = session.execute(
        _query(tenant_id, kind).where(Commitment.id == commitment_id)
    ).first()
    if row is None:
        raise NotFound("Delivery not found.")
    commitment = row[0]
    links = []
    document_id = commitment.document_id
    if commitment.document_line_id:
        line = session.scalar(
            select(DocumentLine).where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.id == commitment.document_line_id,
            )
        )
        if line:
            links.append(
                {"kind": "document_line", "id": line.id, "label": "Document line"}
            )
            document_id = line.document_id
    if document_id:
        document = session.scalar(
            select(Document).where(
                Document.tenant_id == tenant_id, Document.id == document_id
            )
        )
        if document:
            links.append(
                {
                    "kind": "document",
                    "id": document.id,
                    "label": document.number or "Document",
                }
            )
            if document.source_record_id:
                links.append(
                    {
                        "kind": "source_record",
                        "id": document.source_record_id,
                        "label": "Original source",
                    }
                )
    reservation_ids = select(Reservation.id).where(
        Reservation.tenant_id == tenant_id, Reservation.commitment_id == commitment_id
    )
    movement_ids = select(Movement.id).where(
        Movement.tenant_id == tenant_id, Movement.commitment_id == commitment_id
    )
    events_query = select(BusinessEvent).where(
        BusinessEvent.tenant_id == tenant_id,
        or_(
            and_(
                BusinessEvent.subject_type == "commitment",
                BusinessEvent.subject_id == commitment_id,
            ),
            and_(
                BusinessEvent.subject_type == "reservation",
                BusinessEvent.subject_id.in_(reservation_ids),
            ),
            and_(
                BusinessEvent.subject_type == "movement",
                BusinessEvent.subject_id.in_(movement_ids),
            ),
        ),
    )
    if before is not None:
        events_query = events_query.where(BusinessEvent.sequence < before)
    events = list(
        session.scalars(events_query.order_by(BusinessEvent.sequence.desc()).limit(21))
    )
    physical = stock_at(session, tenant_id, commitment.item_id, commitment.location_id)
    reserved = active_reserved(
        session, tenant_id, commitment.item_id, commitment.location_id
    )
    holds = [
        (hold, "commitment")
        for hold in session.scalars(
            select(CommitmentHold)
            .where(
                CommitmentHold.tenant_id == tenant_id,
                CommitmentHold.commitment_id == commitment_id,
                CommitmentHold.released_at.is_(None),
            )
            .order_by(CommitmentHold.id)
            .execution_options(populate_existing=True)
        )
    ]
    if kind == "customer_delivery" and commitment.to_party_id:
        party_hold = active_party_delivery_hold(
            session, tenant_id, commitment.to_party_id
        )
        if party_hold:
            holds.append((party_hold, "party"))
    detail = _row(row)
    detail["blockers"] = [
        {
            "id": hold.id,
            "reason": hold.reason_code,
            "note": hold.note,
            "scope": scope,
            "created_at": hold.created_at,
        }
        for hold, scope in holds
    ]
    return {
        "case": detail,
        "hold_reasons": sorted(HOLD_REASONS),
        "inventory": {
            "item_id": commitment.item_id,
            "location_id": commitment.location_id,
            "unit": row.unit,
            "physical": str(physical),
            "reserved": str(reserved),
            "available": str(physical - reserved),
        },
        "links": links,
        "history": {
            "items": [
                {
                    "id": event.id,
                    "sequence": event.sequence,
                    "type": event.event_type,
                    "occurred_at": event.occurred_at,
                    "subject_type": event.subject_type,
                    "subject_id": event.subject_id,
                }
                for event in events[:20]
            ],
            "has_more": len(events) > 20,
            "next_cursor": str(events[19].sequence) if len(events) > 20 else None,
        },
        "observation": {
            "observed_at": datetime.now(UTC),
            "evidence_available": bool(links),
        },
    }


def delivery_references(
    session: Session, tenant_id: str, commitment_id: str, family: str, query: str = ""
) -> dict[str, Any]:
    """Bound reference choices to the selected tenant and item before limiting."""
    from reality.db.core import HandlingUnit, Lot, SerialUnit

    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id, Commitment.id == commitment_id
        )
    )
    if commitment is None:
        raise NotFound("Delivery not found.")
    families = {
        "handling_unit": (HandlingUnit, HandlingUnit.nve),
        "lot": (Lot, Lot.lot_number),
        "serial_unit": (SerialUnit, SerialUnit.serial_number),
    }
    if family not in families:
        raise InvalidOperation("Unsupported delivery reference family.")
    model, label = families[family]
    statement = select(model.id, label).where(model.tenant_id == tenant_id)
    if model is not HandlingUnit:
        statement = statement.where(model.item_id == commitment.item_id)
    if query:
        statement = statement.where(
            or_(model.id.ilike(f"%{query}%"), label.ilike(f"%{query}%"))
        )
    rows = session.execute(statement.order_by(label, model.id).limit(51)).all()
    return {
        "items": [
            {"id": identity, "label": name or identity} for identity, name in rows[:50]
        ],
        "has_more": len(rows) > 50,
    }


MAX_SOURCE_PAYLOAD = 20_000


def delivery_evidence(
    session: Session, tenant_id: str, kind: str, record_id: str
) -> dict[str, Any]:
    """Inspect exact evidence/event records through their existing shortest links."""
    from reality.db.core import Fact, ImportJob, LedgerEntry, SourceRecord

    models = {
        "document_line": DocumentLine,
        "source_record": SourceRecord,
        "business_event": BusinessEvent,
    }
    if kind not in models:
        raise NotFound("Inspector record type not found.")
    model = models[kind]
    record = session.scalar(
        select(model).where(model.tenant_id == tenant_id, model.id == record_id)
    )
    if record is None:
        raise NotFound("Record not found.")

    from reality.services.inspector_presentation import display_parts, money

    def value(label, content, link=None, presentation=None):
        parts = display_parts(content if presentation is None else presentation)
        return {
            "label": label,
            "value": str(content) if content is not None else "—",
            **({"display_parts": parts} if parts else {}),
            "tone": "",
            "link": link,
        }

    rows = []
    linked_sections = []
    if kind == "document_line":
        rows.append(
            value(
                "Document",
                record.document_id,
                {"kind": "document", "id": record.document_id},
            )
        )
        if record.billed_document_line_id:
            rows.append(
                value(
                    "Referenced position",
                    record.billed_document_line_id,
                    {"kind": "document_line", "id": record.billed_document_line_id},
                )
            )
        document = session.scalar(
            select(Document).where(
                Document.tenant_id == tenant_id, Document.id == record.document_id
            )
        )
        for field in ("description", "quantity", "unit", "gross_amount"):
            if hasattr(record, field):
                rows.append(
                    value(
                        field.replace("_", " ").title(),
                        getattr(record, field),
                        presentation=money(record.gross_amount, document.currency)
                        if field == "gross_amount" and document
                        else None,
                    )
                )
    elif kind == "source_record":
        from reality.db.core import InterpretationOutcome, SourceSystem
        from reality.services.provenance import external_link

        system = session.scalar(
            select(SourceSystem).where(
                SourceSystem.tenant_id == tenant_id,
                SourceSystem.code == record.source_system,
            )
        )
        rows = [
            value("Source system", system.name if system else record.source_system),
            value("External reference", record.external_id),
            value("Source type", record.source_type),
            value("Version", record.version),
            value("Received", record.received_at),
        ]
        job = session.scalar(
            select(ImportJob).where(
                ImportJob.tenant_id == tenant_id,
                ImportJob.source_record_id == record.id,
            )
        )
        rows.append(value("Import job", job.status if job else "No import job"))
        # Terminal outcomes are appended per attempt; the latest is the current
        # answer. A source without one is labeled, never given a fabricated result.
        outcome = session.scalar(
            select(InterpretationOutcome)
            .where(
                InterpretationOutcome.tenant_id == tenant_id,
                InterpretationOutcome.source_record_id == record.id,
            )
            .order_by(InterpretationOutcome.attempt.desc())
            .limit(1)
        )
        rows.append(
            value("Interpretation", outcome.classification if outcome else "not_recorded")
        )
        if outcome and outcome.interpreter_name:
            rows.append(
                value(
                    "Interpreter",
                    f"{outcome.interpreter_name} {outcome.interpreter_version}".strip(),
                )
            )
        if outcome and outcome.reason_code:
            rows.append(value("Reason", outcome.reason_code))
        link = external_link(system, record)
        if link:
            rows.append(value("Open in source system", link))
        for linked_model, linked_kind, title in (
            (Party, "party", "Linked parties"),
            (Item, "item", "Linked items"),
            (Location, "location", "Linked locations"),
            (Movement, "movement", "Linked movements"),
            (Document, "document", "Linked documents"),
            (Fact, "fact", "Linked observations"),
            (LedgerEntry, "ledger_entry", "Linked ledger entries"),
            (BusinessEvent, "business_event", "Recorded events and their subjects"),
        ):
            linked = list(
                session.scalars(
                    select(linked_model)
                    .where(
                        linked_model.tenant_id == tenant_id,
                        linked_model.source_record_id == record.id,
                    )
                    .order_by(linked_model.id)
                    .limit(101)
                )
            )
            link_rows = [
                value(
                    "Record",
                    getattr(row, "number", None)
                    or getattr(row, "name", None)
                    or getattr(row, "event_type", None)
                    or getattr(row, "predicate", None)
                    or row.id,
                    {"kind": linked_kind, "id": row.id},
                )
                for row in linked[:100]
            ]
            if len(linked) > 100:
                link_rows.append(
                    value("Only the first 100 linked records are shown.", "")
                )
            if link_rows:
                linked_sections.append({"title": title, "rows": link_rows})
        if not linked_sections:
            linked_sections.append(
                {
                    "title": "Linked records",
                    "rows": [
                        value(
                            "No supported record links are recorded for this source.",
                            "",
                        )
                    ],
                }
            )
    else:
        rows = [
            value("Event", record.event_type),
            value("Recorded", record.recorded_at),
            value(
                "Subject",
                record.subject_id,
                {"kind": record.subject_type, "id": record.subject_id},
            ),
        ]
        if record.source_record_id:
            rows.append(
                value(
                    "Original source",
                    record.source_record_id,
                    {"kind": "source_record", "id": record.source_record_id},
                )
            )
    return {
        "kind": kind,
        "id": record.id,
        "title": kind.replace("_", " ").title(),
        "subtitle": "",
        "status": "Recorded",
        "metrics": [],
        "trail": [],
        "events": [],
        "sections": [{"title": "Recorded values", "rows": rows}, *linked_sections],
        "technical_rows": [value("Record ID", record.id)],
        # The retained payload is shown verbatim and bounded. Truncation is
        # announced rather than silent, because a payload that looks complete and
        # is not would be read as evidence of something the source never sent.
        "source_payload": (
            record.payload[:MAX_SOURCE_PAYLOAD] if kind == "source_record" else None
        ),
        "source_payload_truncated": (
            len(record.payload) > MAX_SOURCE_PAYLOAD
            if kind == "source_record"
            else False
        ),
    }
