"""Bounded current discovery for a future company manifest, never a valuation.

A PostgreSQL snapshot proves concurrent read consistency, not historical line
membership or financial completeness. Missing evidence stays in the census.
"""

from datetime import UTC, datetime

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    Document,
    DocumentLine,
    ImportJob,
    InterpretationOutcome,
    Item,
    Movement,
    SourceRecord,
)
from reality.services import core
from reality.services.costing import _hash, _sequence


class _Budget:
    def __init__(self, maximum: int):
        self.maximum = maximum
        self.used = 0

    def read(self, session: Session, statement) -> list:
        rows = (
            session.execute(statement.limit(self.maximum - self.used + 1))
            .mappings()
            .all()
        )
        self.used += len(rows)
        if self.used > self.maximum:
            raise core.InvalidOperation("Company cost census record limit exceeded.")
        return rows


def _events(tenant: str, kind: str):
    return (
        select(
            BusinessEvent.subject_id,
            func.count().label("event_count"),
            func.min(BusinessEvent.id).label("event_id"),
            func.min(BusinessEvent.sequence).label("event_sequence"),
        )
        .where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.subject_type == kind,
            BusinessEvent.event_type == f"{kind}.recorded",
        )
        .group_by(BusinessEvent.subject_id)
        .subquery()
    )


def _event_gap(kind: str, count: int | None) -> list[str]:
    if count == 1:
        return []
    return [f"{kind}_recorded_event_{'missing' if not count else 'ambiguous'}"]


