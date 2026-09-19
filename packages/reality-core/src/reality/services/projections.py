from __future__ import annotations

import json
from collections import defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache, wraps
from typing import Any

from sqlalchemy import cast, delete, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    Commitment,
    CommitmentHold,
    Document,
    DocumentLine,
    Item,
    Movement,
    Party,
    PartyHold,
    ProjectionCheckpoint,
    ProjectionRow,
    Reservation,
    SourceRecord,
    Tenant,
    TenantEventProgress,
    now,
    uid,
)
from reality.domain.calendar import day_text

PROJECTION_VERSION = 4
FULFILLMENT_QUEUE = "fulfillment_queue"
FULFILLMENT_BLOCKERS = "fulfillment_blockers"
ITEM_SUPPLY_DEMAND = "item_supply_demand"
TENANT_USAGE = "tenant_usage"
INVENTORY = "inventory"
EXCEPTIONS = "exceptions"
# Compatibility alias for callers created before the terminology correction.
ISSUES = EXCEPTIONS
COMMITMENT_REGISTER = "commitment_register"
DOCUMENT_REGISTER = "document_register"
OPEN_FINANCIAL_ITEMS = "open_financial_items"
PAYMENTS = "payments"
JOURNAL = "journal"
TIMELINE = "timeline"
PRICE_RESOLUTION = "price_resolution"
OPERATIONAL_PROJECTIONS = (
    FULFILLMENT_QUEUE,
    FULFILLMENT_BLOCKERS,
    ITEM_SUPPLY_DEMAND,
    TENANT_USAGE,
    INVENTORY,
    ISSUES,
    COMMITMENT_REGISTER,
    DOCUMENT_REGISTER,
    OPEN_FINANCIAL_ITEMS,
    PAYMENTS,
    JOURNAL,
    TIMELINE,
    PRICE_RESOLUTION,
)
PRIORITY_RANK = {"low": 0, "normal": 1, "high": 2, "critical": 3}


def _read_without_flush(function):
    """A read must not flush unrelated pending writes in a caller-owned session."""

    @wraps(function)
    def read(session: Session, *args: Any, **kwargs: Any):
        with session.no_autoflush:
            return function(session, *args, **kwargs)

    return read


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"Unsupported projection value: {type(value).__name__}")


def _dump(value: Any) -> str:
    return json.dumps(
        value, default=_json_default, sort_keys=True, separators=(",", ":")
    )


def _latest_sequence(session: Session, tenant_id: str) -> int:
    return int(
        session.scalar(
            select(func.coalesce(func.max(BusinessEvent.sequence), 0)).where(
                BusinessEvent.tenant_id == tenant_id
            )
        )
        or 0
    )


def _replace_rows(
    session: Session,
    tenant_id: str,
    projection_name: str,
    rows: dict[str, dict[str, Any]],
    source_sequence: int,
    covers: frozenset[str] | None = None,
    observed: int | None = None,
) -> None:
    """Write a derivation's rows; `covers` says how much of the projection it speaks for.

    `None` means the whole projection was evaluated, so a stored row the derivation
    did not produce no longer belongs and is removed. A narrowed derivation passes the
    record keys it was authoritative for (spec 241 FR-003): rows inside that set but
    absent from the result are removed, rows outside it are left exactly as they are,
    because nothing was learned about them. Loading only the covered rows is where a
    narrowed refresh stops paying for the company.
    """
    stored = select(ProjectionRow).where(
        ProjectionRow.tenant_id == tenant_id,
        ProjectionRow.projection_name == projection_name,
    )
    if covers is not None:
        stored = stored.where(ProjectionRow.record_key.in_(covers | set(rows)))
    existing = {row.record_key: row for row in session.scalars(stored)}
    stamp = now()
    for record_key, payload in rows.items():
        row = existing.pop(record_key, None)
        if row is None:
            row = ProjectionRow(
                id=uid("prj"),
                tenant_id=tenant_id,
                projection_name=projection_name,
                record_key=record_key,
                payload="{}",
            )
            session.add(row)
        row.projection_version = PROJECTION_VERSION
        row.payload = _dump(payload)
        row.source_event_sequence = source_sequence
        row.updated_at = stamp
    if existing:
        session.execute(
            delete(ProjectionRow).where(
                ProjectionRow.tenant_id == tenant_id,
                ProjectionRow.projection_name == projection_name,
                ProjectionRow.record_key.in_(existing),
            )
        )
    checkpoint = session.scalar(
        select(ProjectionCheckpoint).where(
            ProjectionCheckpoint.tenant_id == tenant_id,
            ProjectionCheckpoint.projection_name == projection_name,
        )
    )
    if checkpoint is None:
        checkpoint = ProjectionCheckpoint(
            id=uid("prc"), tenant_id=tenant_id, projection_name=projection_name
        )
        session.add(checkpoint)
    checkpoint.projection_version = PROJECTION_VERSION
    checkpoint.last_event_sequence = source_sequence
    if observed is not None:
        checkpoint.observed_event_sequence = observed
    checkpoint.status = "ready"
    checkpoint.error = ""
    checkpoint.updated_at = stamp


def _inventory_rows(
    session: Session, tenant_id: str, item_ids: frozenset[str] | set[str] | None = None
) -> dict[str, dict[str, Any]]:
    """Stock, for the whole company or for named articles alone."""
    from reality.services.core import inventory_rows

    return {
        row["item"].id: {
            "item_id": row["item"].id,
            "item": row["item"].name,
            "sku": row["item"].sku,
            **quantity_unit(row["item"]),
            "aggregation": "item_all_locations",
            "physical": row["physical"],
            "reserved": row["reserved"],
            "available": row["available"],
            "incoming": row["incoming"],
            "projected": row["projected"],
            "receipt_ids": [movement.id for movement in row["receipts"]],
            "issue_ids": [movement.id for movement in row["issues"]],
        }
        for row in inventory_rows(
            session, tenant_id, item_ids=set(item_ids) if item_ids is not None else None
        )
    }


