"""Read-time sales-order history through held, tenant-scoped relationships."""

from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, or_, select, union
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    Commitment,
    Document,
    DocumentLine,
    Fact,
    LedgerEntry,
    Movement,
    Party,
    Reservation,
    SourceRecord,
    Tenant,
)
from reality.services.core import NotFound, _tenant_record, timeline_activity


def _order_label(
    session: Session, tenant_id: str, document: Document
) -> dict[str, Any]:
    party = session.scalar(
        select(Party.name).where(
            Party.tenant_id == tenant_id, Party.id == document.party_id
        )
    )
    return {"id": document.id, "number": document.number, "party": party or ""}


def search_order_journeys(
    session: Session, tenant_id: str, *, query: str = ""
) -> dict[str, Any]:
    """Bounded selector; numbers and customer names are labels, never identity."""
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    statement = (
        select(Document, Party.name)
        .outerjoin(
            Party, and_(Party.id == Document.party_id, Party.tenant_id == tenant_id)
        )
        .where(Document.tenant_id == tenant_id, Document.type == "sales_order")
    )
    if query.strip():
        needle = query.strip().lower()
        statement = statement.where(
            or_(
                func.lower(Document.number).contains(needle, autoescape=True),
                func.lower(Party.name).contains(needle, autoescape=True),
            )
        )
    rows = list(
        session.execute(
            statement.order_by(
                Document.ordered_at.desc().nulls_last(),
                Document.document_date.desc(),
                Document.id.desc(),
            ).limit(31)
        )
    )
    return {
        "orders": [
            {"id": doc.id, "number": doc.number, "party": name or ""}
            for doc, name in rows[:30]
        ],
        "has_more": len(rows) > 30,
    }


def order_journey(
    session: Session,
    tenant_id: str,
    order_id: str,
    *,
    limit: int = 100,
    before_sequence: int | None = None,
    after_sequence: int | None = None,
) -> dict[str, Any]:
    """Page exact member events before projection; never traverse shared references."""
    document = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.id == order_id,
            Document.type == "sales_order",
        )
    )
    if document is None:
        raise NotFound("Sales order not found.")

    def ids(model, *criteria):
        return select(model.id).where(model.tenant_id == tenant_id, *criteria)

    lines = ids(DocumentLine, DocumentLine.document_id == order_id)
    commitments = ids(
        Commitment,
        or_(
            Commitment.document_line_id.in_(lines),
            and_(
                Commitment.document_line_id.is_(None),
                Commitment.document_id == order_id,
            ),
        ),
    )
    members = {
        "document": ids(Document, Document.id == order_id),
        "document_line": lines,
        "commitment": commitments,
        "reservation": ids(Reservation, Reservation.commitment_id.in_(commitments)),
        "movement": ids(Movement, Movement.commitment_id.in_(commitments)),
        "ledger_entry": ids(LedgerEntry, LedgerEntry.document_id == order_id),
    }
    facts = ids(
        Fact,
        or_(
            *(
                and_(Fact.subject_type == kind, Fact.subject_id.in_(selection))
                for kind, selection in members.items()
            )
        ),
    )
    members["fact"] = facts
    source_ids = union(
        *(
            select(model.source_record_id).where(
                model.tenant_id == tenant_id,
                model.id.in_(members[kind]),
                model.source_record_id.is_not(None),
            )
            for kind, model in (
                ("document", Document),
                ("movement", Movement),
                ("ledger_entry", LedgerEntry),
                ("fact", Fact),
            )
        )
    )
    members["source_record"] = ids(SourceRecord, SourceRecord.id.in_(source_ids))
    members["posting_group"] = select(LedgerEntry.posting_group_id).where(
        LedgerEntry.tenant_id == tenant_id,
        LedgerEntry.document_id == order_id,
        LedgerEntry.posting_group_id != "",
    )
    subject_filter = or_(
        *(
            and_(
                BusinessEvent.subject_type == kind,
                BusinessEvent.subject_id.in_(selection),
            )
            for kind, selection in members.items()
        )
    )
    page = timeline_activity(
        session,
        tenant_id,
        hours=0,
        limit=max(1, min(limit, 250)),
        before_sequence=before_sequence,
        after_sequence=after_sequence,
        _subject_filter=subject_filter,
    )

    # Only loaded subjects need links. Each link comes from a held FK, not payload
    # heuristics or temporal adjacency. Unloaded parents remain undated references.
    edges: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    models = {
        "document": Document,
        "document_line": DocumentLine,
        "commitment": Commitment,
        "reservation": Reservation,
        "movement": Movement,
        "ledger_entry": LedgerEntry,
        "fact": Fact,
    }
    for kind, model in models.items():
        loaded = {
            event["subject_id"]
            for event in page["events"]
            if event["subject_type"] == kind
        }
        if not loaded:
            continue
        for row in session.scalars(
            select(model).where(model.tenant_id == tenant_id, model.id.in_(loaded))
        ):
            parents: list[tuple[str, str | None, str]] = []
            if kind == "document_line":
                parents.append(("document", row.document_id, "Document line"))
            elif kind == "commitment":
                parents.append(
                    ("document_line", row.document_line_id, "Evidence")
                    if row.document_line_id
                    else ("document", row.document_id, "Evidence")
                )
            elif kind in {"reservation", "movement"}:
                parents.append(("commitment", row.commitment_id, "Commitment"))
            elif kind == "ledger_entry":
                parents.append(("document", row.document_id, "Evidence"))
            elif kind == "fact":
                parents.append((row.subject_type, row.subject_id, "Subject"))
            if getattr(row, "source_record_id", None):
                parents.append(
                    ("source_record", row.source_record_id, "Original source")
                )
            for parent_kind, parent_id, label in parents:
                if parent_id:
                    edges[(parent_kind, parent_id, kind, row.id)] = {
                        "from": {"kind": parent_kind, "id": parent_id},
                        "to": {"kind": kind, "id": row.id},
                        "label": label,
                    }
    posting_groups = {
        event["subject_id"]
        for event in page["events"]
        if event["subject_type"] == "posting_group"
    }
    links_truncated = False
    if posting_groups:
        entries = list(
            session.scalars(
                select(LedgerEntry)
                .where(
                    LedgerEntry.tenant_id == tenant_id,
                    LedgerEntry.document_id == order_id,
                    LedgerEntry.posting_group_id.in_(posting_groups),
                )
                .order_by(LedgerEntry.id)
                .limit(251)
            )
        )
        links_truncated = len(entries) > 250
        for entry in entries[:250]:
            edges[
                ("posting_group", entry.posting_group_id, "ledger_entry", entry.id)
            ] = {
                "from": {"kind": "posting_group", "id": entry.posting_group_id},
                "to": {"kind": "ledger_entry", "id": entry.id},
                "label": "Ledger entries",
            }
    return {
        "order": _order_label(session, tenant_id, document),
        "events": page["events"],
        "edges": list(edges.values()),
        "has_more": page["has_more"],
        "links_truncated": links_truncated,
    }
