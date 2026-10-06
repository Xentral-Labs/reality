"""Durable local outside-world intake and simulated mailbox, never real transport."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from reality.db.core import (
    BusinessEvent,
    Commitment,
    Document,
    DocumentLine,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Party,
    PartyRole,
    SourceRecord,
    now,
)
from reality.services import core, scheduled_jobs
from reality.services.memberships import Principal, require_owner

SYSTEM = "company_simulator"
KINDS = {
    "customer_email",
    "supplier_email",
    "order",
    "status_query",
    "cancellation",
    "return_request",
    "supplier_delay",
}


def _owner(session, tenant, actor):
    from reality.db.core import AppUser, Tenant
    from reality.services.account_policy import account_eligible

    require_owner(session, tenant, Principal(actor))
    user = session.get(AppUser, actor)
    company = session.get(Tenant, tenant)
    if (
        not user
        or not account_eligible(session, user)
        or not company
        or company.archived_at
    ):
        raise core.NotFound("Live company not found")


def _json(row):
    return json.loads(row.payload)


def _source(session, tenant, system, kind, key):
    return session.scalar(
        select(SourceRecord)
        .where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.source_system == system,
            SourceRecord.source_type == kind,
            SourceRecord.external_id == key,
        )
        .order_by(SourceRecord.version.desc())
        .limit(1)
    )


def _store(session, tenant, system, kind, key, payload):
    core._lock_source_identity(session, tenant, system, kind, key)
    existing = _source(session, tenant, system, kind, key)
    if existing:
        if _json(existing) != payload:
            raise ValueError("Request identity already has a different payload")
        return existing
    return core.store_source_record(session, tenant, system, kind, key, payload)[0]


def _run(session, tenant, run_id, *, lock=False):
    if lock:
        from reality.services.business_locks import lock_delivery_state

        lock_delivery_state(session, tenant)
    query = select(SourceRecord).where(
        SourceRecord.tenant_id == tenant,
        SourceRecord.id == run_id,
        SourceRecord.source_system == SYSTEM,
        SourceRecord.source_type == "live_run",
    )
    row = session.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise core.NotFound("Live simulator run not found")
    return row, _json(row)


def _namespace(run_id):
    return f"company_simulator:{run_id}"


def _rows(session, tenant, run_id, kind, *, limit=100000):
    return list(
        session.scalars(
            select(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == _namespace(run_id),
                SourceRecord.source_type == kind,
            )
            .order_by(SourceRecord.received_at, SourceRecord.id)
            .limit(limit)
        )
    )


def start(
    session,
    tenant,
    actor,
    *,
    request_id,
    rate=180,
    hours=72,
    max_orders=20000,
    max_backlog=2000,
    confirmed=False,
):
    if confirmed is not True:
        raise ValueError("Exact launch confirmation required")
    _owner(session, tenant, actor)
    from reality.services.business_locks import lock_delivery_state

    lock_delivery_state(session, tenant)
    if type(rate) is not int or not 150 <= rate <= 200 or hours not in {72, 96}:
        raise ValueError("Rate must be 150–200 and duration 72 or 96 hours")
    if (
        not 1 <= max_backlog <= max_orders <= 20000
        or not request_id
        or len(request_id) > 100
    ):
        raise ValueError("Invalid bounded launch")
    core._lock_source_identity(session, tenant, SYSTEM, "live_run", request_id)
    existing = _source(session, tenant, SYSTEM, "live_run", request_id)
    if existing:
        data = _json(existing)
        if (
            data["rate"],
            data["hours"],
            data["owner_id"],
            data["max_orders"],
            data["max_backlog"],
        ) != (rate, hours, actor, max_orders, max_backlog):
            raise ValueError("Launch request conflicts")
        return {
            "run_id": existing.id,
            "company_id": tenant,
            "configuration": {k: v for k, v in data.items() if k != "seed"},
        }
    roles = list(
        session.execute(
            select(Party.id, Party.name, PartyRole.role)
            .join(
                PartyRole,
                (PartyRole.tenant_id == Party.tenant_id)
                & (PartyRole.party_id == Party.id),
            )
            .where(Party.tenant_id == tenant)
        )
    )
    refs = {
        role: [{"id": p, "name": n} for p, n, r in roles if r == role]
        for role in ["company", "customer", "supplier"]
    }
    items = list(
        session.scalars(select(Item).where(Item.tenant_id == tenant).order_by(Item.id))
    )
    locations = list(
        session.scalars(
            select(Location).where(Location.tenant_id == tenant).order_by(Location.id)
        )
    )
    if not all(refs.values()) or not items or not locations:
        raise ValueError(
            "Live company requires company, customer, supplier, item and location masters"
        )
    at = now()
    data = {
        "owner_id": actor,
        "rate": rate,
        "hours": hours,
        "max_orders": max_orders,
        "max_backlog": max_backlog,
        "started_at": at.isoformat(),
        "ends_at": (at + timedelta(hours=hours)).isoformat(),
        "references": refs,
        "items": [{"id": i.id, "sku": i.sku, "name": i.name} for i in items],
        "location_id": locations[0].id,
        "seed": hashlib.sha256(request_id.encode()).hexdigest(),
    }
    row = _store(session, tenant, SYSTEM, "live_run", request_id, data)
    schedule = scheduled_jobs.create_schedule(
        session,
        tenant,
        actor,
        "simulator.world",
        {"run_id": row.id},
        request_id=f"live:{row.id}",
        interval_seconds=round(3600 / rate),
    )
    scheduled_jobs.control_schedule(
        session,
        tenant,
        actor,
        schedule.id,
        "resume",
        schedule.revision,
        f"live-start:{row.id}",
    )
    for job_type, interval in [("simulator.reactions", 30), ("simulator.monitor", 60)]:
        extra = scheduled_jobs.create_schedule(
            session,
            tenant,
            actor,
            job_type,
            {"run_id": row.id},
            request_id=f"{job_type}:{row.id}",
            interval_seconds=interval,
        )
        scheduled_jobs.control_schedule(
            session,
            tenant,
            actor,
            extra.id,
            "resume",
            extra.revision,
            f"start:{extra.id}",
        )
    return {
        "run_id": row.id,
        "company_id": tenant,
        "configuration": {k: v for k, v in data.items() if k != "seed"},
        "schedule_id": schedule.id,
    }


def preview_event(session, tenant, run_id, event):
    _, config = _run(session, tenant, run_id)
    kind = event.get("kind")
    if kind not in KINDS:
        raise ValueError("Unknown world-event template")
    party_id = event.get("party_id")
    expected_role = "supplier" if kind.startswith("supplier") else "customer"
    party = next(
        (p for p in config["references"][expected_role] if p["id"] == party_id), None
    )
    if not party:
        raise ValueError("Existing same-company party with the correct role required")
    document_id = event.get("document_id")
    if document_id:
        doc = session.scalar(
            select(Document).where(
                Document.tenant_id == tenant, Document.id == document_id
            )
        )
        if doc is None or doc.party_id != party_id:
            raise ValueError("Document does not belong to the selected party")
        if kind in {
            "supplier_delay",
            "cancellation",
            "return_request",
        } and doc.type != (
            "purchase_order" if kind == "supplier_delay" else "sales_order"
        ):
            raise ValueError("This event requires the matching order type")
    if kind in {"supplier_delay", "cancellation", "return_request"} and not document_id:
        raise ValueError("This event requires an existing order")
    payload = {
        "kind": kind,
        "party_id": party_id,
        "document_id": document_id,
        "subject": event.get("subject") or f"{kind.replace('_', ' ').title()}",
        "body": event.get("body")
        or "Please review the current recorded business status.",
        "from": f"{party_id}@example.invalid",
        "to": "company@example.invalid",
        "transport": "local_simulation",
        "synthetic": True,
    }
    if (
        not isinstance(payload["subject"], str)
        or not isinstance(payload["body"], str)
        or len(payload["subject"]) > 300
        or len(payload["body"]) > 20000
    ):
        raise ValueError("Invalid message text")
    if event.get("requested_quantity") is not None:
        value = Decimal(str(event["requested_quantity"]))
        if (
            kind not in {"cancellation", "return_request"}
            or not value.is_finite()
            or value <= 0
        ):
            raise ValueError(
                "A positive requested cancellation/return quantity is required"
            )
        payload["requested_quantity"] = str(value)
    if event.get("case_family"):
        if not isinstance(event["case_family"], str) or len(event["case_family"]) > 80:
            raise ValueError("Invalid case family")
        payload["case_family"] = event["case_family"]
    for field, source_type in [
        ("original_message_source_id", "incoming"),
        ("reply_source_record_id", "outgoing"),
    ]:
        if event.get(field):
            parent = session.scalar(
                select(SourceRecord).where(
                    SourceRecord.tenant_id == tenant,
                    SourceRecord.id == event[field],
                    SourceRecord.source_system == _namespace(run_id),
                    SourceRecord.source_type == source_type,
                )
            )
            if (
                parent is None
                or _json(parent).get("document_id") != document_id
                or _json(parent).get("party_id") != party_id
            ):
                raise ValueError(
                    "Message context does not match this party and document"
                )
            payload[field] = parent.id
            if source_type == "outgoing":
                payload["in_reply_to"] = _json(parent)["message_id"]
    if kind == "order":
        item = next(
            (i for i in config["items"] if i["id"] == event.get("item_id")), None
        )
        if (
            item is None
            or type(event.get("quantity")) is not int
            or not 1 <= event["quantity"] <= 100
        ):
            raise ValueError("Existing item and quantity 1–100 required")
        amount = Decimal(str(event.get("amount", "0")))
        if not amount.is_finite() or amount <= 0 or amount > 100000:
            raise ValueError("A positive stated order amount is required")
        payload["destination"] = {
            "name": party["name"] + " receiving desk",
            "street": "Harbour Road 12",
            "postal_code": "20095",
            "city": "Hamburg",
            "country": "DE",
        }
        payload.update(
            item_id=item["id"], quantity=event["quantity"], amount=str(amount)
        )
        if event.get("unit_price") is not None:
            price = Decimal(str(event["unit_price"]))
            if not price.is_finite() or price < 0:
                raise ValueError("A stated unit price must be finite and non-negative")
            payload["unit_price"] = str(price)
    return payload


def inject(
    session,
    tenant,
    actor,
    run_id,
    event,
    *,
    request_id,
    confirmed=False,
    origin="manual",
    at=None,
):
    if confirmed is not True:
        raise ValueError("Exact event confirmation required")
    _owner(session, tenant, actor)
    _, config = _run(session, tenant, run_id, lock=True)
    if not request_id or len(request_id) > 128:
        raise ValueError("Invalid event retry identity")
    payload = preview_event(session, tenant, run_id, event)
    prior = _source(session, tenant, _namespace(run_id), "incoming", request_id)
    if prior:
        old = _json(prior)
        if old["submitted"] != payload or old["origin"] != origin:
            raise ValueError("Event retry payload conflicts")
        return {"source_record_id": prior.id, **old}
    if now() >= datetime.fromisoformat(config["ends_at"]):
        raise ValueError("Live run has ended")
    _run_limits(session, tenant, run_id, config, payload["kind"] == "order")
    release_instant = at or now()
    document_id = payload["document_id"]
    receipt = {}
    if payload["kind"] == "order":
        ordered_at = release_instant
        source, document, lines, commitments = core.create_manual_order(
            session,
            tenant,
            "sales",
            f"LIVE-{hashlib.sha256((run_id + request_id).encode()).hexdigest()[:16]}",
            config["references"]["company"][0]["id"],
            payload["party_id"],
            config["location_id"],
            [
                {
                    "item_id": payload["item_id"],
                    "quantity": str(payload["quantity"]),
                    "gross_amount": payload["amount"],
                    **(
                        {"unit_price": payload["unit_price"]}
                        if "unit_price" in payload
                        else {}
                    ),
                }
            ],
            payload["amount"],
            ship_to_party_id=payload["party_id"],
            document_date=core._company_day(session, tenant, ordered_at).isoformat(),
            ordered_at=ordered_at,
            requested_delivery_at=ordered_at + timedelta(hours=2),
            _commit=False,
        )
        document_id = document.id
        receipt = {
            "source_record_id": source.id,
            "document_id": document.id,
            "document_line_ids": [l.id for l in lines],
            "commitment_ids": [c.id for c in commitments],
        }
    thread_id = (
        f"{run_id}:document:{document_id}"
        if document_id
        else f"{run_id}:mail:{request_id}"
    )
    mail = {
        **payload,
        "submitted": payload,
        "origin": origin,
        "actor_id": actor,
        "receipt": receipt,
        "document_id": document_id,
        "thread_id": thread_id,
        "message_id": f"{run_id}:{request_id}",
        "released_at": release_instant.isoformat(),
        "direction": "incoming",
        "status": "received",
    }
    row = _store(session, tenant, _namespace(run_id), "incoming", request_id, mail)
    return {"source_record_id": row.id, **mail}


def _run_limits(session, tenant, run_id, config, is_order):
    if (
        len(inbox(session, tenant, run_id, limit=config["max_backlog"] + 1))
        >= config["max_backlog"]
    ):
        raise ValueError(
            "Mailbox backlog limit reached; acknowledge processed mail or pause intake"
        )
    if is_order:
        count = session.scalar(
            select(func.count())
            .select_from(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == _namespace(run_id),
                SourceRecord.source_type == "incoming",
                SourceRecord.payload.like('%"kind":"order"%'),
            )
        )
        if count >= config["max_orders"]:
            raise ValueError("Order volume limit reached")


def inbox(
    session, tenant, run_id, *, limit=100, include_acknowledged=False, cursor=None
):
    from sqlalchemy import and_, exists, or_
    from sqlalchemy.orm import aliased

    _run(session, tenant, run_id)
    if not 1 <= limit <= 100001:
        raise ValueError("Invalid inbox page limit")
    query = select(SourceRecord).where(
        SourceRecord.tenant_id == tenant,
        SourceRecord.source_system == _namespace(run_id),
        SourceRecord.source_type == "incoming",
    )
    if not include_acknowledged:
        ack = aliased(SourceRecord)
        query = query.where(
            ~exists().where(
                ack.tenant_id == tenant,
                ack.source_system == _namespace(run_id),
                ack.source_type == "ack",
                ack.external_id == SourceRecord.id,
            )
        )
    if cursor:
        parent, _ = _incoming(session, tenant, run_id, cursor)
        query = query.where(
            or_(
                SourceRecord.received_at > parent.received_at,
                and_(
                    SourceRecord.received_at == parent.received_at,
                    SourceRecord.id > parent.id,
                ),
            )
        )
    return [
        {"source_record_id": r.id, "recorded_at": r.received_at.isoformat(), **_json(r)}
        for r in session.scalars(
            query.order_by(SourceRecord.received_at, SourceRecord.id).limit(limit)
        )
    ]


def _incoming(session, tenant, run_id, message_id):
    _run(session, tenant, run_id)
    row = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.id == message_id,
            SourceRecord.source_system == _namespace(run_id),
            SourceRecord.source_type == "incoming",
        )
    )
    if row is None:
        raise core.NotFound("Incoming message not found")
    return row, _json(row)


def acknowledge(session, tenant, actor, run_id, message_id, *, confirmed=False):
    if confirmed is not True:
        raise ValueError("Acknowledgement confirmation required")
    _owner(session, tenant, actor)
    _incoming(session, tenant, run_id, message_id)
    row = _store(
        session,
        tenant,
        _namespace(run_id),
        "ack",
        message_id,
        {"message_source_id": message_id, "actor_id": actor},
    )
    return {"source_record_id": row.id, "acknowledged": message_id}


def reply(
    session, tenant, actor, run_id, message_id, text, *, request_id, confirmed=False
):
    if confirmed is not True:
        raise ValueError("Exact local reply confirmation required")
    _owner(session, tenant, actor)
    _, parent = _incoming(session, tenant, run_id, message_id)
    if not isinstance(text, str) or not text.strip() or len(text) > 20000:
        raise ValueError("Invalid reply text")
    payload = {
        "body": text,
        "subject": "Re: " + parent["subject"],
        "from": "company@example.invalid",
        "to": parent["from"],
        "party_id": parent["party_id"],
        "document_id": parent["document_id"],
        "thread_id": parent["thread_id"],
        "in_reply_to": parent["message_id"],
        "message_id": f"{run_id}:reply:{request_id}",
        "direction": "outgoing",
        "status": "simulated",
        "transport": "local_simulation",
        "synthetic": True,
        "actor_id": actor,
    }
    row = _store(session, tenant, _namespace(run_id), "outgoing", request_id, payload)
    return {"source_record_id": row.id, **payload}


def tick(session, tenant, run_id, occurrence, at):
    _, config = _run(session, tenant, run_id, lock=True)
    prior = _source(session, tenant, _namespace(run_id), "tick", occurrence)
    if prior:
        return _json(prior)
    if at >= datetime.fromisoformat(config["ends_at"]):
        from reality.db.scheduled_jobs import ScheduledJob

        for schedule in session.scalars(
            select(ScheduledJob).where(
                ScheduledJob.tenant_id == tenant,
                ScheduledJob.job_type.in_(
                    ["simulator.world", "simulator.reactions", "simulator.monitor"]
                ),
            )
        ):
            if (
                schedule.enabled
                and schedule.configuration["arguments"]["run_id"] == run_id
            ):
                scheduled_jobs.control_schedule(
                    session,
                    tenant,
                    config["owner_id"],
                    schedule.id,
                    "pause",
                    schedule.revision,
                    "end:" + occurrence,
                )
        if not _source(session, tenant, _namespace(run_id), "terminal_report", run_id):
            _store(
                session,
                tenant,
                _namespace(run_id),
                "terminal_report",
                run_id,
                monitor(session, tenant, run_id),
            )
        result = {"generated": 0, "ended": True}
    else:
        seed = int(
            hashlib.sha256((config["seed"] + occurrence).encode()).hexdigest()[:12], 16
        )
        party = config["references"]["customer"][
            seed % len(config["references"]["customer"])
        ]
        item = config["items"][seed % len(config["items"])]
        quantity = 1 + seed % 4
        event = {
            "kind": "order",
            "party_id": party["id"],
            "item_id": item["id"],
            "quantity": quantity,
            "amount": str(quantity * 10),
            "unit_price": "10",
            "subject": f"Order for {quantity} {item['name']}",
            "body": f"Please deliver {quantity} {item['name']} to our receiving desk within two hours.",
        }
        try:
            mail = inject(
                session,
                tenant,
                config["owner_id"],
                run_id,
                event,
                request_id=occurrence,
                confirmed=True,
                origin="automatic",
                at=at,
            )
            result = {"generated": 1, "source_record_id": mail["source_record_id"]}
        except ValueError as error:
            if not any(
                reason in str(error) for reason in ["backlog limit", "volume limit"]
            ):
                raise
            from reality.db.scheduled_jobs import ScheduledJob

            schedules = session.scalars(
                select(ScheduledJob).where(
                    ScheduledJob.tenant_id == tenant,
                    ScheduledJob.job_type == "simulator.world",
                )
            )
            for schedule in schedules:
                if (
                    schedule.enabled
                    and schedule.configuration["arguments"]["run_id"] == run_id
                ):
                    scheduled_jobs.control_schedule(
                        session,
                        tenant,
                        config["owner_id"],
                        schedule.id,
                        "pause",
                        schedule.revision,
                        "bound:" + occurrence,
                    )
            result = {"generated": 0, "paused_reason": str(error)}
    _store(session, tenant, _namespace(run_id), "tick", occurrence, result)
    return result


def monitor(session, tenant, run_id):
    """Compare retained source inputs and raw effects, independently of intake receipts."""
    _, config = _run(session, tenant, run_id)
    cutoff = lambda: (
        session.scalar(
            select(func.max(BusinessEvent.sequence)).where(
                BusinessEvent.tenant_id == tenant
            )
        )
        or 0
    )
    from reality.services.business_locks import lock_delivery_state

    lock_delivery_state(session, tenant)
    before = cutoff()
    mismatches = []
    documents = {
        d.id: d
        for d in session.scalars(select(Document).where(Document.tenant_id == tenant))
    }
    by_document = {}
    for line in session.scalars(
        select(DocumentLine).where(DocumentLine.tenant_id == tenant)
    ):
        by_document.setdefault(line.document_id, []).append(line)
    for message in inbox(
        session, tenant, run_id, limit=100000, include_acknowledged=True
    ):
        if message["kind"] != "order":
            continue
        doc = documents.get(message["document_id"])
        lines = by_document.get(message["document_id"], [])
        if (
            doc is None
            or len(lines) != 1
            or lines[0].quantity != Decimal(str(message["quantity"]))
            or doc.gross_amount != Decimal(message["amount"])
        ):
            mismatches.append(
                {
                    "source_record_id": message["source_record_id"],
                    "reason": "Order/source quantity or amount mismatch",
                }
            )
    for item in config["items"]:
        moves = list(
            session.scalars(
                select(Movement).where(
                    Movement.tenant_id == tenant, Movement.item_id == item["id"]
                )
            )
        )
        expected = sum(
            (
                (m.quantity if m.to_location_id else Decimal(0))
                - (m.quantity if m.from_location_id else Decimal(0))
                for m in moves
            ),
            Decimal(0),
        )
        actual = core.stock_at(session, tenant, item["id"])
        if expected != actual:
            mismatches.append(
                {
                    "item_id": item["id"],
                    "expected": str(expected),
                    "actual": str(actual),
                }
            )
    balances = {}
    for entry in session.scalars(
        select(LedgerEntry).where(LedgerEntry.tenant_id == tenant)
    ):
        key = (entry.posting_group_id, entry.currency)
        balances[key] = balances.get(key, Decimal(0)) + (
            entry.amount if entry.debit_credit == "debit" else -entry.amount
        )
    for key, value in balances.items():
        if value:
            mismatches.append({"posting_group": key, "imbalance": str(value)})
    from reality.services.live_company_checks import check_effects, delivery_goals

    mismatches.extend(check_effects(session, tenant))
    after = cutoff()
    stable = before == after
    if not stable:
        mismatches = []
    incoming = inbox(session, tenant, run_id, limit=100000, include_acknowledged=True)
    counts = Counter(m["kind"] for m in incoming)
    terms = core.commitment_terms(session, tenant)
    commitments = list(
        session.scalars(select(Commitment).where(Commitment.tenant_id == tenant))
    )
    observed_now = now()
    open_orders = sum(
        c.type == "customer_delivery"
        and c.status != "cancelled"
        and terms[c.id].open > 0
        for c in commitments
    )
    overdue = sum(
        c.type == "customer_delivery"
        and c.status != "cancelled"
        and terms[c.id].open > 0
        and terms[c.id].due_at is not None
        and terms[c.id].due_at < observed_now
        for c in commitments
    )
    hourly = sum(
        m["kind"] == "order"
        and m["origin"] == "automatic"
        and datetime.fromisoformat(m["recorded_at"])
        >= observed_now - timedelta(hours=1)
        for m in incoming
    )
    return {
        "run_id": run_id,
        "observed_at": now().isoformat(),
        "core_status": ("failed" if mismatches else "passed")
        if stable
        else "deferred_concurrent_change",
        "event_cutoff": after,
        "differences": mismatches,
        "orders": counts["order"],
        "requested_orders_per_hour": config["rate"],
        "generated_and_committed_orders": counts["order"],
        "automatic_orders_last_hour": hourly,
        "open_orders": open_orders,
        "overdue_orders": overdue,
        "messages": len(incoming),
        "manual": sum(m["origin"] == "manual" for m in incoming),
        "replies": len(_rows(session, tenant, run_id, "outgoing")),
        "unread": len(inbox(session, tenant, run_id, limit=100000)),
        "case_families": dict(
            Counter(m.get("case_family", m["kind"]) for m in incoming)
            + Counter(
                "recorded_" + _json(r)["kind"]
                for r in _rows(session, tenant, run_id, "world_effect")
                if "kind" in _json(r)
            )
        ),
        "messages_by_role": dict(
            Counter(
                "supplier"
                if m["party_id"] in {p["id"] for p in config["references"]["supplier"]}
                else "customer"
                for m in incoming
            )
        ),
        "delivery_goals": delivery_goals(session, tenant, incoming, observed_now),
        "worker_liveness": "unknown",
        "operator_liveness": "unknown",
    }


def reactions(session, tenant, run_id, at):
    """External evidence follows actual purchases/dispatch, not fixture policy actions."""
    from reality.services import shipments
    from reality.services.live_company_carrier import observe_carrier

    _, config = _run(session, tenant, run_id, lock=True)
    system = _namespace(run_id)
    start_at = datetime.fromisoformat(config["started_at"])
    if at >= datetime.fromisoformat(config["ends_at"]):
        return {"messages": 0, "receipts": 0, "arrivals": 0, "payments": 0}
    counts = {"messages": 0, "receipts": 0, "arrivals": 0, "payments": 0}
    counts["arrivals"] = observe_carrier(session, tenant, run_id, start_at, at)
    # Reserve a bounded batch of mailbox slots before recording due evidence.
    # Backpressure waits for the operator; it is not a failed business booking.
    unread = len(inbox(session, tenant, run_id, limit=config["max_backlog"] + 1))
    if unread > max(0, config["max_backlog"] - 200):
        return counts
    supplier_ids = [p["id"] for p in config["references"]["supplier"]]
    from sqlalchemy import exists

    pending_purchase = exists().where(
        Commitment.tenant_id == tenant,
        Commitment.document_id == Document.id,
        ~exists().where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.source_system == system,
            SourceRecord.source_type == "world_effect",
            SourceRecord.external_id == "receipt-done:" + Commitment.id,
        ),
    )
    purchases = list(
        session.execute(
            select(Document, SourceRecord)
            .join(
                SourceRecord,
                (SourceRecord.tenant_id == Document.tenant_id)
                & (SourceRecord.id == Document.source_record_id),
            )
            .where(
                Document.tenant_id == tenant,
                Document.type == "purchase_order",
                Document.party_id.in_(supplier_ids),
                SourceRecord.received_at >= start_at,
                pending_purchase,
            )
            .limit(20)
        )
    )
    for purchase, purchase_source in purchases:
        commitments = list(
            session.scalars(
                select(Commitment).where(
                    Commitment.tenant_id == tenant,
                    Commitment.document_id == purchase.id,
                )
            )
        )
        requested_items = ", ".join(
            f"{c.quantity} {next((i['name'] for i in config['items'] if i['id'] == c.item_id), c.item_id)}"
            for c in commitments
        )
        age = (at - purchase_source.received_at).total_seconds()
        delayed = int(hashlib.sha256(purchase.id.encode()).hexdigest()[:8], 16) % 4 == 0
        if (
            delayed
            and age >= 60
            and not _source(
                session, tenant, system, "incoming", "supplier-delay:" + purchase.id
            )
        ):
            inject(
                session,
                tenant,
                config["owner_id"],
                run_id,
                {
                    "kind": "supplier_delay",
                    "party_id": purchase.party_id,
                    "document_id": purchase.id,
                    "subject": "Supplier delivery delayed",
                    "body": f"Hello, purchase {purchase.number} has a picking delay. Both deliveries will arrive two minutes later than confirmed. Can you accept this revised timing, or do you need us to prioritize a smaller first delivery? Please reply with the quantity you need first.",
                    "case_family": "supplier_delay_acknowledgement",
                },
                request_id="supplier-delay:" + purchase.id,
                confirmed=True,
                origin="automatic",
                at=at,
            )
            counts["messages"] += 1
        if age >= 30:
            event = {
                "kind": "supplier_email",
                "party_id": purchase.party_id,
                "document_id": purchase.id,
                "subject": "Purchase confirmed",
                "body": f"Hello, we confirm purchase {purchase.number}: {requested_items}, for {purchase.gross_amount} {purchase.currency}. The first part is due five minutes after receipt of your purchase, the remainder after ten minutes. Can your warehouse accept a split delivery? Please confirm your receiving arrangements.",
                "case_family": "supplier_partial_delivery_confirmation",
            }
            if not _source(
                session, tenant, system, "incoming", "supplier-confirm:" + purchase.id
            ):
                inject(
                    session,
                    tenant,
                    config["owner_id"],
                    run_id,
                    event,
                    request_id="supplier-confirm:" + purchase.id,
                    confirmed=True,
                    origin="automatic",
                    at=at,
                )
                counts["messages"] += 1
        clarification_key = "supplier-clarification:" + purchase.id
        if age >= 120 and not _source(
            session, tenant, system, "incoming", clarification_key
        ):
            from reality.services.live_company_mail import case_variant

            variant = case_variant(purchase.id) % 3
            questions = [
                (
                    "Receiving hours for your purchase",
                    "supplier_receiving_hours_query",
                    "What are your goods-receiving hours, who should our driver contact and is there a loading-bay restriction? Please confirm before we arrange the vehicle.",
                ),
                (
                    "Which items should we prioritize?",
                    "supplier_priority_quantity_query",
                    "If you need a smaller first delivery, which quantities do you need first? Please confirm your preferred split and whether you accept separate parcels; we will not change the agreed quantities based on this enquiry.",
                ),
                (
                    "Packaging instructions for your purchase",
                    "supplier_packaging_query",
                    "Do you need the goods packed separately by item or together? Are there special labels or fragile-handling instructions? Please confirm; any extra service would need a separate quote and approval.",
                ),
            ]
            subject, family, question = questions[variant]
            inject(
                session,
                tenant,
                config["owner_id"],
                run_id,
                {
                    "kind": "supplier_email",
                    "party_id": purchase.party_id,
                    "document_id": purchase.id,
                    "subject": f"{subject} {purchase.number}",
                    "body": f"Hello, regarding purchase {purchase.number}: {requested_items}. {question}",
                    "case_family": family,
                },
                request_id=clarification_key,
                confirmed=True,
                origin="automatic",
                at=at,
            )
            counts["messages"] += 1
        for commitment in commitments:
            if (
                core.open_quantity(session, tenant, commitment.id) == 0
                or commitment.status == "cancelled"
            ):
                _store(
                    session,
                    tenant,
                    system,
                    "world_effect",
                    "receipt-done:" + commitment.id,
                    {
                        "kind": "supplier_obligation_closed",
                        "commitment_id": commitment.id,
                    },
                )
                continue
            for part, seconds in [(1, 300), (2, 600)]:
                key = f"receipt:{commitment.id}:{part}"
                if age < seconds + (120 if delayed else 0) or _source(
                    session, tenant, system, "world_effect", key
                ):
                    continue
                quantity = commitment.quantity / 2
                remaining = core.open_quantity(session, tenant, commitment.id)
                if commitment.status == "cancelled" or remaining < quantity:
                    continue
                source = _store(
                    session,
                    tenant,
                    system,
                    "physical_receipt",
                    key,
                    {
                        "commitment_id": commitment.id,
                        "quantity": str(quantity),
                        "part": part,
                    },
                )
                receipt = shipments.record_packaged_execution(
                    session,
                    tenant,
                    direction="inbound",
                    purpose="supplier_delivery",
                    counterparty_id=purchase.party_id,
                    source_record_id=source.id,
                    occurred_at=at,
                    movements=[
                        {
                            "commitment_id": commitment.id,
                            "item_id": commitment.item_id,
                            "quantity": str(quantity),
                            "to_location_id": commitment.location_id
                            or config["location_id"],
                        }
                    ],
                    commit=False,
                )
                _store(
                    session,
                    tenant,
                    system,
                    "world_effect",
                    key,
                    {"kind": "supplier_receipt", "receipt": receipt},
                )
                event = {
                    "kind": "supplier_email",
                    "party_id": purchase.party_id,
                    "document_id": purchase.id,
                    "subject": "Partial delivery received",
                    "body": f"Delivery {part}: {quantity} pieces have been received by your warehouse.",
                }
                inject(
                    session,
                    tenant,
                    config["owner_id"],
                    run_id,
                    event,
                    request_id=key + ":mail",
                    confirmed=True,
                    origin="automatic",
                    at=at,
                )
                counts["receipts"] += 1
    from sqlalchemy.orm import aliased

    from reality.services.live_company_mail import customer_conversations

    counts["messages"] += customer_conversations(session, tenant, run_id, config, at)
    customer_ids = [p["id"] for p in config["references"]["customer"]]
    done_payment = aliased(SourceRecord)
    invoices = list(
        session.execute(
            select(Document, SourceRecord)
            .join(
                SourceRecord,
                (SourceRecord.tenant_id == Document.tenant_id)
                & (SourceRecord.id == Document.source_record_id),
            )
            .where(
                Document.tenant_id == tenant,
                Document.type == "sales_invoice",
                ~exists().where(
                    done_payment.tenant_id == tenant,
                    done_payment.source_system == system,
                    done_payment.source_type == "world_effect",
                    done_payment.external_id == "payment-done:" + Document.id,
                ),
                Document.party_id.in_(customer_ids),
                SourceRecord.received_at >= start_at,
                SourceRecord.received_at <= at - timedelta(minutes=2),
            )
            .limit(30)
        )
    )
    for invoice, invoice_source in invoices:
        if _source(
            session, tenant, system, "world_effect", "payment-done:" + invoice.id
        ):
            continue
        if core.open_invoice_amount(session, tenant, invoice.id) <= 0:
            _store(
                session,
                tenant,
                system,
                "world_effect",
                "payment-done:" + invoice.id,
                {"kind": "invoice_settled", "invoice_id": invoice.id},
            )
            continue
        for part, seconds in [(1, 120), (2, 240)]:
            key = f"payment:{invoice.id}:{part}"
            if (at - invoice_source.received_at).total_seconds() < seconds or _source(
                session, tenant, system, "world_effect", key
            ):
                continue
            total = invoice.gross_amount
            first = (total / 2).quantize(Decimal(".01"))
            amount = first if part == 1 else total - first
            if (
                amount <= 0
                or core.open_invoice_amount(session, tenant, invoice.id) < amount
            ):
                continue
            source = _store(
                session,
                tenant,
                system,
                "bank_receipt",
                key,
                {
                    "invoice_id": invoice.id,
                    "party_id": invoice.party_id,
                    "amount": str(amount),
                    "currency": invoice.currency,
                    "synthetic": True,
                },
            )
            entries = core.post_customer_payment(
                session,
                tenant,
                invoice.id,
                amount,
                payment_number="LIVE-"
                + hashlib.sha256((run_id + key).encode()).hexdigest()[:16],
                source_record_id=source.id,
                effective_at=at,
                _commit=False,
            )
            _store(
                session,
                tenant,
                system,
                "world_effect",
                key,
                {
                    "kind": "customer_payment",
                    "invoice_id": invoice.id,
                    "amount": str(amount),
                    "ledger_entry_ids": [e.id for e in entries],
                },
            )
            counts["payments"] += 1
    return counts


def save_monitor(session, tenant, run_id, occurrence, at):
    _run(session, tenant, run_id)
    prior = _source(session, tenant, _namespace(run_id), "checkpoint", occurrence)
    if prior:
        return _json(prior)
    report = monitor(session, tenant, run_id)
    _store(session, tenant, _namespace(run_id), "checkpoint", occurrence, report)
    _, config = _run(session, tenant, run_id)
    if at >= datetime.fromisoformat(config["ends_at"]):
        # The monitor closes runs even when intake was already paused by backpressure.
        tick(session, tenant, run_id, "terminal:" + occurrence, at)
    elapsed = (at - datetime.fromisoformat(config["started_at"])).total_seconds()
    bucket = int(elapsed // 10800)
    if bucket >= 1 and not _source(
        session, tenant, _namespace(run_id), "three_hour_report", str(bucket)
    ):
        _store(
            session,
            tenant,
            _namespace(run_id),
            "three_hour_report",
            str(bucket),
            report,
        )
        print("SIMULATOR CHECK " + json.dumps(report, default=str), flush=True)
    if report["differences"]:
        from reality.db.scheduled_jobs import ScheduledJob

        for schedule in session.scalars(
            select(ScheduledJob).where(
                ScheduledJob.tenant_id == tenant,
                ScheduledJob.job_type.in_(["simulator.world", "simulator.reactions"]),
            )
        ):
            if (
                schedule.configuration["arguments"]["run_id"] == run_id
                and schedule.enabled
            ):
                scheduled_jobs.control_schedule(
                    session,
                    tenant,
                    config["owner_id"],
                    schedule.id,
                    "pause",
                    schedule.revision,
                    "fault:" + occurrence,
                )
    return report


def live_view(session, tenant, run_id, *, performance_filter=""):
    """Bounded human view; private seed and future reactions never leave the world."""
    from reality.db.core import Commitment

    _, config = _run(session, tenant, run_id)
    recent = lambda kind: list(
        session.scalars(
            select(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == _namespace(run_id),
                SourceRecord.source_type == kind,
            )
            .order_by(SourceRecord.received_at.desc(), SourceRecord.id.desc())
            .limit(300)
        )
    )
    messages = [
        {"source_record_id": r.id, "recorded_at": r.received_at.isoformat(), **_json(r)}
        for kind in ["incoming", "outgoing"]
        for r in recent(kind)
    ]
    messages.sort(key=lambda m: m["recorded_at"])
    orders = []
    terms = core.commitment_terms(session, tenant)
    for doc, line, commitment in session.execute(
        select(Document, DocumentLine, Commitment)
        .join(
            SourceRecord,
            (SourceRecord.tenant_id == Document.tenant_id)
            & (SourceRecord.id == Document.source_record_id),
        )
        .join(
            DocumentLine,
            (DocumentLine.tenant_id == Document.tenant_id)
            & (DocumentLine.document_id == Document.id),
        )
        .join(
            Commitment,
            (Commitment.tenant_id == DocumentLine.tenant_id)
            & (Commitment.document_line_id == DocumentLine.id),
        )
        .where(
            Document.tenant_id == tenant,
            SourceRecord.received_at >= datetime.fromisoformat(config["started_at"]),
            Document.type.in_(["sales_order", "purchase_order"]),
        )
        .order_by(SourceRecord.received_at.desc(), Document.id)
        .limit(100)
    ):
        orders.append(
            {
                "id": doc.id,
                "number": doc.number,
                "party_id": doc.party_id,
                "type": doc.type,
                "source_record_id": doc.source_record_id,
                "document_line_id": line.id,
                "commitment_id": commitment.id,
                "quantity": str(commitment.quantity),
                "fulfilled": str(terms[commitment.id].fulfilled),
                "open": str(
                    terms[commitment.id].open if commitment.status != "cancelled" else 0
                ),
                "amount": str(doc.gross_amount),
                "status": commitment.status,
                "ordered_at": doc.ordered_at.isoformat() if doc.ordered_at else None,
                "due_at": doc.requested_delivery_at.isoformat()
                if doc.requested_delivery_at
                else None,
            }
        )
    checkpoints = recent("checkpoint")
    report = (
        _json(checkpoints[0])
        if checkpoints
        else {"core_status": "unchecked", "observed_at": None}
    )
    ticks = recent("tick")
    from reality.db.scheduled_jobs import ScheduledJob

    schedules = list(
        session.scalars(
            select(ScheduledJob).where(
                ScheduledJob.tenant_id == tenant,
                ScheduledJob.job_type.in_(
                    ["simulator.world", "simulator.reactions", "simulator.monitor"]
                ),
            )
        )
    )
    incoming_count = session.scalar(
        select(func.count())
        .select_from(SourceRecord)
        .where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.source_system == _namespace(run_id),
            SourceRecord.source_type == "incoming",
        )
    )
    order_count = session.scalar(
        select(func.count())
        .select_from(SourceRecord)
        .where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.source_system == _namespace(run_id),
            SourceRecord.source_type == "incoming",
            SourceRecord.payload.like('%"kind":"order"%'),
        )
    )
    outgoing_count = session.scalar(
        select(func.count())
        .select_from(SourceRecord)
        .where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.source_system == _namespace(run_id),
            SourceRecord.source_type == "outgoing",
        )
    )
    from reality.services.live_company_view import enrich

    return enrich(
        session,
        tenant,
        run_id,
        config,
        {
            "run_id": run_id,
            "company_id": tenant,
            "observed_at": now().isoformat(),
            "started_at": config["started_at"],
            "ends_at": config["ends_at"],
            "target_orders_per_hour": config["rate"],
            "orders": orders,
            "messages": messages,
            "message_count": incoming_count,
            "order_count": order_count,
            "reply_count": outgoing_count,
            "parties": [
                {**p, "role": role}
                for role, rows in config["references"].items()
                for p in rows
            ],
            "items": config["items"],
            "stock": [
                {**i, "quantity": str(core.stock_at(session, tenant, i["id"]))}
                for i in config["items"]
            ],
            "checkpoint": report,
            "last_world_tick": ticks[0].received_at.isoformat() if ticks else None,
            "schedules": [
                {"id": s.id, "type": s.job_type, "enabled": s.enabled}
                for s in schedules
                if s.configuration["arguments"]["run_id"] == run_id
            ],
            "view_limit": "Latest 100 order lines and 300 messages per direction; totals count the full run.",
        },
        order_filter=performance_filter,
    )