def _document_register_rows(
    session: Session,
    tenant_id: str,
    document_ids: frozenset[str] | set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """The document register, for the whole company or for named documents alone."""
    from reality.services.core import document_rows

    return {
        document.id: {
            "document_id": document.id,
            "type": document.type,
            "number": document.number,
            "document_date": day_text(document.document_date),
            "party_id": document.party_id,
            "gross_amount": document.gross_amount,
            "currency": document.currency,
            "source_record_id": source.id if source else None,
            "source_system": source.source_system if source else None,
            "external_id": source.external_id if source else None,
            "line_ids": [line.id for line in lines_],
            "commitment_ids": [commitment.id for commitment in commitments_],
        }
        for document, source, lines_, commitments_ in document_rows(
            session, tenant_id, document_ids
        )
    }


def _journal_row(entry) -> dict[str, Any]:
    """One journal row, so the whole company and one posting group agree on its shape."""
    return {
        "ledger_entry_id": entry.id,
        "posting_group_id": entry.posting_group_id,
        "account": entry.account,
        "account_id": entry.account_id,
        "account_code": entry.account_record.code,
        "party_id": entry.party_id,
        "document_id": entry.document_id,
        "debit_credit": entry.debit_credit,
        "amount": entry.amount,
        "currency": entry.currency,
        "effective_at": entry.effective_at,
        "source_record_id": entry.source_record_id,
    }


def quantity_unit(
    item: Item | None, line: DocumentLine | None = None
) -> dict[str, Any]:
    unit = item.unit or None if item else None
    line_unit = line.unit or None if line else None
    return {
        "unit": unit,
        "unit_status": "known" if unit else "unknown",
        "quantity_basis": "item_unit",
        "document_line_unit": line_unit,
        "unit_mismatch": unit != line_unit if unit and line_unit else None,
    }


def _build_financial_rows(
    session: Session, tenant_id: str
) -> dict[str, dict[str, Any]]:
    from reality.services.core import financial_open_items

    open_items_projection = {}
    for row in financial_open_items(session, tenant_id):
        document = row["document"]
        open_items_projection[document.id] = {
            "document_id": document.id,
            "number": document.number,
            "document_type": document.type,
            "origin": row["origin"],
            "coverage_kind": row["coverage_kind"],
            "flow": "receivable"
            if row["control"].account == "accounts_receivable"
            else "payable",
            "original_due_date": row["original_due_date"].isoformat()
            if row["original_due_date"]
            else None,
            "document_date": day_text(document.document_date),
            "party_id": document.party_id,
            "party": row["party"],
            "gross": document.gross_amount,
            "settled": row["settled"],
            "open": row["open"],
            "currency": document.currency,
            "status": row["status"],
        }
    return open_items_projection


def _build_payment_rows(session: Session, tenant_id: str) -> dict[str, dict[str, Any]]:
    from reality.services.core import payment_rows

    payment_projection = {}
    for row in payment_rows(session, tenant_id):
        cash = row["cash_entry"]
        payment_projection[cash.id] = {
            "payment_entry_id": cash.id,
            "posting_group_id": cash.posting_group_id,
            "document_id": row["document"].id,
            "document_number": row["document"].number,
            "party_id": cash.party_id,
            "party": row["party"],
            "direction": row["direction"],
            "amount": cash.amount,
            "allocated": row["allocated"],
            "unallocated": row["unallocated"],
            "currency": cash.currency,
            "effective_at": cash.effective_at,
        }
    return payment_projection


def _build_operational_rows(
    session: Session, tenant_id: str, names: set[str] | None = None
) -> dict[str, dict[str, dict[str, Any]]]:
    # Imported here to keep the authoritative domain services independent from
    # their disposable read cache.
    from reality.services.core import (
        commitment_rows,
        commitment_terms,
        inventory_rows,
        journal_rows,
        tenant_usage_summaries,
        timeline,
    )

    selected = set(OPERATIONAL_PROJECTIONS) if names is None else names
    result = {}
    if selected & {
        FULFILLMENT_QUEUE,
        FULFILLMENT_BLOCKERS,
        ITEM_SUPPLY_DEMAND,
        COMMITMENT_REGISTER,
    }:
        items = {
            row.id: row
            for row in session.scalars(select(Item).where(Item.tenant_id == tenant_id))
        }
        document_lines = {
            row.id: row
            for row in session.scalars(
                select(DocumentLine).where(DocumentLine.tenant_id == tenant_id)
            )
        }
    # Spec 181 FR-003: the queue, the blockers and supply and demand are about work
    # that is still open, so they are given the promises that are still open and
    # nothing else. The commitment register is a register — it shows a promise that was
    # cancelled — so when it is in this batch the terms are read for the whole company
    # and shared. A closed promise excluded here is excluded by predicate, never
    # fetched and skipped.
    working_set = selected & {
        FULFILLMENT_QUEUE,
        FULFILLMENT_BLOCKERS,
        ITEM_SUPPLY_DEMAND,
    }
    customer_commitments = (
        list(
            session.scalars(
                select(Commitment).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.type == "customer_delivery",
                    Commitment.status == "open",
                )
            )
        )
        if working_set
        else []
    )
    terms = (
        commitment_terms(session, tenant_id)
        if COMMITMENT_REGISTER in selected
        else commitment_terms(
            session, tenant_id, [row.id for row in customer_commitments]
        )
        if working_set
        else {}
    )
    if working_set:
        parties = {
            row.id: row
            for row in session.scalars(
                select(Party).where(Party.tenant_id == tenant_id)
            )
        }
        # Only the orders those open promises were made on, and only their source
        # records: a company's finished history is not part of its open work.
        open_document_ids = {row.document_id for row in customer_commitments} - {None}
        documents = (
            {
                row.id: row
                for row in session.scalars(
                    select(Document).where(
                        Document.tenant_id == tenant_id,
                        Document.id.in_(open_document_ids),
                    )
                )
            }
            if open_document_ids
            else {}
        )
        open_source_ids = {row.source_record_id for row in documents.values()} - {None}
        sources = (
            {
                row.id: row
                for row in session.scalars(
                    select(SourceRecord).where(
                        SourceRecord.tenant_id == tenant_id,
                        SourceRecord.id.in_(open_source_ids),
                    )
                )
            }
            if open_source_ids
            else {}
        )
        active_reservations: dict[str, Decimal] = defaultdict(Decimal)
        for reservation in session.scalars(
            select(Reservation).where(
                Reservation.tenant_id == tenant_id, Reservation.status == "active"
            )
        ):
            active_reservations[reservation.commitment_id] += reservation.quantity
        commitment_holds = {
            hold.commitment_id: hold
            for hold in session.scalars(
                select(CommitmentHold).where(
                    CommitmentHold.tenant_id == tenant_id,
                    CommitmentHold.released_at.is_(None),
                )
            )
        }
        party_holds = {
            hold.party_id: hold
            for hold in session.scalars(
                select(PartyHold).where(
                    PartyHold.tenant_id == tenant_id,
                    PartyHold.hold_type == "delivery",
                    PartyHold.released_at.is_(None),
                )
            )
        }
        grouped: dict[str, list[Commitment]] = defaultdict(list)
        for commitment in customer_commitments:
            grouped[commitment.document_id or commitment.id].append(commitment)

        queue: dict[str, dict[str, Any]] = {}
        blockers: dict[str, dict[str, Any]] = {}
        blocked_orders_by_item: dict[str, set[str]] = defaultdict(set)
        demand_by_item: dict[str, Decimal] = defaultdict(Decimal)
        uncovered_by_item: dict[str, Decimal] = defaultdict(Decimal)
        for record_key, commitments in grouped.items():
            document = documents.get(commitments[0].document_id or "")
            source = sources.get(document.source_record_id or "") if document else None
            lines = []
            order_blockers: list[dict[str, Any]] = []
            for commitment in commitments:
                open_value = terms[commitment.id].open
                reserved = active_reservations[commitment.id]
                shortage = max(Decimal(0), open_value - reserved)
                if not commitment.item_id:
                    continue
                demand_by_item[commitment.item_id] += open_value
                reasons: list[tuple[str, str]] = []
                if hold := commitment_holds.get(commitment.id):
                    reasons.append(("commitment_hold", hold.reason_code))
                if hold := party_holds.get(commitment.to_party_id or ""):
                    reasons.append(("party_delivery_hold", hold.reason_code))
                if shortage > 0:
                    reasons.append(
                        ("insufficient_reservation", "stock not fully reserved")
                    )
                    uncovered_by_item[commitment.item_id] += shortage
                item = items.get(commitment.item_id or "")
                line = {
                    "commitment_id": commitment.id,
                    "item_id": commitment.item_id,
                    "item": item.name if item else commitment.item_id,
                    "sku": item.sku if item else "",
                    "quantity": terms[commitment.id].quantity,
                    "original_quantity": commitment.quantity,
                    "open_quantity": open_value,
                    "reserved_quantity": reserved,
                    "shortage_quantity": shortage,
                    "due_at": terms[commitment.id].due_at,
                    "original_due_at": commitment.due_at,
                    "location_id": commitment.location_id,
                    "blocking_reasons": [reason for reason, _ in reasons],
                    **quantity_unit(
                        item, document_lines.get(commitment.document_line_id)
                    ),
                }
                lines.append(line)
                for reason, detail in reasons:
                    blocker_key = f"{commitment.id}:{reason}"
                    blocker = {
                        "blocker_id": blocker_key,
                        "blocker_type": reason,
                        "detail": detail,
                        "order_key": record_key,
                        "document_id": commitment.document_id,
                        "document_number": document.number if document else None,
                        "commitment_id": commitment.id,
                        "item_id": commitment.item_id,
                        "item": item.name if item else commitment.item_id,
                        "shortage_quantity": shortage
                        if reason == "insufficient_reservation"
                        else "0",
                        "due_at": terms[commitment.id].due_at,
                        **quantity_unit(
                            item, document_lines.get(commitment.document_line_id)
                        ),
                    }
                    blockers[blocker_key] = blocker
                    order_blockers.append(blocker)
                    blocked_orders_by_item[commitment.item_id].add(record_key)
            party_id = document.party_id if document else commitments[0].to_party_id
            party = parties.get(party_id or "")
            queue[record_key] = {
                "order_key": record_key,
                "document_id": document.id if document else None,
                "document_number": document.number if document else None,
                "source_system": source.source_system if source else None,
                "external_order_id": source.external_id if source else None,
                "party_id": party_id,
                "party": party.name if party else party_id,
                "due_at": min(
                    (line["due_at"] for line in lines if line["due_at"]), default=None
                ),
                "priority": max(
                    (row.priority for row in commitments),
                    key=lambda value: PRIORITY_RANK.get(value, 1),
                    default="normal",
                ),
                "readiness": "ready" if not order_blockers else "blocked",
                "ship_ready": not order_blockers,
                "blocking_reasons": sorted(
                    {row["blocker_type"] for row in order_blockers}
                ),
                "lines": lines,
            }

        supply_demand: dict[str, dict[str, Any]] = {}
        for row in inventory_rows(session, tenant_id):
            item = row["item"]
            supply_demand[item.id] = {
                "item_id": item.id,
                "item": item.name,
                "sku": item.sku,
                **quantity_unit(item),
                "physical": row["physical"],
                "reserved": row["reserved"],
                "available": row["available"],
                "incoming": row["incoming"],
                "open_customer_demand": demand_by_item[item.id],
                "uncovered_demand": uncovered_by_item[item.id],
                "projected": row["projected"],
                "blocked_order_count": len(blocked_orders_by_item[item.id]),
                "blocked_order_keys": sorted(blocked_orders_by_item[item.id]),
            }
        for name, rows in (
            (FULFILLMENT_QUEUE, queue),
            (FULFILLMENT_BLOCKERS, blockers),
            (ITEM_SUPPLY_DEMAND, supply_demand),
        ):
            if name in selected:
                result[name] = rows
    if INVENTORY in selected:
        result[INVENTORY] = _inventory_rows(session, tenant_id)
    if EXCEPTIONS in selected:
        from reality.services.exceptions import operational_exception_rows

        # The stored rows keep the derivation's canonical order as a position, so a
        # reader paging through them shows the same sequence the live queue would.
        exception_projection = {
            row["id"]: {**row, "position": position}
            for position, row in enumerate(
                operational_exception_rows(session, tenant_id)
            )
        }
        result[EXCEPTIONS] = exception_projection
    if COMMITMENT_REGISTER in selected:
        commitment_projection = {}
        for (
            commitment,
            commitment_risk,
            counterparty,
            item_name,
            reserved,
        ) in commitment_rows(session, tenant_id):
            commitment_projection[commitment.id] = {
                "commitment_id": commitment.id,
                "type": commitment.type,
                "status": commitment.status,
                "document_id": commitment.document_id,
                "item_id": commitment.item_id,
                "item": item_name,
                "counterparty": counterparty,
                "quantity": terms[commitment.id].quantity,
                "original_quantity": commitment.quantity,
                **quantity_unit(
                    items.get(commitment.item_id),
                    document_lines.get(commitment.document_line_id),
                ),
                "reserved": reserved,
                "open_quantity": terms[commitment.id].open,
                "due_at": terms[commitment.id].due_at,
                "original_due_at": commitment.due_at,
                "priority": commitment.priority,
                "risk": commitment_risk,
            }
        result[COMMITMENT_REGISTER] = commitment_projection
    if DOCUMENT_REGISTER in selected:
        result[DOCUMENT_REGISTER] = _document_register_rows(session, tenant_id)
    if JOURNAL in selected:
        result[JOURNAL] = {
            entry.id: _journal_row(entry) for entry in journal_rows(session, tenant_id)
        }
    if TIMELINE in selected:
        timeline_projection = {
            f"{occurred_at.isoformat()}:{record_type}:{record_id}": {
                "occurred_at": occurred_at,
                "record_type": record_type,
                "title": title,
                "record_id": record_id,
            }
            for occurred_at, record_type, title, record_id in timeline(
                session, tenant_id
            )
        }
        result[TIMELINE] = timeline_projection
    if OPEN_FINANCIAL_ITEMS in selected:
        result[OPEN_FINANCIAL_ITEMS] = _build_financial_rows(session, tenant_id)
    if PAYMENTS in selected:
        result[PAYMENTS] = _build_payment_rows(session, tenant_id)
    if TENANT_USAGE in selected:
        result[TENANT_USAGE] = {
            tenant_id: tenant_usage_summaries(session, tenant_id=tenant_id)[tenant_id]
        }
    if PRICE_RESOLUTION in selected:
        result[PRICE_RESOLUTION] = {}
    return result


