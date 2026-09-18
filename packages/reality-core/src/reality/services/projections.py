from __future__ import annotations

import json
from collections import defaultdict
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
) -> None:
    existing = {
        row.record_key: row
        for row in session.scalars(
            select(ProjectionRow).where(
                ProjectionRow.tenant_id == tenant_id,
                ProjectionRow.projection_name == projection_name,
            )
        )
    }
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
    checkpoint.status = "ready"
    checkpoint.error = ""
    checkpoint.updated_at = stamp


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
        document_rows,
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
    terms = (
        commitment_terms(session, tenant_id)
        if selected
        & {
            FULFILLMENT_QUEUE,
            FULFILLMENT_BLOCKERS,
            ITEM_SUPPLY_DEMAND,
            COMMITMENT_REGISTER,
        }
        else {}
    )
    if selected & {FULFILLMENT_QUEUE, FULFILLMENT_BLOCKERS, ITEM_SUPPLY_DEMAND}:
        parties = {
            row.id: row
            for row in session.scalars(
                select(Party).where(Party.tenant_id == tenant_id)
            )
        }
        documents = {
            row.id: row
            for row in session.scalars(
                select(Document).where(Document.tenant_id == tenant_id)
            )
        }
        sources = {
            row.id: row
            for row in session.scalars(
                select(SourceRecord).where(SourceRecord.tenant_id == tenant_id)
            )
        }
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
        customer_commitments = list(
            session.scalars(
                select(Commitment).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.type == "customer_delivery",
                    Commitment.status == "open",
                )
            )
        )
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
        inventory_projection = {
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
            for row in inventory_rows(session, tenant_id)
        }
        result[INVENTORY] = inventory_projection
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
        document_projection = {}
        for document, source, lines_, commitments_ in document_rows(session, tenant_id):
            document_projection[document.id] = {
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
        result[DOCUMENT_REGISTER] = document_projection
    if JOURNAL in selected:
        journal_projection = {
            entry.id: {
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
            for entry in journal_rows(session, tenant_id)
        }
        result[JOURNAL] = journal_projection
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
TIME_SENSITIVE_PROJECTIONS = (EXCEPTIONS, COMMITMENT_REGISTER, TENANT_USAGE)


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
        rows = derive_projection_rows(session, tenant_id, name)
        _replace_rows(session, tenant_id, name, rows, targets[name])
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
