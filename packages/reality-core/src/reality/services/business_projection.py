"""Incremental, resumable Business read models on the shared projection worker."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import cast, delete, func, literal_column, or_, select, tuple_
from sqlalchemy.dialects.postgresql import JSONB, aggregate_order_by
from sqlalchemy.orm import Session

from reality.db.business_projection import (
    ORDER_FLAGS,
    BusinessMailRow,
    BusinessOrderRow,
)
from reality.db.core import (
    BusinessEvent,
    Commitment,
    Document,
    DocumentLine,
    Movement,
    ProjectionCheckpoint,
    ProjectionRow,
    Reservation,
    SourceRecord,
    StockBlock,
    TenantEventProgress,
    now,
    uid,
)
from reality.services import business_projection_derivation as derive
from reality.services import projections

NAME = "business_performance"
VERSION = 1
CHUNK = 200
EVENT_BUDGET = 100
ORDER_COUNTERS = (
    "unshipped_orders",
    "partial_orders",
    "complete_dispatch_orders",
    "cancelled_orders",
    "eligible_orders",
    "ready_orders",
    "blocked_orders",
    "reservation_blocked_orders",
    "held_orders",
    "overdue_orders",
    "at_risk_orders",
    "orders_received_last_hour",
    "orders_completed_last_hour",
    "invalid_timing_orders",
    "unknown_receipt_orders",
    "order_count",
    "first_dispatch_sample_orders",
    "complete_dispatch_sample_orders",
)
DECIMAL_KEYS = ("open_units", "first_sum", "complete_sum")
MIN_TIME = datetime.min.replace(tzinfo=UTC)


def _totals() -> dict[str, Any]:
    return {
        **dict.fromkeys(ORDER_COUNTERS, 0),
        **dict.fromkeys(DECIMAL_KEYS, "0"),
        "incoming": 0,
        "outgoing": 0,
        "waiting": 0,
        "unread": 0,
    }


def _delta(totals: dict, previous: dict, current: dict) -> None:
    for key, value in totals.items():
        if key in DECIMAL_KEYS:
            totals[key] = str(
                Decimal(value)
                - Decimal(str(previous.get(key, 0)))
                + Decimal(str(current.get(key, 0)))
            )
        else:
            totals[key] = value + current.get(key, 0) - previous.get(key, 0)


def _put_orders(
    session: Session,
    tenant: str,
    generation: str,
    ids: list[str],
    totals: dict,
    stamp: datetime,
) -> int:
    existing = {
        r.document_id: r
        for r in session.scalars(
            select(BusinessOrderRow).where(
                BusinessOrderRow.tenant_id == tenant,
                BusinessOrderRow.generation == generation,
                BusinessOrderRow.document_id.in_(ids),
            )
        )
    }
    values = derive.order_rows(session, tenant, ids, stamp)
    for value in values:
        key = value["document_id"]
        contribution = value.pop("_contribution")
        transition = value.pop("_next_transition_at")
        row = existing.pop(key, None)
        _delta(totals, row.contribution if row else {}, contribution)
        if row is None:
            row = BusinessOrderRow(
                tenant_id=tenant, generation=generation, document_id=key
            )
            session.add(row)
        row.received_sort = (
            datetime.fromisoformat(value["received_at"])
            if value["received_at"]
            else MIN_TIME
        )
        row.next_transition_at = transition
        row.flags = value["flags"]
        row.payload = json.loads(projections._dump(value))
        row.contribution = contribution
    for row in existing.values():
        _delta(totals, row.contribution, {})
        session.delete(row)
    return len(values)


def _mail_contribution(row: BusinessMailRow) -> dict:
    return {
        "incoming": int(row.direction == "incoming"),
        "outgoing": int(row.direction == "outgoing"),
        "waiting": int(row.waiting),
        "unread": int(row.unread),
    }


def _put_mail(
    session: Session, tenant: str, generation: str, ids: list[str], totals: dict
) -> int:
    existing = {
        r.source_record_id: r
        for r in session.scalars(
            select(BusinessMailRow).where(
                BusinessMailRow.tenant_id == tenant,
                BusinessMailRow.generation == generation,
                BusinessMailRow.source_record_id.in_(ids),
            )
        )
    }
    values = derive.mail_rows(session, tenant, ids)
    for value in values:
        key = value["source_record_id"]
        unread, waiting = value.pop("_unread"), value.pop("_waiting")
        direction = (
            "incoming"
            if value["direction"] in ("incoming", "inbound")
            else "outgoing"
            if value["direction"] in ("outgoing", "outbound")
            else "unclassified"
        )
        row = existing.pop(key, None)
        _delta(
            totals,
            _mail_contribution(row) if row else {},
            {
                "incoming": int(direction == "incoming"),
                "outgoing": int(direction == "outgoing"),
                "waiting": int(waiting),
                "unread": int(unread),
            },
        )
        if row is None:
            row = BusinessMailRow(
                tenant_id=tenant, generation=generation, source_record_id=key
            )
            session.add(row)
        row.direction, row.waiting, row.unread = direction, waiting, unread
        row.recorded_at = datetime.fromisoformat(value["recorded_at"])
        row.payload = value
    for row in existing.values():
        _delta(totals, _mail_contribution(row), {})
        session.delete(row)
    return len(values)


def _mail_predicate():
    direction = cast(SourceRecord.payload, JSONB)["direction"].astext
    valid = direction.in_(["inbound", "outbound", "incoming", "outgoing"])
    return or_(
        (SourceRecord.source_type == "email_message") & valid,
        SourceRecord.source_system.startswith("company_simulator:", autoescape=True)
        & or_(
            SourceRecord.source_type == "incoming",
            (SourceRecord.source_type == "outgoing") & valid,
        ),
    )


def _mail_affected(session: Session, tenant: str, source_id: str):
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant, SourceRecord.id == source_id
        )
    )
    if not source:
        return SourceRecord.id == source_id
    raw = json.loads(source.payload)
    message_id = raw.get("message_id")
    reply_to = raw.get("in_reply_to")
    reach = [SourceRecord.id == source_id]
    if source.source_type == "ack":
        reach.append(SourceRecord.id == source.external_id)
    if message_id is not None:
        reach.append(derive.message_identity(SourceRecord, "in_reply_to", message_id))
    if reply_to is not None or source.source_type == "outgoing":
        reach.append(derive.message_identity(SourceRecord, "message_id", reply_to))
    return (SourceRecord.source_system == source.source_system) & or_(*reach)


def _affected_order_query(session: Session, tenant: str, event: BusinessEvent):
    """Resolve high fan-out in SQL; common recorded links use the shared resolver."""
    kind, key = event.subject_type, event.subject_id
    dependencies = projections.projection_dependencies().get(event.event_type)
    relevant = {
        projections.FULFILLMENT_QUEUE,
        projections.COMMITMENT_REGISTER,
        projections.DOCUMENT_REGISTER,
        projections.INVENTORY,
    }
    query = select(Document.id).where(
        Document.tenant_id == tenant, Document.type == "sales_order"
    )
    if (
        dependencies is not None
        and not dependencies & relevant
        and kind != "source_record"
    ):
        return query.where(False)
    if kind in {"item", "party", "location", "stock_block"}:
        if kind == "stock_block":
            key = session.scalar(
                select(StockBlock.item_id).where(
                    StockBlock.tenant_id == tenant, StockBlock.id == key
                )
            )
            kind = "item"
        condition = (
            Commitment.item_id == key
            if kind == "item"
            else Commitment.to_party_id == key
            if kind == "party"
            else Commitment.location_id == key
        )
        reach = Document.id.in_(
            select(Commitment.document_id).where(
                Commitment.tenant_id == tenant,
                Commitment.type == "customer_delivery",
                Commitment.status == "open",
                condition,
            )
        )
        if kind == "party":
            reach = or_(reach, Document.party_id == key)
        return query.where(reach)
    if kind == "source_record":
        return query.where(Document.source_record_id == key)
    if kind == "document_line":
        return query.where(
            Document.id.in_(
                select(DocumentLine.document_id).where(
                    DocumentLine.tenant_id == tenant, DocumentLine.id == key
                )
            )
        )
    if kind == "payment_term":
        return query.where(Document.payment_term_id == key)
    if kind == "movement":
        # Stock changes affect other open orders sharing the item, not just the
        # shipment's own order; follow corrections through the canonical resolver.
        from reality.db.core import MovementCorrection

        movement_ids = {key}
        for original, compensating, replacement in session.execute(
            select(
                MovementCorrection.original_movement_id,
                MovementCorrection.compensating_movement_id,
                MovementCorrection.replacement_movement_id,
            ).where(
                MovementCorrection.tenant_id == tenant,
                MovementCorrection.original_movement_id == key,
            )
        ):
            movement_ids.update(v for v in (original, compensating, replacement) if v)
        movement_scope = select(Movement).where(
            Movement.tenant_id == tenant, Movement.id.in_(movement_ids)
        )
        movements = list(session.scalars(movement_scope))
        commitments = {m.commitment_id for m in movements if m.commitment_id}
        items = {m.item_id for m in movements if m.item_id}
        return query.where(
            Document.id.in_(
                select(Commitment.document_id).where(
                    Commitment.tenant_id == tenant,
                    or_(
                        Commitment.id.in_(commitments),
                        (Commitment.status == "open") & Commitment.item_id.in_(items),
                    ),
                )
            )
        )
    if kind == "reservation":
        reservation = session.scalar(
            select(Reservation).where(
                Reservation.tenant_id == tenant, Reservation.id == key
            )
        )
        if reservation:
            return query.where(
                Document.id.in_(
                    select(Commitment.document_id).where(
                        Commitment.tenant_id == tenant,
                        or_(
                            Commitment.id == reservation.commitment_id,
                            (Commitment.status == "open")
                            & (Commitment.item_id == reservation.item_id),
                        ),
                    )
                )
            )
    touched = projections._orders_touched(
        session, tenant, projections.ChangeSet({kind: frozenset([key])}), NAME
    )
    if isinstance(touched, str):
        # A broad/unknown scope is paged, never hidden behind a full-history batch.
        return query
    return query.where(Document.id.in_(touched))


def _checkpoint(session: Session, tenant: str) -> ProjectionCheckpoint:
    checkpoint = session.scalar(
        select(ProjectionCheckpoint).where(
            ProjectionCheckpoint.tenant_id == tenant,
            ProjectionCheckpoint.projection_name == NAME,
        )
    )
    if checkpoint is None:
        checkpoint = ProjectionCheckpoint(
            id=uid("prc"),
            tenant_id=tenant,
            projection_name=NAME,
            projection_version=projections.PROJECTION_VERSION,
            last_event_sequence=0,
            observed_event_sequence=0,
        )
        session.add(checkpoint)
    return checkpoint


def _cleanup(session: Session, tenant: str, active: str, building: str | None) -> bool:
    remaining = False
    for model, key in (
        (BusinessOrderRow, BusinessOrderRow.document_id),
        (BusinessMailRow, BusinessMailRow.source_record_id),
    ):
        old = (
            select(model.generation, key)
            .where(
                model.tenant_id == tenant,
                model.generation.not_in([v for v in (active, building) if v]),
            )
            .limit(CHUNK)
            .subquery()
        )
        session.execute(
            delete(model).where(
                model.tenant_id == tenant,
                tuple_(model.generation, key).in_(select(old)),
            )
        )

    for model in (BusinessOrderRow, BusinessMailRow):
        remaining = remaining or bool(
            session.scalar(
                select(model.generation)
                .where(
                    model.tenant_id == tenant,
                    model.generation.not_in([v for v in (active, building) if v]),
                )
                .limit(1)
            )
        )
    return remaining


def refresh(session: Session, tenant: str, *, force: bool = False) -> int:
    """One bounded publication unit; called within shared builder lock/fenced run."""
    from reality.services.core import get_tenant

    get_tenant(session, tenant)
    # Shared builder supplies this lock too; repeated acquisition is harmless.
    session.execute(
        select(
            func.pg_advisory_xact_lock(func.hashtextextended("projection:" + tenant, 0))
        )
    )
    stamp = now()
    target = (
        session.scalar(
            select(TenantEventProgress.last_event_sequence).where(
                TenantEventProgress.tenant_id == tenant
            )
        )
        or 0
    )
    stored = session.scalar(
        select(ProjectionRow)
        .where(
            ProjectionRow.tenant_id == tenant,
            ProjectionRow.projection_name == NAME,
            ProjectionRow.record_key == "summary",
        )
        .execution_options(populate_existing=True)
    )
    state = (
        json.loads(stored.payload) if stored else {"active": None, "totals": _totals()}
    )
    checkpoint = _checkpoint(session, tenant)
    if (
        force
        or state.get("version") != VERSION
        or checkpoint.projection_version != projections.PROJECTION_VERSION
        or not state.get("active")
    ) and not state.get("build"):
        state["build"] = {
            "generation": uid("bpg"),
            "phase": "orders",
            "after": "",
            "sequence": target,
            "totals": _totals(),
            "rows": 0,
        }
        state["version"] = VERSION
    changed = 0
    build = state.get("build")
    if build:
        generation = build["generation"]
        budget = CHUNK
        for _ in range(2):
            phase = build["phase"]
            if phase == "orders":
                ids = list(
                    session.scalars(
                        select(Document.id)
                        .where(
                            Document.tenant_id == tenant,
                            Document.type == "sales_order",
                            Document.id > build["after"],
                        )
                        .order_by(Document.id)
                        .limit(budget)
                    )
                )
                changed += _put_orders(
                    session, tenant, generation, ids, build["totals"], stamp
                )
            else:
                ids = list(
                    session.scalars(
                        select(SourceRecord.id)
                        .where(
                            SourceRecord.tenant_id == tenant,
                            _mail_predicate(),
                            SourceRecord.id > build["after"],
                        )
                        .order_by(SourceRecord.id)
                        .limit(budget)
                    )
                )
                changed += _put_mail(session, tenant, generation, ids, build["totals"])
            build["rows"] += len(ids)
            if ids:
                build["after"] = ids[-1]
            if len(ids) == budget:
                break
            budget -= len(ids)
            if phase == "orders":
                build["phase"], build["after"] = "mail", ""
            else:
                state["active"], state["totals"] = generation, build["totals"]
                checkpoint.last_event_sequence = build["sequence"]
                state["build"] = None
                state.pop("event", None)
                state["published_at"] = stamp.isoformat()
                break
    else:
        generation = state["active"]
        # Clock work has priority even during a busy event stream; bounded indexed
        # selection handles simultaneous deadlines over several durable runs.
        clock_ids = list(
            session.scalars(
                select(BusinessOrderRow.document_id)
                .where(
                    BusinessOrderRow.tenant_id == tenant,
                    BusinessOrderRow.generation == generation,
                    BusinessOrderRow.next_transition_at <= stamp,
                )
                .order_by(
                    BusinessOrderRow.next_transition_at, BusinessOrderRow.document_id
                )
                .limit(CHUNK)
            )
        )
        changed += _put_orders(
            session, tenant, generation, clock_ids, state["totals"], stamp
        )
        for _ in range(EVENT_BUDGET):
            event = session.scalar(
                select(BusinessEvent)
                .where(
                    BusinessEvent.tenant_id == tenant,
                    BusinessEvent.sequence > checkpoint.last_event_sequence,
                    BusinessEvent.sequence <= target,
                )
                .order_by(BusinessEvent.sequence)
                .limit(1)
            )
            if not event:
                break
            progress = state.get("event") or {
                "sequence": event.sequence,
                "orders_after": "",
                "mail_after": "",
                "orders_done": False,
            }
            if not progress["orders_done"]:
                ids = list(
                    session.scalars(
                        _affected_order_query(session, tenant, event)
                        .where(Document.id > progress["orders_after"])
                        .order_by(Document.id)
                        .limit(CHUNK)
                    )
                )
                changed += _put_orders(
                    session, tenant, generation, ids, state["totals"], stamp
                )
                if ids:
                    progress["orders_after"] = ids[-1]
                progress["orders_done"] = len(ids) < CHUNK
                if not progress["orders_done"]:
                    state["event"] = progress
                    break
            ids = []
            if event.subject_type == "source_record":
                ids = list(
                    session.scalars(
                        select(SourceRecord.id)
                        .where(
                            SourceRecord.tenant_id == tenant,
                            _mail_predicate(),
                            _mail_affected(session, tenant, event.subject_id),
                            SourceRecord.id > progress["mail_after"],
                        )
                        .order_by(SourceRecord.id)
                        .limit(CHUNK)
                    )
                )
                changed += _put_mail(session, tenant, generation, ids, state["totals"])
            if len(ids) == CHUNK:
                progress["mail_after"] = ids[-1]
                state["event"] = progress
                break
            checkpoint.last_event_sequence = event.sequence
            state["event"] = None
            if changed >= CHUNK:
                break
    session.flush()
    active = state.get("active")
    if active:
        clock_due = session.scalar(
            select(func.min(BusinessOrderRow.next_transition_at)).where(
                BusinessOrderRow.tenant_id == tenant,
                BusinessOrderRow.generation == active,
            )
        )
    else:
        clock_due = None
    # Also update ancillary observations and their clock-dependent goods flow.
    # They do not execute on API reads and intentionally retain legacy semantics.
    if active:
        state["aux"] = json.loads(
            projections._dump(derive.auxiliary(session, tenant, stamp))
        )
        state["aux_at"] = stamp.isoformat()
    goods_expiry = session.scalar(
        select(func.min(Movement.occurred_at)).where(
            Movement.tenant_id == tenant,
            Movement.type.in_(["receipt", "shipment"]),
            Movement.occurred_at >= stamp - timedelta(hours=1),
        )
    )
    auxiliary_due = (
        goods_expiry + timedelta(hours=1, microseconds=1)
        if goods_expiry
        else stamp + timedelta(days=1)
    )
    checkpoint.clock_due_at = (
        min(clock_due, auxiliary_due) if clock_due else auxiliary_due
    )
    if (
        state.get("build")
        or state.get("event")
        or checkpoint.last_event_sequence < target
    ):
        checkpoint.clock_due_at = stamp
    checkpoint.projection_version = projections.PROJECTION_VERSION
    checkpoint.observed_event_sequence = target
    checkpoint.status, checkpoint.error = "ready", ""
    checkpoint.updated_at = stamp
    state["completed_at"] = stamp.isoformat()
    state["target_sequence"] = target
    if stored is None:
        stored = ProjectionRow(
            id=uid("prj"), tenant_id=tenant, projection_name=NAME, record_key="summary"
        )
        session.add(stored)
    stored.payload = projections._dump(state)
    stored.projection_version = projections.PROJECTION_VERSION
    stored.source_event_sequence = checkpoint.last_event_sequence
    stored.updated_at = stamp
    garbage_pending = _cleanup(
        session,
        tenant,
        active or "",
        state["build"]["generation"] if state.get("build") else None,
    )
    if garbage_pending:
        checkpoint.clock_due_at = min(
            checkpoint.clock_due_at, stamp + timedelta(seconds=5)
        )
    session.flush()
    return changed


def _cursor(
    tenant: str, generation: str, cohort: str, stamp: datetime, key: str
) -> str:
    return base64.urlsafe_b64encode(
        json.dumps([tenant, generation, cohort, stamp.isoformat(), key]).encode()
    ).decode()


def _decode_cursor(value: str, tenant: str, generation: str | None, cohort: str):
    try:
        if len(value) > 2000:
            raise ValueError
        parts = json.loads(base64.urlsafe_b64decode(value))
        if (
            len(parts) != 5
            or parts[0] != tenant
            or parts[2] != cohort
            or (generation is not None and parts[1] != generation)
            or not isinstance(parts[1], str)
            or not isinstance(parts[4], str)
        ):
            raise ValueError
        stamp = datetime.fromisoformat(parts[3])
        if stamp.tzinfo is None:
            raise ValueError
        return stamp, parts[4]
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid or expired Business page cursor.") from exc


def _cohort(flag: str):
    # The finite allowlist makes this literal safe, and keeps partial indexes
    # usable with PostgreSQL generic prepared plans (a bound flag cannot do so).
    if flag not in ORDER_FLAGS:
        raise ValueError("Unknown Business cohort.")
    return BusinessOrderRow.flags.bool_op("@>")(
        literal_column(f"ARRAY['{flag}']::varchar[]")
    )


@projections._read_without_flush
def overview(
    session: Session,
    tenant_id: str,
    *,
    order_filter: str = "",
    mail_filter: str = "",
    order_cursor: str = "",
    mail_cursor: str = "",
    order_limit: int = 200,
    mail_limit: int = 50,
) -> dict[str, Any]:
    if (
        order_filter
        and order_filter not in ORDER_FLAGS
        or mail_filter not in ("", "incoming", "outgoing", "waiting")
    ):
        raise ValueError("Unknown Business cohort.")
    if not 1 <= order_limit <= 200 or not 1 <= mail_limit <= 50:
        raise ValueError("Invalid Business page size.")
    # Totals, both pages, oldest dates and freshness share one PostgreSQL statement
    # snapshot, including READ COMMITTED API sessions and concurrent publication.
    expressions = projections.projection_state_expressions(tenant_id, NAME)
    raw = (
        select(ProjectionRow.payload)
        .where(
            ProjectionRow.tenant_id == tenant_id,
            ProjectionRow.projection_name == NAME,
            ProjectionRow.record_key == "summary",
        )
        .scalar_subquery()
    )
    summary = select(raw.label("payload")).cte("business_summary")
    active = cast(summary.c.payload, JSONB)["active"].astext
    order_query = (
        select(
            BusinessOrderRow.payload.label("payload"),
            BusinessOrderRow.received_sort.label("stamp"),
            BusinessOrderRow.document_id.label("key"),
        )
        .where(
            BusinessOrderRow.tenant_id == tenant_id,
            BusinessOrderRow.generation == active,
        )
        .correlate(summary)
    )
    if order_filter:
        order_query = order_query.where(_cohort(order_filter))
    if order_cursor:
        stamp, key = _decode_cursor(
            order_cursor, tenant_id, None, "orders:" + order_filter
        )
        order_query = order_query.where(
            tuple_(BusinessOrderRow.received_sort, BusinessOrderRow.document_id)
            > tuple_(stamp, key)
        )
    order_page = (
        order_query.order_by(
            BusinessOrderRow.received_sort, BusinessOrderRow.document_id
        )
        .limit(order_limit + 1)
        .subquery()
    )
    order_values = (
        select(
            func.jsonb_agg(
                aggregate_order_by(
                    func.jsonb_build_object(
                        "payload",
                        order_page.c.payload,
                        "stamp",
                        order_page.c.stamp,
                        "key",
                        order_page.c.key,
                    ),
                    order_page.c.stamp,
                    order_page.c.key,
                )
            )
        )
        .select_from(order_page)
        .scalar_subquery()
    )
    mail_query = (
        select(
            BusinessMailRow.payload.label("payload"),
            BusinessMailRow.recorded_at.label("stamp"),
            BusinessMailRow.source_record_id.label("key"),
        )
        .where(
            BusinessMailRow.tenant_id == tenant_id, BusinessMailRow.generation == active
        )
        .correlate(summary)
    )
    mail_query = mail_query.where(
        BusinessMailRow.direction.in_(["incoming", "outgoing"])
    )
    if mail_filter == "waiting":
        mail_query = mail_query.where(BusinessMailRow.waiting)
    elif mail_filter:
        mail_query = mail_query.where(BusinessMailRow.direction == mail_filter)
    if mail_cursor:
        stamp, key = _decode_cursor(mail_cursor, tenant_id, None, "mail:" + mail_filter)
        mail_query = mail_query.where(
            or_(
                BusinessMailRow.recorded_at < stamp,
                (BusinessMailRow.recorded_at == stamp)
                & (BusinessMailRow.source_record_id > key),
            )
        )
    mail_page = (
        mail_query.order_by(
            BusinessMailRow.recorded_at.desc(), BusinessMailRow.source_record_id
        )
        .limit(mail_limit + 1)
        .subquery()
    )
    mail_values = (
        select(
            func.jsonb_agg(
                aggregate_order_by(
                    func.jsonb_build_object(
                        "payload",
                        mail_page.c.payload,
                        "stamp",
                        mail_page.c.stamp,
                        "key",
                        mail_page.c.key,
                    ),
                    mail_page.c.stamp.desc(),
                    mail_page.c.key,
                )
            )
        )
        .select_from(mail_page)
        .scalar_subquery()
    )
    oldest_queries = [
        select(BusinessOrderRow.received_sort)
        .where(
            BusinessOrderRow.tenant_id == tenant_id,
            BusinessOrderRow.generation == active,
            _cohort(flag),
            BusinessOrderRow.received_sort > MIN_TIME,
        )
        .order_by(BusinessOrderRow.received_sort, BusinessOrderRow.document_id)
        .limit(1)
        .correlate(summary)
        .scalar_subquery()
        .label("oldest_" + flag)
        for flag in ("unshipped", "partial")
    ]
    lag_at = (
        select(BusinessEvent.recorded_at)
        .where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.sequence
            > func.coalesce(expressions["processed_event_sequence"], 0),
        )
        .order_by(BusinessEvent.sequence)
        .limit(1)
        .scalar_subquery()
    )
    values = (
        session.execute(
            select(
                summary.c.payload.label("summary"),
                lag_at.label("oldest_pending_event_at"),
                *(v.label(k) for k, v in expressions.items()),
                order_values.label("order_page"),
                mail_values.label("mail_page"),
                *oldest_queries,
            ).select_from(summary)
        )
        .mappings()
        .one()
    )
    state = json.loads(values["summary"]) if values["summary"] else {}
    metadata = projections.projection_metadata(NAME, dict(values))
    generation = state.get("active")
    if state.get("build") and metadata["state"] != "failed":
        metadata["state"] = "rebuilding"
    if not generation and metadata["state"] == "ready":
        metadata["state"] = "uninitialized"
    clock = now()
    lag_stamps = [
        stamp
        for stamp in (values["oldest_pending_event_at"], values["clock_due_at"])
        if stamp and stamp <= clock
    ]
    metadata.update(
        {
            "lag_seconds": round(
                max(
                    ((clock - stamp).total_seconds() for stamp in lag_stamps), default=0
                ),
                3,
            ),
            "delayed": metadata["state"] != "ready",
            "clock_due_at": values["clock_due_at"].isoformat()
            if values["clock_due_at"]
            else None,
            "rebuild": {k: state["build"][k] for k in ("phase", "rows")}
            if state.get("build")
            else None,
            "available": bool(generation),
            "upstream_freshness": "unknown",
        }
    )
    totals = state.get("totals") or _totals()
    orders, messages = [], []
    next_order = next_mail = None
    oldest = None
    for value, cohort in (
        (order_cursor, "orders:" + order_filter),
        (mail_cursor, "mail:" + mail_filter),
    ):
        if value:
            if not generation:
                raise ValueError("Invalid or expired Business page cursor.")
            _decode_cursor(value, tenant_id, generation, cohort)
    observed = now()
    order_rows = values["order_page"] or []
    mail_rows = values["mail_page"] or []
    orders = [dict(r["payload"]) for r in order_rows[:order_limit]]
    messages = [r["payload"] for r in mail_rows[:mail_limit]]
    for row in orders:
        row["age_minutes"] = (
            round(
                (observed - datetime.fromisoformat(row["received_at"])).total_seconds()
                / 60,
                1,
            )
            if row["received_at"]
            else None
        )
    if len(order_rows) > order_limit:
        row = order_rows[order_limit - 1]
        next_order = _cursor(
            tenant_id,
            generation,
            "orders:" + order_filter,
            datetime.fromisoformat(row["stamp"]),
            row["key"],
        )
    if len(mail_rows) > mail_limit:
        row = mail_rows[mail_limit - 1]
        next_mail = _cursor(
            tenant_id,
            generation,
            "mail:" + mail_filter,
            datetime.fromisoformat(row["stamp"]),
            row["key"],
        )
    oldest_stamps = [
        values["oldest_" + flag]
        for flag in ("unshipped", "partial")
        if values["oldest_" + flag]
    ]
    oldest = (
        round((observed - min(oldest_stamps)).total_seconds() / 60, 1)
        if oldest_stamps
        else None
    )
    first_count, complete_count = (
        totals["first_dispatch_sample_orders"],
        totals["complete_dispatch_sample_orders"],
    )
    return {
        **{k: totals[k] for k in ORDER_COUNTERS},
        **state.get(
            "aux",
            {
                "inventory": [],
                "recent_documents": [],
                "replenishment": [],
                "goods_flow_last_hour": [],
                "open_replenishment_lines": 0,
                "pending_decisions": 0,
            },
        ),
        "processing": metadata,
        "orders": orders,
        "messages": messages,
        "orders_next_cursor": next_order,
        "messages_next_cursor": next_mail,
        "mailbox_counts": {k: totals[k] for k in ("incoming", "outgoing", "waiting")},
        "local_unread_messages": totals["unread"],
        "open_units": totals["open_units"],
        "observed_at": state.get("completed_at"),
        "oldest_open_order_minutes": oldest,
        "bottleneck": "dispatch"
        if totals["ready_orders"]
        else "blocked"
        if totals["blocked_orders"]
        else "no_open_dispatch",
        "dispatch_rate_percent": round(
            100 * totals["complete_dispatch_orders"] / totals["eligible_orders"], 1
        )
        if totals["eligible_orders"]
        else None,
        "average_first_dispatch_minutes": round(
            float(Decimal(totals["first_sum"]) / first_count), 1
        )
        if first_count
        else None,
        "average_complete_dispatch_minutes": round(
            float(Decimal(totals["complete_sum"]) / complete_count), 1
        )
        if complete_count
        else None,
        "risk_horizon_hours": 2,
        "scope": "All company sales orders; paginated oldest orders. Data is derived and may be delayed.",
    }