def derive_projection_rows(
    session: Session, tenant_id: str, projection_name: str
) -> dict[str, dict[str, Any]]:
    """Use the canonical derivation without creating or refreshing cache records."""
    from reality.services.core import get_tenant

    get_tenant(session, tenant_id)
    if projection_name not in OPERATIONAL_PROJECTIONS:
        raise ValueError("Unknown operational projection.")
    with session.no_autoflush:
        rows = (
            _build_financial_rows(session, tenant_id)
            if projection_name == OPEN_FINANCIAL_ITEMS
            else _build_payment_rows(session, tenant_id)
            if projection_name == PAYMENTS
            else _build_operational_rows(session, tenant_id, {projection_name})[
                projection_name
            ]
        )
        return json.loads(_dump(rows))


MATERIALIZED_PROJECTIONS = tuple(
    name for name in OPERATIONAL_PROJECTIONS if name != PRICE_RESOLUTION
)
#: Projections whose rows change because the clock moved, with no event to announce
#: it, and which are therefore refreshed on a cadence rather than on a change.
#:
#: Only exceptions belong here. An exception judges a promise against the moment it is
#: read — overdue, standing so many days — so its rows move without anybody doing
#: anything. The commitment register and the tenant usage summary were on this list
#: too, and measurement says they do not belong: a promise's risk is `reserved < open`
#: and its date in force is the last one stated, while a usage summary is counts and a
#: latest timestamp. Neither reads the clock, so rebuilding them every minute was work
#: that could not change an answer. `test_clock_sensitivity.py` keeps that honest: if
#: one of them starts reading the clock, it fails and the name goes back on this list.
TIME_SENSITIVE_PROJECTIONS = (EXCEPTIONS,)


