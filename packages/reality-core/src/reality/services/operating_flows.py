"""Company-wide operating observations; business effects remain in shared services."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import cast, exists, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, aliased

from reality.db.core import (
    BusinessEvent,
    Commitment,
    Document,
    Movement,
    MovementCorrection,
    PartyRole,
    SourceRecord,
    now,
)
from reality.services import core, exceptions, return_dispositions

CLASSES = {
    "orders": [
        "overdue_outgoing_customer_commitment",
        "outgoing_commitment_due_soon",
        "outgoing_commitment_at_risk",
    ],
    "supply": ["overdue_incoming_supplier_commitment"],
    "stock": ["item_oversold"],
    "returns": ["return_unresolved", "announced_return_not_arrived"],
}


def _signal(findings: list, pending: int = 0, *, unknown: bool = False) -> str:
    if any(row.severity in {"critical", "high"} for row in findings):
        return "critical"
    if unknown:
        return "unknown"
    if findings:
        return "attention"
    return "progress" if pending else "clear"


def _evidence(kind: str, identity: str, label: str) -> dict:
    return {"kind": kind, "id": identity, "label": label}


def _risk_partition(
    scope: str, members: list[tuple[str, str, bool]], findings: list
) -> dict:
    """Partition the complete primary cohort; worst held condition wins per identity."""
    rank = {"in_plan": 0, "unclassified": 1, "at_risk": 2, "critical": 3}
    units: dict[str, str] = {}
    records: dict[str, str] = {}
    for record_id, unit_id, assessed in members:
        records[record_id] = unit_id
        category = "in_plan" if assessed else "unclassified"
        if rank[category] >= rank.get(units.get(unit_id, "in_plan"), 0):
            units[unit_id] = category
    for finding in findings:
        unit = records.get(finding.record_id)
        if unit is None:
            continue
        category = "critical" if finding.severity in {"high", "critical"} else "at_risk"
        if rank[category] > rank[units[unit]]:
            units[unit] = category
    counts = {
        category: sum(value == category for value in units.values())
        for category in rank
    }
    return {
        "scope": scope,
        "total": len(units),
        **counts,
        "coverage": "partial" if counts["unclassified"] else "complete",
    }


def _mail(
    session: Session, tenant: str, observed: datetime, instants: list, buckets: list
) -> dict:
    reply, ack = aliased(SourceRecord), aliased(SourceRecord)
    replies = (
        select(
            reply.source_system.label("system"),
            cast(reply.payload, JSONB)["in_reply_to"].astext.label("message_id"),
            func.min(reply.received_at).label("answered"),
        )
        .where(
            reply.tenant_id == tenant,
            reply.source_type == "outgoing",
            reply.source_system.startswith("company_simulator:", autoescape=True),
            reply.received_at <= observed,
        )
        .group_by(reply.source_system, "message_id")
        .subquery()
    )
    acknowledgements = (
        select(
            ack.source_system.label("system"),
            ack.external_id.label("message_source_id"),
        )
        .where(
            ack.tenant_id == tenant,
            ack.source_type == "ack",
            ack.received_at <= observed,
        )
        .group_by(ack.source_system, ack.external_id)
        .subquery()
    )
    customers = (
        select(PartyRole.party_id)
        .where(PartyRole.tenant_id == tenant, PartyRole.role == "customer")
        .subquery()
    )
    # Aggregate each reply/ack cohort once, then match exact identities. Multiple
    # replies or source versions cannot multiply incoming rows; no per-row SQL.
    rows = session.execute(
        select(
            SourceRecord.id,
            SourceRecord.received_at,
            replies.c.answered,
            acknowledgements.c.message_source_id.is_not(None).label("acknowledged"),
            customers.c.party_id.is_not(None).label("customer"),
            cast(SourceRecord.payload, JSONB)["kind"].astext.label("kind"),
            cast(SourceRecord.payload, JSONB)["subject"].astext.label("subject"),
        )
        .outerjoin(
            replies,
            (replies.c.system == SourceRecord.source_system)
            & (
                replies.c.message_id
                == cast(SourceRecord.payload, JSONB)["message_id"].astext
            ),
        )
        .outerjoin(
            acknowledgements,
            (acknowledgements.c.system == SourceRecord.source_system)
            & (acknowledgements.c.message_source_id == SourceRecord.id),
        )
        .outerjoin(
            customers,
            customers.c.party_id
            == cast(SourceRecord.payload, JSONB)["party_id"].astext,
        )
        .where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.source_system.startswith(
                "company_simulator:", autoescape=True
            ),
            SourceRecord.source_type == "incoming",
            SourceRecord.received_at <= observed,
        )
        .order_by(SourceRecord.received_at, SourceRecord.id)
    ).all()
    external = (
        session.scalar(
            select(func.count())
            .select_from(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_type == "email_message",
                SourceRecord.received_at <= observed,
                cast(SourceRecord.payload, JSONB)["direction"].astext.in_(
                    ["inbound", "incoming"]
                ),
            )
        )
        or 0
    )
    scope_present = bool(rows) or bool(
        session.scalar(
            select(SourceRecord.id)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == "company_simulator",
                SourceRecord.source_type == "live_run",
                SourceRecord.received_at <= observed,
            )
            .limit(1)
        )
    )
    coverage = "partial" if external else "complete" if scope_present else "unavailable"
    waiting = [r for r in rows if r.answered is None]
    recent = observed - timedelta(hours=1)
    series = [
        {
            "at": at.isoformat(),
            "unanswered": sum(
                r.received_at <= at and (r.answered is None or r.answered > at)
                for r in rows
            )
            if scope_present
            else None,
        }
        for at in instants
    ]
    for index, bucket in enumerate(buckets):
        start = datetime.fromisoformat(bucket["start"])
        end = datetime.fromisoformat(bucket["end"])
        final = index == len(buckets) - 1

        def contains(
            at: datetime | None,
            start: datetime = start,
            end: datetime = end,
            final: bool = final,
        ) -> bool:
            return at is not None and start <= at and (at < end or final and at == end)

        covered = scope_present and bucket["known"]
        bucket["messages_incoming"] = (
            sum(contains(row.received_at) for row in rows) if covered else None
        )
        bucket["message_first_replies"] = (
            sum(contains(row.answered) for row in rows) if covered else None
        )
    return {
        "coverage": coverage,
        "provider_reply_coverage": "unavailable",
        "unanswered": len(waiting) if scope_present else None,
        "unread": sum(not r.acknowledged for r in rows) if scope_present else None,
        "customer_requests": sum(r.customer and r.kind != "order" for r in waiting)
        if scope_present
        else None,
        "incoming_last_hour": sum(recent <= r.received_at <= observed for r in rows),
        "first_replies_last_hour": sum(
            r.answered is not None and recent <= r.answered <= observed for r in rows
        ),
        "external_incoming": external,
        "series": series,
        "oldest_unanswered_at": waiting[0].received_at.isoformat() if waiting else None,
        "signal": _signal([], len(waiting), unknown=coverage != "complete"),
        "evidence": [
            _evidence("source_record", r.id, r.subject or r.id) for r in waiting[:4]
        ],
    }


def observe(
    session: Session, tenant_id: str, *, observed_at: datetime | None = None
) -> dict:
    """
    BUSINESS PURPOSE:
    Explain intake, reply backlog, supplier receipts, stock risks and physical returns.

    BUSINESS RULE operating_flows.authority:
    Read complete company cohorts through shared effective fulfillment, exception,
    announcement and disposition semantics. No summed mixed-item quantity, new risk
    threshold, persisted observation or external success claim is introduced.

    BUSINESS RULE operating_flows.timing:
    Count first-recorded order identities, immutable local-mail recording/reply times
    and effective physical movement occurrence times separately. Bound chart output
    to thirteen five-minute buckets and evidence previews to four after full totals.
    Current corrections apply to movement observations; this is not historical stock.

    BUSINESS RULE operating_flows.coverage:
    Unknown provider replies/disposition remain unknown. Traffic lights describe only
    the evaluated named exceptions or pending work; they never certify Agent quality.
    """
    # reality-rule: operating_flows.authority
    tenant = core.get_tenant(session, tenant_id)
    observed = (
        observed_at or session.info.get("operations_snapshot_observed_at") or now()
    )
    first = datetime.fromtimestamp(
        int(observed.timestamp()) // 300 * 300, UTC
    ) - timedelta(hours=1)
    window_start = observed - timedelta(hours=1)
    instants = [window_start + timedelta(minutes=5 * i) for i in range(13)]
    findings = exceptions.operational_exceptions(
        session,
        tenant_id,
        as_of=observed,
        classes=[c for values in CLASSES.values() for c in values],
    )
    grouped = {
        key: [row for row in findings if row.class_id in classes]
        for key, classes in CLASSES.items()
    }
    if session.info.get("operations_snapshot_consistent"):
        from reality.services.delivery_reads import _fulfillment_cohort

        cohort = _fulfillment_cohort(tenant_id).subquery()
        commitments = list(
            core._metadata_rows(
                session.execute(
                    select(cohort)
                    .where(
                        (cohort.c.open > 0)
                        | (
                            (cohort.c.type == "supplier_delivery")
                            & (cohort.c.open == 0)
                            & (cohort.c.fulfilled > 0)
                        )
                    )
                    .order_by(cohort.c.created_at, cohort.c.id)
                )
            )
        )
        work = [r for r in commitments if r.open > 0]
        outgoing = [r for r in work if r.type == "customer_delivery"]
        incoming = [r for r in work if r.type == "supplier_delivery"]
        received = [
            r
            for r in commitments
            if r.type == "supplier_delivery" and r.open == 0 and r.fulfilled > 0
        ]
        received_lines = len(received)
        supply_preview = incoming[:4] or received[:4]
    else:
        commitments = list(
            session.scalars(
                select(Commitment)
                .where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.status != "cancelled",
                    Commitment.type.in_(["customer_delivery", "supplier_delivery"]),
                )
                .order_by(Commitment.created_at, Commitment.id)
            )
        )
        terms = core.commitment_terms(
            session,
            tenant_id,
            [c.id for c in commitments],
            _commitments={c.id: c for c in commitments},
        )
        work = [
            SimpleNamespace(
                id=c.id,
                type=c.type,
                document_id=c.document_id,
                due_at=terms[c.id].due_at,
            )
            for c in commitments
            if terms[c.id].open > 0
        ]
        outgoing = [r for r in work if r.type == "customer_delivery"]
        incoming = [r for r in work if r.type == "supplier_delivery"]
        received_lines = sum(
            c.type == "supplier_delivery"
            and terms[c.id].open == 0
            and terms[c.id].fulfilled > 0
            for c in commitments
        )
        supply_preview = (
            incoming[:4]
            or [
                c
                for c in commitments
                if c.type == "supplier_delivery"
                and terms[c.id].open == 0
                and terms[c.id].fulfilled > 0
            ][:4]
        )
    supply_labels = dict(
        session.execute(
            select(Document.id, Document.number).where(
                Document.tenant_id == tenant_id,
                Document.id.in_(
                    [r.document_id for r in supply_preview if r.document_id]
                ),
            )
        ).all()
    )
    recorded = session.execute(
        select(
            Document.id,
            Document.number,
            func.min(BusinessEvent.recorded_at).label("at"),
        )
        .join(
            BusinessEvent,
            (BusinessEvent.tenant_id == Document.tenant_id)
            & (BusinessEvent.subject_id == Document.id)
            & (BusinessEvent.subject_type == "document")
            & (BusinessEvent.event_type == "document.recorded"),
        )
        .where(
            Document.tenant_id == tenant_id,
            BusinessEvent.tenant_id == tenant_id,
            Document.type == "sales_order",
        )
        .group_by(Document.id, Document.number)
        .having(func.min(BusinessEvent.recorded_at) <= observed)
        .order_by(func.min(BusinessEvent.recorded_at).desc(), Document.id)
    ).all()
    corrected = exists().where(
        MovementCorrection.tenant_id == tenant_id,
        MovementCorrection.original_movement_id == Movement.id,
    )
    movements = session.scalars(
        select(Movement)
        .where(
            Movement.tenant_id == tenant_id,
            ~corrected,
            Movement.occurred_at <= observed,
            (Movement.type == "return") | (Movement.occurred_at >= first),
        )
        .order_by(Movement.occurred_at, Movement.id)
    ).all()
    recent = observed - timedelta(hours=1)
    arrivals = [m for m in movements if m.type == "return"]
    receipts = [m for m in movements if m.type == "receipt" and m.commitment_id]
    dispatched = [m for m in movements if m.type == "shipment"]
    resolving = [
        m
        for m in movements
        if m.resolves_movement_id
        and m.type in {"transfer", "adjustment", "supplier_return"}
    ]
    pending, resolved, unknown = [], [], []
    for movement in arrivals:
        try:
            summary = return_dispositions.return_disposition_summary(
                session, tenant_id, movement.id
            )
        except core.InvalidOperation:
            unknown.append(movement)
        else:
            (pending if summary["unresolved"] > 0 else resolved).append(movement)
    expected = [
        a
        for a in core.return_announcements(session, tenant_id, status="open")
        if core.announcement_outstanding(session, tenant_id, a) > 0
    ]
    # reality-rule: operating_flows.timing
    buckets = []
    for i, start in enumerate([first + timedelta(minutes=5 * j) for j in range(13)]):
        end = min(start + timedelta(minutes=5), observed)
        start = max(start, window_start)
        if end <= start:
            continue
        buckets.append(
            {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "known": start >= tenant.created_at,
                "orders_received": sum(start <= r.at < end for r in recorded),
                "dispatch_movements": sum(
                    start <= m.occurred_at < end for m in dispatched
                ),
                "receipts": sum(start <= m.occurred_at < end for m in receipts),
                "return_arrivals": sum(start <= m.occurred_at < end for m in arrivals),
                "return_dispositions": sum(
                    start <= m.occurred_at < end for m in resolving
                ),
            }
        )
    mail = _mail(session, tenant_id, observed, instants, buckets)
    for point in mail["series"]:
        if datetime.fromisoformat(point["at"]) < tenant.created_at:
            point["unanswered"] = None
    mail["backlog_change_last_hour"] = (
        None
        if mail["series"][0]["unanswered"] is None
        else mail["unanswered"] - mail["series"][0]["unanswered"]
    )
    # reality-rule: operating_flows.coverage
    values = {
        "orders": {
            "open_orders": len({r.document_id for r in outgoing if r.document_id}),
            "unlinked_open_lines": sum(r.document_id is None for r in outgoing),
            "received_last_hour": sum(recent <= r.at <= observed for r in recorded),
            "dispatch_movements_last_hour": sum(
                m.occurred_at >= recent for m in dispatched
            ),
            "signal": _signal(grouped["orders"], len(outgoing)),
            "evidence": [
                _evidence("document", r.id, r.number or r.id) for r in recorded[:4]
            ],
        },
        "supply": {
            "open_lines": len(incoming),
            "fully_received_lines": received_lines,
            "unknown_due_lines": sum(r.due_at is None for r in incoming),
            "receipts_last_hour": sum(m.occurred_at >= recent for m in receipts),
            "signal": _signal(
                grouped["supply"],
                len(incoming),
                unknown=any(r.due_at is None for r in incoming),
            ),
            "evidence": [
                _evidence("commitment", r.id, supply_labels.get(r.document_id) or r.id)
                for r in supply_preview
            ],
        },
        "stock": {
            "oversold_items": len({r.record_id for r in grouped["stock"]}),
            "signal": _signal(grouped["stock"]),
            "evidence": [],
        },
        "returns": {
            "expected_announcements": len(expected),
            "arrived_positions": len(arrivals),
            "arrivals_last_hour": sum(m.occurred_at >= recent for m in arrivals),
            "resolved_positions": len(resolved),
            "pending_positions": len(pending),
            "unknown_positions": len(unknown),
            "coverage": "partial" if unknown else "complete",
            "signal": _signal(
                grouped["returns"], len(pending) + len(expected), unknown=bool(unknown)
            ),
            "evidence": [
                _evidence("movement", m.id, m.id)
                for m in (pending + unknown + resolved)[:4]
            ],
        },
    }
    values["orders"]["risk"] = _risk_partition(
        "open_orders",
        [
            (row.id, row.document_id, row.due_at is not None)
            for row in outgoing
            if row.document_id
        ],
        grouped["orders"],
    )
    values["supply"]["risk"] = _risk_partition(
        "open_supplier_lines",
        [(row.id, row.id, row.due_at is not None) for row in incoming],
        grouped["supply"],
    )
    values["stock"]["risk"] = _risk_partition(
        "oversold_items",
        [(row.record_id, row.record_id, True) for row in grouped["stock"]],
        grouped["stock"],
    )
    values["returns"]["risk"] = _risk_partition(
        "pending_return_positions",
        [(row.id, row.id, False) for row in pending],
        grouped["returns"],
    )
    mail["risk"] = {
        "scope": "unanswered_local_messages",
        "total": mail["unanswered"],
        "in_plan": None,
        "at_risk": None,
        "critical": None,
        "unclassified": mail["unanswered"],
        "coverage": "unavailable",
    }
    for key, rows in grouped.items():
        values[key]["exception_total"] = len(rows)
        values[key]["evaluated_classes"] = CLASSES[key]
        values[key]["exceptions"] = [
            {
                "id": r.id,
                "class_id": r.class_id,
                "severity": r.severity,
                "title": r.title,
                "kind": r.record_type,
                "record_id": r.record_id,
            }
            for r in rows[:4]
        ]
        if key == "stock":
            values[key]["evidence"] = [
                _evidence(r.record_type, r.record_id, r.title) for r in rows[:4]
            ]
    return {
        "observed_at": observed.isoformat(),
        "start": window_start.isoformat(),
        "coverage_start": tenant.created_at.isoformat(),
        "scope": "company_wide_live_60_minutes",
        "buckets": buckets,
        "messages": mail,
        **values,
    }
