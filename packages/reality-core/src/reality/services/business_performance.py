"""Read-only trading operations derived from ordinary company Reality."""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import cast, exists, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, aliased

from reality.db.core import (
    ChangeProposal,
    Commitment,
    CommitmentHold,
    Document,
    Item,
    Movement,
    MovementCorrection,
    Party,
    PartyHold,
    SourceRecord,
    now,
)
from reality.services import core
from reality.services.projections import _open_work_rows


def overview(
    session: Session,
    tenant_id: str,
    *,
    document_ids: list[str] | None = None,
    received_at_by_document: dict[str, datetime] | None = None,
    order_filter: str = "",
    mail_filter: str = "",
) -> dict[str, Any]:
    observed = now()
    query = (
        select(Document, SourceRecord.received_at)
        .outerjoin(
            SourceRecord,
            (SourceRecord.tenant_id == Document.tenant_id)
            & (SourceRecord.id == Document.source_record_id),
        )
        .where(Document.tenant_id == tenant_id, Document.type == "sales_order")
    )
    if document_ids is not None:
        query = query.where(Document.id.in_(document_ids))
    documents = list(session.execute(query))
    cs = list(
        session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_id.in_([d.id for d, _ in documents]),
                Commitment.type == "customer_delivery",
            )
        )
    )
    terms = core.commitment_terms(session, tenant_id, [c.id for c in cs])
    held = set(
        session.scalars(
            select(CommitmentHold.commitment_id).where(
                CommitmentHold.tenant_id == tenant_id,
                CommitmentHold.released_at.is_(None),
            )
        )
    )
    held_parties = set(
        session.scalars(
            select(PartyHold.party_id).where(
                PartyHold.tenant_id == tenant_id,
                PartyHold.hold_type == "delivery",
                PartyHold.released_at.is_(None),
            )
        )
    )
    corrected = select(MovementCorrection.original_movement_id).where(
        MovementCorrection.tenant_id == tenant_id
    )
    movements = list(
        session.scalars(
            select(Movement)
            .where(
                Movement.tenant_id == tenant_id,
                Movement.type == "shipment",
                Movement.commitment_id.in_([c.id for c in cs]),
                Movement.id.not_in(corrected),
            )
            .order_by(Movement.occurred_at, Movement.id)
        )
    )
    by_c, by_d = {}, {}
    for m in movements:
        by_c.setdefault(m.commitment_id, []).append(m)
    for c in cs:
        by_d.setdefault(c.document_id, []).append(c)
    parties = {
        p.id: p.name
        for p in session.scalars(select(Party).where(Party.tenant_id == tenant_id))
    }
    counts = {
        k: 0
        for k in (
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
        )
    }
    rows, first_samples, complete_samples = [], [], []
    work = _open_work_rows(
        session,
        tenant_id,
        [c for c in cs if c.status == "open" and terms[c.id].open > 0],
        terms,
    )
    opened_total = Decimal("0.0000")
    for d, received in documents:
        received = (received_at_by_document or {}).get(d.id, received)
        lines = by_d.get(d.id, [])
        active = [c for c in lines if c.status != "cancelled"]
        outstanding = [c for c in active if terms[c.id].open > 0]
        opened = sum((terms[c.id].open for c in outstanding), Decimal("0.0000"))
        shipped = sum((terms[c.id].fulfilled for c in lines), Decimal(0))
        cancelled = bool(lines) and not active
        complete = bool(active) and not outstanding and shipped > 0
        hold = bool(outstanding) and (
            d.party_id in held_parties or any(c.id in held for c in outstanding)
        )
        missing = any(terms[c.id].reserved < terms[c.id].open for c in outstanding)
        overdue = any(
            terms[c.id].due_at and terms[c.id].due_at < observed for c in outstanding
        )
        queue_row = work.queue.get(d.id)
        blockers = queue_row["blocking_reasons"] if queue_row else []
        ready = bool(outstanding) and bool(queue_row and queue_row["ship_ready"])
        risk = bool(blockers) and any(
            terms[c.id].due_at
            and observed <= terms[c.id].due_at <= observed + timedelta(hours=2)
            for c in outstanding
        )
        state = (
            "cancelled"
            if cancelled
            else "complete"
            if complete
            else "partial"
            if shipped > 0
            else "unshipped"
            if outstanding
            else "unresolved"
        )
        flags = [state]
        for flag, condition in (
            ("ready", ready),
            ("blocked", bool(outstanding) and not ready),
            ("reservation_blocked", missing),
            ("held", hold),
            ("overdue", overdue),
            ("at_risk", risk),
        ):
            if condition:
                flags.append(flag)
        for flag, key in (
            ("unshipped", "unshipped_orders"),
            ("partial", "partial_orders"),
            ("complete", "complete_dispatch_orders"),
            ("cancelled", "cancelled_orders"),
            ("ready", "ready_orders"),
            ("blocked", "blocked_orders"),
            ("reservation_blocked", "reservation_blocked_orders"),
            ("held", "held_orders"),
            ("overdue", "overdue_orders"),
            ("at_risk", "at_risk_orders"),
        ):
            counts[key] += flag in flags
        counts["eligible_orders"] += bool(active)
        counts["orders_received_last_hour"] += bool(
            received and observed - timedelta(hours=1) <= received <= observed
        )
        counts["unknown_receipt_orders"] += received is None
        opened_total += opened
        times = [m.occurred_at for c in lines for m in by_c.get(c.id, [])]
        completion = []
        for c in active:
            cumulative = Decimal(0)
            for m in by_c.get(c.id, []):
                cumulative += m.quantity
                if cumulative >= terms[c.id].quantity:
                    completion.append(m.occurred_at)
                    break
        first = min(times) if times else None
        finished = (
            max(completion) if complete and len(completion) == len(active) else None
        )
        counts["invalid_timing_orders"] += any(
            t < received for t in (first, finished) if t and received
        )
        if first and received and first >= received:
            first_samples.append((first - received).total_seconds() / 60)
        if finished and received and finished >= received:
            complete_samples.append((finished - received).total_seconds() / 60)
        counts["orders_completed_last_hour"] += bool(
            finished and observed - timedelta(hours=1) <= finished <= observed
        )
        for flag, condition in (
            ("eligible", bool(active)),
            (
                "received_last_hour",
                bool(
                    received and observed - timedelta(hours=1) <= received <= observed
                ),
            ),
            (
                "completed_last_hour",
                bool(
                    finished and observed - timedelta(hours=1) <= finished <= observed
                ),
            ),
            ("first_dispatch_sample", bool(first and received and first >= received)),
            (
                "complete_dispatch_sample",
                bool(finished and received and finished >= received),
            ),
        ):
            if condition:
                flags.append(flag)
        rows.append(
            {
                "document_id": d.id,
                "number": d.number,
                "source_record_id": d.source_record_id,
                "party_id": d.party_id,
                "party_name": parties.get(d.party_id),
                "received_at": received.isoformat() if received else None,
                "open_units": str(opened),
                "first_dispatch_minutes": round(
                    (first - received).total_seconds() / 60, 1
                )
                if first and received and first >= received
                else None,
                "complete_dispatch_minutes": round(
                    (finished - received).total_seconds() / 60, 1
                )
                if finished and received and finished >= received
                else None,
                "flags": flags,
                "blocker_codes": blockers,
                "commitment_ids": [c.id for c in lines],
                "due_at": min(
                    (terms[c.id].due_at for c in outstanding if terms[c.id].due_at),
                    default=None,
                ),
                "age_minutes": round((observed - received).total_seconds() / 60, 1)
                if received
                else None,
            }
        )
    rows.sort(key=lambda row: (row["received_at"] or "", row["document_id"]))
    all_movements = list(
        session.scalars(
            select(Movement).where(
                Movement.tenant_id == tenant_id,
                Movement.type.in_(["receipt", "shipment"]),
                Movement.occurred_at >= observed - timedelta(hours=1),
                Movement.id.not_in(corrected),
            )
        )
    )
    goods = {}
    for movement in all_movements:
        values = goods.setdefault(
            movement.item_id,
            {
                "item_id": movement.item_id,
                "received": Decimal(0),
                "shipped": Decimal(0),
            },
        )
        values["received" if movement.type == "receipt" else "shipped"] += (
            movement.quantity
        )
    items = {
        i.id: i
        for i in session.scalars(select(Item).where(Item.tenant_id == tenant_id))
    }
    goods_flow = [
        {
            **values,
            "name": items[key].name,
            "sku": items[key].sku,
            "received": str(values["received"]),
            "shipped": str(values["shipped"]),
        }
        for key, values in goods.items()
        if key in items
    ]
    suppliers = list(
        session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.type == "supplier_delivery",
                Commitment.status != "cancelled",
            )
        )
    )
    supplier_terms = core.commitment_terms(
        session, tenant_id, [c.id for c in suppliers]
    )
    replenishment = [
        {
            "commitment_id": c.id,
            "document_id": c.document_id,
            "item_id": c.item_id,
            "item_name": items[c.item_id].name if c.item_id in items else c.item_id,
            "quantity": str(supplier_terms[c.id].open),
            "due_at": supplier_terms[c.id].due_at,
        }
        for c in suppliers
        if supplier_terms[c.id].open > 0
    ]
    direction = cast(SourceRecord.payload, JSONB)["direction"].astext
    mail_query = select(SourceRecord).where(
        SourceRecord.tenant_id == tenant_id,
        direction.in_(["inbound", "outbound", "incoming", "outgoing"]),
        or_(
            SourceRecord.source_type == "email_message",
            SourceRecord.source_system.startswith("company_simulator:", autoescape=True)
            & SourceRecord.source_type.in_(["incoming", "outgoing"]),
        ),
    )
    reply_source = aliased(SourceRecord)
    waiting = (
        SourceRecord.source_system.startswith("company_simulator:", autoescape=True)
        & (SourceRecord.source_type == "incoming")
        & ~exists().where(
            reply_source.tenant_id == tenant_id,
            reply_source.source_system == SourceRecord.source_system,
            reply_source.source_type == "outgoing",
            cast(reply_source.payload, JSONB)["in_reply_to"].astext
            == cast(SourceRecord.payload, JSONB)["message_id"].astext,
        )
    )
    mailbox_counts = {
        "incoming": session.scalar(
            select(func.count()).select_from(
                mail_query.where(direction.in_(["incoming", "inbound"])).subquery()
            )
        )
        or 0,
        "outgoing": session.scalar(
            select(func.count()).select_from(
                mail_query.where(direction.in_(["outgoing", "outbound"])).subquery()
            )
        )
        or 0,
        "waiting": session.scalar(
            select(func.count()).select_from(mail_query.where(waiting).subquery())
        )
        or 0,
    }
    if mail_filter == "incoming":
        mail_query = mail_query.where(direction.in_(["incoming", "inbound"]))
    elif mail_filter == "outgoing":
        mail_query = mail_query.where(direction.in_(["outgoing", "outbound"]))
    elif mail_filter == "waiting":
        mail_query = mail_query.where(waiting)
    recent_mail = list(
        session.scalars(
            mail_query.order_by(SourceRecord.received_at.desc(), SourceRecord.id).limit(
                50
            )
        )
    )
    messages = []
    for source in recent_mail:
        payload = json.loads(source.payload)
        message = payload.get("message", payload)
        original = None
        if (
            source.source_type == "outgoing"
            and source.source_system.startswith("company_simulator:")
            and payload.get("in_reply_to")
        ):
            original_source = session.scalar(
                select(SourceRecord).where(
                    SourceRecord.tenant_id == tenant_id,
                    cast(SourceRecord.payload, JSONB)["message_id"].astext
                    == payload["in_reply_to"],
                    SourceRecord.source_system == source.source_system,
                    SourceRecord.source_type == "incoming",
                )
            )
            if original_source:
                raw = json.loads(original_source.payload)
                original = {
                    "source_record_id": original_source.id,
                    "subject": raw.get("subject", ""),
                    "body": raw.get("body", ""),
                    "recorded_at": original_source.received_at.isoformat(),
                }
        reply_recorded = None
        replies = []
        if source.source_type == "incoming" and source.source_system.startswith(
            "company_simulator:"
        ):
            reply_sources = session.scalars(
                select(SourceRecord)
                .where(
                    SourceRecord.tenant_id == tenant_id,
                    SourceRecord.source_system == source.source_system,
                    SourceRecord.source_type == "outgoing",
                    cast(SourceRecord.payload, JSONB)["in_reply_to"].astext
                    == payload.get("message_id"),
                )
                .order_by(SourceRecord.received_at, SourceRecord.id)
            )
            for reply_source in reply_sources:
                raw = json.loads(reply_source.payload)
                replies.append(
                    {
                        "source_record_id": reply_source.id,
                        "subject": raw.get("subject", ""),
                        "body": raw.get("body", ""),
                        "recorded_at": reply_source.received_at.isoformat(),
                    }
                )
            reply_recorded = bool(replies)
        messages.append(
            {
                "reply_recorded": reply_recorded,
                "replies": replies,
                "source_record_id": source.id,
                "subject": message.get("subject", ""),
                "body": message.get("body", message.get("text", "")),
                "direction": payload.get("direction"),
                "recorded_at": source.received_at.isoformat(),
                "original": original,
            }
        )
    ack = aliased(SourceRecord)
    local_unread = (
        session.scalar(
            select(func.count())
            .select_from(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system.startswith(
                    "company_simulator:", autoescape=True
                ),
                SourceRecord.source_type == "incoming",
                ~exists().where(
                    ack.tenant_id == tenant_id,
                    ack.source_system == SourceRecord.source_system,
                    ack.source_type == "ack",
                    ack.external_id == SourceRecord.id,
                ),
            )
        )
        or 0
    )
    pending_decisions = (
        session.scalar(
            select(func.count())
            .select_from(ChangeProposal)
            .where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.status == "proposed",
            )
        )
        or 0
    )
    oldest = max(
        (
            row["age_minutes"]
            for row in rows
            if row["age_minutes"] is not None
            and ("unshipped" in row["flags"] or "partial" in row["flags"])
        ),
        default=None,
    )
    bottleneck = (
        "dispatch"
        if counts["ready_orders"]
        else "blocked"
        if counts["blocked_orders"]
        else "no_open_dispatch"
    )
    inventory = [
        {
            "item_id": row["item"].id,
            "name": row["item"].name,
            "sku": row["item"].sku,
            "physical": str(row["physical"]),
            "reserved": str(row["reserved"]),
            "available": str(row["available"]),
            "incoming": str(row["incoming"]),
        }
        for row in core.inventory_rows(session, tenant_id)
    ]
    recent_documents = [
        {
            "id": d.id,
            "number": d.number,
            "type": d.type,
            "party_name": parties.get(d.party_id),
            "amount": str(d.gross_amount) if d.gross_amount is not None else None,
            "currency": d.currency,
        }
        for d in session.scalars(
            select(Document)
            .join(
                SourceRecord,
                (SourceRecord.tenant_id == Document.tenant_id)
                & (SourceRecord.id == Document.source_record_id),
            )
            .where(Document.tenant_id == tenant_id)
            .order_by(SourceRecord.received_at.desc(), Document.id)
            .limit(20)
        )
    ]
    return {
        **counts,
        "recent_documents": recent_documents,
        "inventory": inventory[:100],
        "goods_flow_last_hour": goods_flow,
        "replenishment": replenishment[:100],
        "open_replenishment_lines": len(replenishment),
        "messages": messages,
        "mailbox_counts": mailbox_counts,
        "local_unread_messages": local_unread,
        "pending_decisions": pending_decisions,
        "oldest_open_order_minutes": oldest,
        "bottleneck": bottleneck,
        "observed_at": observed.isoformat(),
        "open_units": str(opened_total),
        "dispatch_rate_percent": round(
            100 * counts["complete_dispatch_orders"] / counts["eligible_orders"], 1
        )
        if counts["eligible_orders"]
        else None,
        "average_first_dispatch_minutes": round(
            sum(first_samples) / len(first_samples), 1
        )
        if first_samples
        else None,
        "average_complete_dispatch_minutes": round(
            sum(complete_samples) / len(complete_samples), 1
        )
        if complete_samples
        else None,
        "first_dispatch_sample_orders": len(first_samples),
        "complete_dispatch_sample_orders": len(complete_samples),
        "risk_horizon_hours": 2,
        "orders": [
            row for row in rows if not order_filter or order_filter in row["flags"]
        ][:200],
        "order_count": len(rows),
        "scope": "All company sales orders; oldest 200 orders shown. Quantities are item-unit counts, not weight or money.",
    }