@lru_cache(maxsize=1)
def projection_dependencies() -> dict[str, frozenset[str]]:
    """Executable dependency catalog; unrecognized event types invalidate all."""
    import yaml

    from reality.config import config_text

    names = {
        entry["name"]: entry["materialized_as"]
        for entry in yaml.safe_load(config_text("projection_catalog.yaml"))[
            "projections"
        ]
    }
    return {
        event["type"]: frozenset(names[name] for name in event["invalidates"])
        | {TENANT_USAGE}
        for event in yaml.safe_load(config_text("business_event_catalog.yaml"))[
            "events"
        ]
    }


def relevant_event_target(tenant_id: str, name: str):
    dependencies = projection_dependencies()
    types = [kind for kind, affected in dependencies.items() if name in affected]
    return (
        select(func.coalesce(func.max(BusinessEvent.sequence), 0))
        .where(
            BusinessEvent.tenant_id == tenant_id,
            or_(
                BusinessEvent.event_type.in_(types),
                BusinessEvent.event_type.not_in(tuple(dependencies)),
            ),
        )
        .scalar_subquery()
    )


#: Why each projection of the last refresh did or did not narrow, for whoever is
#: measuring. Spec 241 SC-004: a feature whose builders all decline must look like
#: that, not like a success. `None` against a name means it narrowed.
NARROWING: ContextVar[dict | None] = ContextVar("projection_narrowing", default=None)


@contextmanager
def narrowing_report():
    """Collect why each projection narrowed or did not, for one refresh."""
    report: dict[str, str | None] = {}
    token = NARROWING.set(report)
    try:
        yield report
    finally:
        NARROWING.reset(token)


@dataclass(frozen=True)
class ChangeSet:
    """The records a refresh has to account for, or the reason it cannot narrow.

    Spec 241 FR-001. `subjects` maps a subject type to the ids of the records whose
    business events fall between the stored checkpoint and the target sequence. A
    builder given one may derive only those records' rows; a builder that does not
    know how to narrow by them says so and evaluates the company, which is FR-002
    and always correct.

    `reason` names why narrowing is off when it is, so that "everything fell back"
    is a visible state rather than a silent one (SC-004).
    """

    subjects: dict[str, frozenset[str]] | None
    reason: str | None = None

    @property
    def narrowed(self) -> bool:
        return self.subjects is not None

    def ids(self, subject_type: str) -> frozenset[str]:
        return (self.subjects or {}).get(subject_type, frozenset())


#: Above this many changed records, deriving each one costs more than deriving the
#: company: the narrowed path issues work per subject and the full path does not.
#: A refresh that has fallen this far behind is a rebuild wearing another name.
MAX_NARROWED_SUBJECTS = 200


def change_set(
    session: Session, tenant_id: str, name: str, since: int, until: int
) -> ChangeSet:
    """What changed for this projection between two sequences.

    Narrowing is refused, rather than guessed, in three cases: nothing is known about
    an event type the catalog does not list, the refresh is time-sensitive and ran
    because the clock moved rather than because a record did, and too many records
    changed to be worth visiting one at a time.
    """
    if since >= until:
        return ChangeSet(None, "no new events")
    dependencies = projection_dependencies()
    types = [kind for kind, affected in dependencies.items() if name in affected]
    rows = session.execute(
        select(
            BusinessEvent.event_type,
            BusinessEvent.subject_type,
            BusinessEvent.subject_id,
        )
        .where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.sequence > since,
            BusinessEvent.sequence <= until,
        )
        .limit(MAX_NARROWED_SUBJECTS + 1)
    ).all()
    if len(rows) > MAX_NARROWED_SUBJECTS:
        return ChangeSet(None, "too many changes to visit one at a time")
    subjects: dict[str, set[str]] = {}
    for event_type, subject_type, subject_id in rows:
        if event_type not in dependencies:
            # The catalog does not say what this event touches, so nothing may be
            # assumed about what it left unchanged.
            return ChangeSet(None, f"unknown event type {event_type!r}")
        if event_type not in types:
            continue
        subjects.setdefault(subject_type, set()).add(subject_id)
    return ChangeSet({kind: frozenset(ids) for kind, ids in subjects.items()})