def _capture(
    session: Session,
    tenant: str,
    effective_at: datetime,
    *,
    max_records: int = 100_000,
    _records: dict | None = None,
) -> dict:
    if not isinstance(effective_at, datetime) or effective_at.utcoffset() is None:
        raise core.InvalidOperation(
            "Company cost census requires an aware effective cutoff."
        )
    if type(max_records) is not int or not 1 <= max_records <= 100_000:
        raise core.InvalidOperation(
            "Company cost census record limit must be 1–100000."
        )
    if session.connection().get_isolation_level() != "REPEATABLE READ":
        raise core.InvalidOperation("Company cost census requires REPEATABLE READ.")
    with session.no_autoflush:
        core.get_tenant(session, tenant)
        snapshot, observed_at = session.execute(
            select(func.pg_current_snapshot(), func.statement_timestamp())
        ).one()
        watermark = _sequence(session, tenant)
        budget = _Budget(max_records)
        movement, item = Movement.__table__, Item.__table__
        events = _events(tenant, "movement")
        movements = budget.read(
            session,
            select(
                *movement.c,
                item.c.id.label("scoped_item_id"),
                events.c.event_count,
                events.c.event_id,
                events.c.event_sequence,
            )
            .outerjoin(
                item, (item.c.tenant_id == tenant) & (item.c.id == movement.c.item_id)
            )
            .outerjoin(events, events.c.subject_id == movement.c.id)
            .where(
                movement.c.tenant_id == tenant, movement.c.occurred_at <= effective_at
            )
            .order_by(movement.c.item_id, movement.c.id),
        )
        inventory = {}
        fingerprints = {}
        for record in movements:
            row = dict(record)
            if row["scoped_item_id"] is None:
                raise core.InvalidOperation(
                    "Company cost census contains an unavailable item."
                )
            key = row["item_id"]
            target = inventory.setdefault(
                key,
                {
                    "item_id": key,
                    "movement_ids": [],
                    "gaps": [],
                    "valuation": "not_assessed",
                },
            )
            target["movement_ids"].append(row["id"])
            target["gaps"].extend(_event_gap("movement", row["event_count"]))
            fingerprints.setdefault(key, []).append(_hash(row))
        for key, target in inventory.items():
            target["record_fingerprint"] = _hash(fingerprints[key])
            target["gaps"] = sorted(set(target["gaps"]))

        document, line = Document.__table__, DocumentLine.__table__
        unavailable_header = session.scalar(
            select(line.c.id)
            .outerjoin(
                document,
                (document.c.tenant_id == tenant)
                & (document.c.id == line.c.document_id),
            )
            .where(line.c.tenant_id == tenant, document.c.id.is_(None))
            .limit(1)
        )
        if unavailable_header is not None:
            raise core.InvalidOperation(
                "Company cost census contains an unavailable header."
            )
        events = _events(tenant, "document")
        headers = budget.read(
            session,
            select(
                *document.c,
                events.c.event_count,
                events.c.event_id,
                events.c.event_sequence,
            )
            .outerjoin(events, events.c.subject_id == document.c.id)
            .where(
                document.c.tenant_id == tenant,
                document.c.type.in_(("sales_invoice", "credit_note")),
            )
            .order_by(document.c.id),
        )
        header_by_id = {row["id"]: dict(row) for row in headers}
        lines = budget.read(
            session,
            select(*line.c)
            .join(
                document,
                (document.c.tenant_id == tenant)
                & (document.c.id == line.c.document_id),
            )
            .where(
                line.c.tenant_id == tenant,
                document.c.type.in_(("sales_invoice", "credit_note")),
            )
            .order_by(line.c.id),
        )
        contribution, populated = [], set()
        for record in lines:
            row = dict(record)
            header = header_by_id[row["document_id"]]
            populated.add(header["id"])
            contribution.append(
                {
                    "document_line_id": row["id"],
                    "document_id": header["id"],
                    "record_fingerprint": _hash({"header": header, "line": row}),
                    "valuation": "not_assessed",
                    "gaps": [
                        "economic_scope_unassessed",
                        "line_knowledge_history_unassessed",
                        *_event_gap("document", header["event_count"]),
                    ],
                }
            )
        document_gaps = [
            {"document_id": identity, "reason": "document_lines_missing"}
            for identity in header_by_id
            if identity not in populated
        ]

        source, job, outcome = (
            SourceRecord.__table__,
            ImportJob.__table__,
            InterpretationOutcome.__table__,
        )
        newer = source.alias("newer")
        sources = budget.read(
            session,
            select(
                source.c.id.label("source_record_id"),
                source.c.payload_hash,
                source.c.version,
                source.c.received_at,
                job.c.status.label("import_status"),
                outcome.c.id.label("outcome_id"),
                outcome.c.classification,
            )
            .outerjoin(
                job,
                (job.c.tenant_id == tenant) & (job.c.source_record_id == source.c.id),
            )
            .outerjoin(
                outcome,
                (outcome.c.tenant_id == tenant)
                & (outcome.c.source_record_id == source.c.id)
                & (outcome.c.import_job_id == job.c.id)
                & (outcome.c.attempt == job.c.attempts),
            )
            .where(
                source.c.tenant_id == tenant,
                ~exists(
                    select(1).where(
                        newer.c.tenant_id == tenant,
                        newer.c.source_system == source.c.source_system,
                        newer.c.source_type == source.c.source_type,
                        newer.c.external_id == source.c.external_id,
                        newer.c.version > source.c.version,
                    )
                ),
            )
            .order_by(source.c.id),
        )
        source_rows = [
            {
                **dict(row),
                "received_at": row["received_at"].isoformat(),
                "classification": row["classification"] or "unresolved",
            }
            for row in sources
        ]
        if _records is not None:
            _records.update(
                movement=[dict(row) for row in movements],
                document=[dict(row) for row in headers],
                line=[dict(row) for row in lines],
                source=source_rows,
            )
        return {
            "state": "discovered",
            "publication_eligible": False,
            "context": {
                "tenant_id": tenant,
                "effective_at": effective_at.astimezone(UTC).isoformat(),
                "snapshot": str(snapshot),
                "observed_at": observed_at.astimezone(UTC).isoformat(),
                "event_sequence": watermark,
            },
            "inventory": list(inventory.values()),
            "contribution": contribution,
            "document_gaps": document_gaps,
            "sources": source_rows,
            "counts": {
                "inventory_items": len(inventory),
                "contribution_candidates": len(contribution),
                "document_gaps": len(document_gaps),
                "active_sources": len(source_rows),
                "unresolved_sources": sum(
                    row["classification"] != "interpreted" for row in source_rows
                ),
                "input_records": budget.used,
            },
            "persistence": {"business_writes": False, "projection_writes": False},
        }