@dataclass(frozen=True)
class NarrowedRows:
    """What a narrowed builder produced, and how much of the projection it speaks for.

    `covers` is the set of record keys the builder was authoritative for in this
    refresh. A key inside it that is missing from `rows` has genuinely gone; a key
    outside it was not looked at and must survive untouched (FR-003).
    """

    rows: dict[str, dict[str, Any]]
    covers: frozenset[str]


def _narrowed_journal(
    session: Session, tenant_id: str, changes: ChangeSet
) -> NarrowedRows | str:
    """The journal, for the posting groups and accounts that changed (FR-002).

    Four event types reach this projection. Two name a `posting_group`, one names a
    `subledger_account` whose code every entry on it prints, and `payments.run` names
    the tenant — which is not a record this builder can visit, so it declines and the
    company is evaluated.

    A reversal is the trap here. `ledger.reversed` names the group that *was*
    reversed, while the entries it creates belong to a new reversing group that no
    event names. Narrowing on the subject alone would leave those entries out of the
    journal, so the stored reversal relation is followed to find them. That is a
    recorded link, not an assumption about what the producer happens to do today.
    """
    from reality.db.core import LedgerEntry, LedgerReversal

    known = {"posting_group", "subledger_account"}
    unknown = sorted(set(changes.subjects or {}) - known)
    if unknown:
        return f"journal cannot narrow by {unknown[0]}"
    groups = set(changes.ids("posting_group"))
    accounts = set(changes.ids("subledger_account"))
    if not groups and not accounts:
        return "no journal subject changed"
    if groups:
        for original, reversing in session.execute(
            select(
                LedgerReversal.original_posting_group_id,
                LedgerReversal.reversing_posting_group_id,
            ).where(
                LedgerReversal.tenant_id == tenant_id,
                or_(
                    LedgerReversal.original_posting_group_id.in_(groups),
                    LedgerReversal.reversing_posting_group_id.in_(groups),
                ),
            )
        ).all():
            groups.update((original, reversing))
    reach = []
    if groups:
        reach.append(LedgerEntry.posting_group_id.in_(groups))
    if accounts:
        reach.append(LedgerEntry.account_id.in_(accounts))
    entries = list(
        session.scalars(
            select(LedgerEntry)
            .where(LedgerEntry.tenant_id == tenant_id, or_(*reach))
            .order_by(LedgerEntry.effective_at.desc(), LedgerEntry.posting_group_id)
        )
    )
    rows = json.loads(_dump({entry.id: _journal_row(entry) for entry in entries}))
    # A ledger entry is never deleted — a correction is a reversing entry — so the
    # entries read here are exactly the stored rows this refresh speaks for.
    return NarrowedRows(rows, frozenset(rows))


#: A change set names records, but one record can reach many rows: every document of a
#: party, every entry on an account. Past this many resolved rows a narrowed refresh is
#: no longer obviously the cheaper path, so the builder declines and the company is
#: evaluated in the four sequential reads it already knows how to do. The number is a
#: declared ceiling rather than a measurement; lower it when there is one.
MAX_NARROWED_ROWS = 2_000


def _narrowed_document_register(
    session: Session, tenant_id: str, changes: ChangeSet
) -> NarrowedRows | str:
    """The document register, for the documents the changed records belong to.

    Five subject types reach this projection and each resolves to documents without
    guessing: a document is itself, a commitment and a source record name the document
    they belong to, and a party or a payment term name every document that cites them.

    That last pair is the reason `MAX_NARROWED_ROWS` exists. One `party.updated` for a
    customer with the company's whole order history resolves to the whole company, and
    a narrowed path that visits everything is the slow path with extra steps.
    """
    known = {"document", "commitment", "source_record", "party", "payment_term"}
    unknown = sorted(set(changes.subjects or {}) - known)
    if unknown:
        return f"document register cannot narrow by {unknown[0]}"
    documents = set(changes.ids("document"))
    reach = []
    if parties := changes.ids("party"):
        reach.append(
            or_(Document.party_id.in_(parties), Document.ship_to_party_id.in_(parties))
        )
    if sources := changes.ids("source_record"):
        reach.append(Document.source_record_id.in_(sources))
    if terms := changes.ids("payment_term"):
        reach.append(Document.payment_term_id.in_(terms))
    if reach:
        documents.update(
            session.scalars(
                select(Document.id).where(Document.tenant_id == tenant_id, or_(*reach))
            )
        )
    if commitments := changes.ids("commitment"):
        # A commitment's document is set when it is made and never moved, so the
        # document it names now is the only row it has ever been part of.
        documents.update(
            session.scalars(
                select(Commitment.document_id).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.id.in_(commitments),
                    Commitment.document_id.is_not(None),
                )
            )
        )
    if not documents:
        return "no document register subject resolved to a document"
    if len(documents) > MAX_NARROWED_ROWS:
        return f"{len(documents)} documents is not worth visiting one at a time"
    rows = json.loads(_dump(_document_register_rows(session, tenant_id, documents)))
    # A document is never deleted, so the documents read here are exactly the stored
    # rows this refresh speaks for.
    return NarrowedRows(rows, frozenset(rows))


def _items_touched(
    session: Session, tenant_id: str, changes: ChangeSet
) -> frozenset[str] | str:
    """The articles the changed records belong to, or why they cannot be found.

    Every frequent subject that reaches a stock projection carries an article: a
    movement, a reservation, a promise, an observation about one of those. A location,
    a master-data lifecycle change and the tenant do not, and are declined — they are
    rare enough that evaluating the company for them costs little.

    The trap here is the same shape as the ledger reversal, in a different service.
    `movement.corrected` names the **original** movement, while the compensating and
    replacement movements it creates are appended with `emit_recorded_event=False` —
    no event names them, and a replacement may carry a *different* article than the
    one that was corrected. Narrowing on the named movement alone leaves that article
    stale. The stored correction is followed instead.
    """
    from reality.db.core import Fact, Lot, Movement, MovementCorrection

    known = {"item", "movement", "reservation", "commitment", "fact"}
    unknown = sorted(set(changes.subjects or {}) - known)
    if unknown:
        return f"stock cannot narrow by {unknown[0]}"
    items = set(changes.ids("item"))
    movements = set(changes.ids("movement"))
    commitments = set(changes.ids("commitment"))
    lots: set[str] = set()
    if facts := changes.ids("fact"):
        for subject_type, subject_id in session.execute(
            select(Fact.subject_type, Fact.subject_id).where(
                Fact.tenant_id == tenant_id, Fact.id.in_(facts)
            )
        ).all():
            if subject_type == "movement":
                movements.add(subject_id)
            elif subject_type == "commitment":
                commitments.add(subject_id)
            elif subject_type == "lot":
                lots.add(subject_id)
            else:
                return f"stock cannot narrow by an observation about a {subject_type}"
    if movements:
        for original, compensating, replacement in session.execute(
            select(
                MovementCorrection.original_movement_id,
                MovementCorrection.compensating_movement_id,
                MovementCorrection.replacement_movement_id,
            ).where(
                MovementCorrection.tenant_id == tenant_id,
                MovementCorrection.original_movement_id.in_(movements),
            )
        ).all():
            movements.update(
                value for value in (original, compensating, replacement) if value
            )
        items.update(
            session.scalars(
                select(Movement.item_id).where(
                    Movement.tenant_id == tenant_id, Movement.id.in_(movements)
                )
            )
        )
    if reservations := changes.ids("reservation"):
        items.update(
            session.scalars(
                select(Reservation.item_id).where(
                    Reservation.tenant_id == tenant_id,
                    Reservation.id.in_(reservations),
                )
            )
        )
    if commitments:
        items.update(
            session.scalars(
                select(Commitment.item_id).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.id.in_(commitments),
                    Commitment.item_id.is_not(None),
                )
            )
        )
    if lots:
        items.update(
            session.scalars(
                select(Lot.item_id).where(Lot.tenant_id == tenant_id, Lot.id.in_(lots))
            )
        )
    return frozenset(items)


def _narrowed_inventory(
    session: Session, tenant_id: str, changes: ChangeSet
) -> NarrowedRows | str:
    """Stock, for the articles the changed records belong to (FR-002)."""
    items = _items_touched(session, tenant_id, changes)
    if isinstance(items, str):
        return items
    if not items:
        return "no stock subject resolved to an article"
    if len(items) > MAX_NARROWED_ROWS:
        return f"{len(items)} articles is not worth visiting one at a time"
    rows = json.loads(_dump(_inventory_rows(session, tenant_id, items)))
    # An Item is never deleted, so the articles read here are exactly the stored rows
    # this refresh speaks for.
    return NarrowedRows(rows, frozenset(rows))


#: Builders that can derive by change. A projection absent from this map evaluates the
#: company, which is always correct; one present may still decline for a change set it
#: cannot resolve, by returning the reason instead of rows (FR-002).
NARROWED_BUILDERS = {
    JOURNAL: _narrowed_journal,
    DOCUMENT_REGISTER: _narrowed_document_register,
    INVENTORY: _narrowed_inventory,
}


def projection_state_expressions(tenant_id: str, name: str) -> dict[str, Any]:
    """Scalar expressions can accompany data in the very same PostgreSQL snapshot."""
    from reality.db.scheduled_jobs import ScheduledJobRun

    def checkpoint(column):
        return (
            select(column)
            .where(
                ProjectionCheckpoint.tenant_id == tenant_id,
                ProjectionCheckpoint.projection_name == name,
            )
            .scalar_subquery()
        )

    failed = (
        select(
            func.max(
                func.coalesce(ScheduledJobRun.finished_at, ScheduledJobRun.created_at)
            )
        )
        .where(
            ScheduledJobRun.tenant_id == tenant_id,
            ScheduledJobRun.job_type == "projections.refresh",
            ScheduledJobRun.status.in_(("failed", "unresolved")),
            ScheduledJobRun.configuration["arguments"]["names"].contains([name]),
        )
        .scalar_subquery()
    )
    return {
        "processed_event_sequence": checkpoint(
            ProjectionCheckpoint.last_event_sequence
        ),
        "completed_at": checkpoint(ProjectionCheckpoint.updated_at),
        "projection_version": checkpoint(ProjectionCheckpoint.projection_version),
        "target_event_sequence": relevant_event_target(tenant_id, name),
        "failed_at": failed,
    }


def projection_metadata(name: str, values: dict[str, Any]) -> dict[str, Any]:
    completed = values["completed_at"]
    failed = values.get("failed_at")
    pending = (
        values["projection_version"] != PROJECTION_VERSION
        or (values["processed_event_sequence"] or 0) < values["target_event_sequence"]
        or (
            name in TIME_SENSITIVE_PROJECTIONS
            and completed is not None
            and (now() - completed).total_seconds() >= 60
        )
    )
    state = (
        "failed"
        if failed and (not completed or failed >= completed)
        else "uninitialized"
        if not completed
        else "pending"
        if pending
        else "ready"
    )
    return {
        "projection": name,
        "calculation_mode": "stored",
        "state": state,
        "processed_event_sequence": values["processed_event_sequence"],
        "target_event_sequence": values["target_event_sequence"],
        "completed_at": completed.isoformat() if completed else None,
        "projection_version": values["projection_version"],
        "upstream_freshness": "unknown",
        "consistency": "completed_snapshot",
    }


@_read_without_flush
def projection_snapshot(
    session: Session, tenant_id: str, name: str, *, limit: int = 100
) -> dict[str, Any]:
    """Read rows and progress together; missing caches are not business emptiness."""
    from reality.services.core import NotFound

    if name not in MATERIALIZED_PROJECTIONS or not 1 <= limit <= 100:
        raise ValueError("Unknown stored projection or invalid limit.")
    rows = (
        select(ProjectionRow.payload)
        .where(
            ProjectionRow.tenant_id == tenant_id, ProjectionRow.projection_name == name
        )
        .order_by(ProjectionRow.record_key)
        .limit(limit)
        .subquery()
    )
    items = select(func.json_agg(cast(rows.c.payload, JSONB))).scalar_subquery()
    values = (
        session.execute(
            select(
                items.label("items"),
                *(
                    value.label(key)
                    for key, value in projection_state_expressions(
                        tenant_id, name
                    ).items()
                ),
            ).where(Tenant.id == tenant_id)
        )
        .mappings()
        .first()
    )
    if values is None:
        raise NotFound("Tenant not found.")
    return {
        "items": values["items"] or [],
        "metadata": projection_metadata(name, values),
    }


def rebuild_projections(
    session: Session,
    tenant_id: str,
    names: list[str] | tuple[str, ...],
    *,
    force: bool = False,
) -> int:
    """Caller-owned publication transaction; no business action and no commit.

    Workers use REPEATABLE READ. Explicit maintenance callers at READ COMMITTED
    take the existing tenant writer lock to obtain an equivalent stable state.
    """
    from reality.services.core import get_tenant

    get_tenant(session, tenant_id)
    selected = set(names)
    if not selected or not selected <= set(MATERIALIZED_PROJECTIONS):
        raise ValueError("Unknown stored projection.")
    if session.connection().get_isolation_level() != "REPEATABLE READ":
        session.execute(
            select(Tenant.id).where(Tenant.id == tenant_id).with_for_update()
        )
    session.execute(
        select(
            func.pg_advisory_xact_lock(
                func.hashtextextended("projection:" + tenant_id, 0)
            )
        )
    )
    targets = {
        name: session.scalar(select(relevant_event_target(tenant_id, name)))
        for name in selected
    }
    # Where the company as a whole has got to, so each refreshed projection can record
    # that it has looked at least this far (spec 181 FR-004).
    observed = (
        session.scalar(
            select(TenantEventProgress.last_event_sequence).where(
                TenantEventProgress.tenant_id == tenant_id
            )
        )
        or 0
    )
    checkpoints = {
        c.projection_name: c
        for c in session.scalars(
            select(ProjectionCheckpoint)
            .where(
                ProjectionCheckpoint.tenant_id == tenant_id,
                ProjectionCheckpoint.projection_name.in_(selected),
            )
            .execution_options(populate_existing=True)
        )
    }
    changed = {
        name
        for name in selected
        if force
        or name not in checkpoints
        or checkpoints[name].projection_version != PROJECTION_VERSION
        or checkpoints[name].last_event_sequence < targets[name]
        or (
            name in TIME_SENSITIVE_PROJECTIONS
            and (now() - checkpoints[name].updated_at).total_seconds() >= 60
        )
    }
    count = 0
    # Financial builders remain independent even when tests forbid operational reads.
    for name in changed:
        since = checkpoints[name].last_event_sequence if name in checkpoints else 0
        narrowing = (
            ChangeSet(None, "full rebuild requested")
            if force or name not in checkpoints
            # A new row shape applies to rows no event touched, so a version change
            # is evaluated in full however little changed (FR-005).
            else ChangeSet(None, "projection version changed")
            if checkpoints[name].projection_version != PROJECTION_VERSION
            else change_set(session, tenant_id, name, since, targets[name])
        )
        narrowed = None
        if narrowing.narrowed and name in NARROWED_BUILDERS:
            with session.no_autoflush:
                outcome = NARROWED_BUILDERS[name](session, tenant_id, narrowing)
            if isinstance(outcome, NarrowedRows):
                narrowed = outcome
            else:
                narrowing = ChangeSet(None, outcome)
        elif narrowing.narrowed:
            narrowing = ChangeSet(None, f"{name} evaluates the company")
        report = NARROWING.get()
        if report is not None:
            report.setdefault(name, narrowing.reason)
        if narrowed is None:
            rows, covers = derive_projection_rows(session, tenant_id, name), None
        else:
            rows, covers = narrowed.rows, narrowed.covers
        _replace_rows(
            session,
            tenant_id,
            name,
            rows,
            targets[name],
            covers=covers,
            observed=observed,
        )
        count += len(rows)
    session.flush()
    return count


def refresh_operational_projections(
    session: Session, tenant_id: str, *, force: bool = False
) -> int:
    """Explicit maintenance boundary; never called by a stored-data read."""
    rebuild_projections(session, tenant_id, MATERIALIZED_PROJECTIONS, force=force)
    sequence = _latest_sequence(session, tenant_id)
    session.commit()
    return sequence


def refresh_projection(session: Session, tenant_id: str, projection_name: str) -> int:
    """Explicit maintenance of one projection; request reads do not call this."""
    rebuild_projections(session, tenant_id, [projection_name])
    sequence = _latest_sequence(session, tenant_id)
    session.commit()
    return sequence


@_read_without_flush
def projection_rows(
    session: Session, tenant_id: str, projection_name: str, *, refresh: bool = False
) -> list[dict[str, Any]]:
    from reality.services.core import get_tenant

    get_tenant(session, tenant_id)
    if projection_name not in OPERATIONAL_PROJECTIONS:
        raise ValueError("Unknown operational projection.")
    if refresh:
        raise ValueError("Use the explicit maintenance refresh service.")
    if projection_name == PRICE_RESOLUTION:
        return []
    return [
        json.loads(row.payload)
        for row in session.scalars(
            select(ProjectionRow)
            .where(
                ProjectionRow.tenant_id == tenant_id,
                ProjectionRow.projection_name == projection_name,
            )
            .order_by(ProjectionRow.record_key)
        )
    ]


@_read_without_flush
def materialized_resolve_price(
    session: Session,
    tenant_id: str,
    party_id: str,
    item_id: str,
    quantity: Decimal | float | str,
    direction: str,
    currency: str,
    unit: str,
    *,
    at: datetime | str | None = None,
) -> dict[str, Any] | None:
    """Compatibility entrypoint for the live, parameterized canonical price read."""
    from reality.services.core import resolve_price

    result = resolve_price(
        session,
        tenant_id,
        party_id,
        item_id,
        quantity,
        direction,
        currency,
        unit,
        at=at,
    )
    if result is None:
        return None
    return json.loads(
        _dump(
            {
                "unit_price": result.unit_price,
                "currency": result.currency,
                "unit": result.unit,
                "price_list_id": result.price_list_id,
                "price_list_entry_id": result.price_list_entry_id,
                "source": result.source,
            }
        )
    )


def explain_order_projection(
    session: Session, tenant_id: str, order_reference: str
) -> dict[str, Any]:
    """Explain retained evidence, independent of membership in the current work queue."""
    with session.no_autoflush:
        return _explain_retained_order(session, tenant_id, order_reference)


def _explain_retained_order(
    session: Session, tenant_id: str, order_reference: str
) -> dict[str, Any]:
    from reality.services.core import (
        InvalidOperation,
        NotFound,
        document_detail,
        get_tenant,
    )
    from reality.services.delivery_reads import delivery_case
    from reality.services.read_contracts import read_metadata

    get_tenant(session, tenant_id)
    document_query = select(Document).where(
        Document.tenant_id == tenant_id,
        Document.type.in_(["sales_order", "purchase_order"]),
    )
    document = session.scalar(document_query.where(Document.id == order_reference))
    selected = None
    if document is None:
        selected = session.scalar(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.id == order_reference,
                Commitment.type.in_(["customer_delivery", "supplier_delivery"]),
            )
        )
        if selected:
            document_id = selected.document_id
            if not document_id and selected.document_line_id:
                document_id = session.scalar(
                    select(DocumentLine.document_id).where(
                        DocumentLine.tenant_id == tenant_id,
                        DocumentLine.id == selected.document_line_id,
                    )
                )
            if document_id:
                document = session.scalar(
                    document_query.where(Document.id == document_id)
                )
        else:
            sources = select(SourceRecord.id).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.external_id == order_reference,
            )
            matches = list(
                session.scalars(
                    document_query.where(
                        or_(
                            Document.number == order_reference,
                            Document.source_record_id.in_(sources),
                        )
                    ).limit(2)
                )
            )
            if len(matches) > 1:
                raise InvalidOperation(
                    "Order reference is ambiguous; use an opaque order ID."
                )
            document = matches[0] if matches else None
    if document is None and selected is None:
        raise NotFound("Order not found.")
    detail = document_detail(session, tenant_id, document.id) if document else None
    evidence_lines = sorted(detail["lines"], key=lambda row: row.id) if detail else []
    commitments = (
        list(
            session.scalars(
                select(Commitment)
                .where(
                    Commitment.tenant_id == tenant_id,
                    or_(
                        Commitment.document_id == document.id,
                        Commitment.document_line_id.in_(
                            [row.id for row in evidence_lines]
                        ),
                    ),
                )
                .order_by(Commitment.id)
            )
        )
        if document
        else [selected]
    )
    delivery_commitments = [
        c for c in commitments if c.type in {"customer_delivery", "supplier_delivery"}
    ]
    lines = []
    for commitment in delivery_commitments:
        case = delivery_case(session, tenant_id, commitment.id)
        row = case["case"]
        open_value = Decimal(row["open"]) if row["status"] == "open" else Decimal(0)
        shortage = max(Decimal(0), open_value - Decimal(row["reserved"]))
        reasons = sorted(
            {
                (
                    "party_delivery_hold"
                    if h["scope"] == "party"
                    else h["scope"] + "_hold"
                )
                for h in row["blockers"]
            }
        )
        if shortage:
            reasons.append("insufficient_reservation")
        lines.append(
            {
                "commitment_id": commitment.id,
                "document_line_id": commitment.document_line_id,
                "item_id": row["item_id"],
                "item": row["item"],
                "unit": row["unit"] or None,
                "unit_status": "known" if row["unit"] else "unknown",
                "quantity_basis": "item_unit",
                "status": row["status"],
                "quantity": row["promised"],
                "original_quantity": str(commitment.quantity),
                "open_quantity": str(open_value),
                "priority": commitment.priority,
                "fulfilled_quantity": row["fulfilled"],
                "reserved_quantity": row["reserved"],
                "shortage_quantity": str(shortage),
                "due_at": row["due_at"],
                "original_due_at": commitment.due_at,
                "location_id": row["location_id"],
                "blocking_reasons": reasons,
                "inventory": case["inventory"],
            }
        )
    ids = [c.id for c in commitments]
    reservations = list(
        session.scalars(
            select(Reservation)
            .where(
                Reservation.tenant_id == tenant_id, Reservation.commitment_id.in_(ids)
            )
            .order_by(Reservation.id)
        )
    )
    movements = list(
        session.scalars(
            select(Movement)
            .where(Movement.tenant_id == tenant_id, Movement.commitment_id.in_(ids))
            .order_by(Movement.id)
        )
    )
    item_ids = (
        {c.item_id for c in commitments if c.item_id}
        | {m.item_id for m in movements}
        | {line.item_id for line in evidence_lines if line.item_id}
    )
    items = {
        item.id: item
        for item in session.scalars(
            select(Item).where(Item.tenant_id == tenant_id, Item.id.in_(item_ids))
        )
    }
    for line in lines:
        item = items.get(line["item_id"])
        line["sku"] = item.sku if item else ""
    commitment_items = {c.id: c.item_id for c in commitments}
    source = detail["source"] if detail else None
    active = [
        line
        for line in lines
        if line["status"] == "open" and Decimal(line["open_quantity"]) > 0
    ]
    ready = bool(active) and not any(line["blocking_reasons"] for line in active)
    result = {
        "fulfillment": {
            "order_key": document.id if document else selected.id,
            "document_id": document.id if document else None,
            "document_number": document.number if document else None,
            "source_system": source.source_system if source else None,
            "external_order_id": source.external_id if source else None,
            "party_id": document.party_id if document else selected.to_party_id,
            "party": detail["party"].name if detail and detail["party"] else None,
            "due_at": min(
                (line["due_at"] for line in lines if line["due_at"]), default=None
            ),
            "priority": max(
                (line["priority"] for line in lines),
                key=lambda value: PRIORITY_RANK.get(value, 1),
                default="normal",
            ),
            "readiness": "ready" if ready else "blocked" if active else "closed",
            "ship_ready": ready,
            "blocking_reasons": sorted(
                {r for line in active for r in line["blocking_reasons"]}
            ),
            "lines": lines,
        },
        "document": {
            "id": document.id,
            "type": document.type,
            "number": document.number,
            "currency": document.currency,
            "gross_amount": str(document.gross_amount),
            "source_record_id": document.source_record_id,
        }
        if document
        else None,
        "document_lines": [
            {
                "id": line.id,
                "item_id": line.item_id,
                "quantity": str(line.quantity),
                "unit": line.unit or None,
                "item_unit": items[line.item_id].unit or None
                if line.item_id in items
                else None,
                "unit_mismatch": quantity_unit(items.get(line.item_id), line)[
                    "unit_mismatch"
                ],
                "unit_price": str(line.unit_price),
                "gross_amount": str(line.gross_amount),
                "billed_document_line_id": line.billed_document_line_id,
            }
            for line in evidence_lines
        ],
        "commitment_ids": ids,
        "reservations": [
            {
                "id": row.id,
                "commitment_id": row.commitment_id,
                "quantity": str(row.quantity),
                "status": row.status,
                **quantity_unit(items.get(commitment_items.get(row.commitment_id))),
                "handling_unit_id": row.handling_unit_id,
                "lot_id": row.lot_id,
                "serial_unit_id": row.serial_unit_id,
            }
            for row in reservations
        ],
        "movements": [
            {
                "id": row.id,
                "commitment_id": row.commitment_id,
                "type": row.type,
                "quantity": str(row.quantity),
                **quantity_unit(items.get(row.item_id)),
                "from_location_id": row.from_location_id,
                "to_location_id": row.to_location_id,
                "occurred_at": row.occurred_at,
            }
            for row in movements
        ],
        "source": {
            "source_record_id": source.id,
            "source_system": source.source_system,
            "source_type": source.source_type,
            "external_id": source.external_id,
            "version": source.version,
            "raw_payload": json.loads(source.payload),
        }
        if source
        else None,
        "metadata": read_metadata(
            session, tenant_id, {"order_reference": order_reference}
        ),
    }
    return json.loads(_dump(result))
