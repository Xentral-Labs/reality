"""Optional synthetic source lifecycle using the shared durable scheduler."""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Document,
    ImportJob,
    Item,
    Location,
    Party,
    PaymentTerm,
    PlaygroundRun,
    SourceRecord,
    SourceSystem,
    Tenant,
    now,
    uid,
)
from reality.db.demo_data import DemoDataConnection
from reality.db.scheduled_jobs import ScheduledJob, ScheduledJobRun
from reality.demo.international import (
    DEMO_DATA_CUSTOMERS,
    DEMO_DATA_PAYMENT_TERM,
    ITEMS,
    MINIMAL_ITEMS,
    item_number,
)
from reality.services import core
from reality.services import scheduled_jobs as jobs
from reality.services.tenant_policy import (
    _INTAKE_OPERATIONS,
    _SEED_OPERATIONS,
    _SETTLEMENT_OPERATIONS,
    PlaygroundOperationDenied,
    _bound_profile_scope,
    require_playground_run,
)

RATES = {10: 360, 60: 60, 300: 12}
# Feature 168: the settlement stream. Fixed cadence, bounded batch, bounded scan.
SETTLEMENT_INTERVAL = 60
SETTLEMENT_BATCH = 25  # 300 orders/hour need about 10 records a minute; keep headroom
SETTLEMENT_WINDOW = timedelta(days=30)
SETTLEMENT_RECENT = timedelta(hours=12)
SYNTHETIC_TYPES = ("order", "invoice", "payment")
_DOCUMENT_TYPES = {
    "order": "sales_order",
    "invoice": "sales_invoice",
    "payment": "customer_payment",
}
_CONNECT_OPERATIONS = _SEED_OPERATIONS | frozenset(
    {
        "source_system_create",
        "source_capability_create",
        "store_source_record",
        "create_payment_term",
    }
)


def _digest(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def eligible(session: Session, tenant_id: str, actor_id: str) -> PlaygroundRun:
    run = session.scalar(
        select(PlaygroundRun).where(
            PlaygroundRun.tenant_id == tenant_id,
            PlaygroundRun.owner_user_id == actor_id,
        )
    )
    if run is None:
        raise PlaygroundOperationDenied("Demo Data requires your own Sandbox.")
    run = require_playground_run(session, run.id, actor_id, for_write=True)
    if (
        run.status != "active"
        or run.sandbox_kind != "practice"
        or run.preset_key not in {"company-empty", "international-demo"}
        or (run.preset_key == "company-empty" and run.preset_version != 1)
        or (
            run.preset_key == "international-demo"
            and run.preset_version not in {1, 2, 3, 4, 5, 6, 7}
        )
    ):
        raise PlaygroundOperationDenied(
            "Demo Data requires a ready compatible practice company."
        )
    return run


def _connection(
    session: Session, tenant_id: str, *, lock: bool = False
) -> DemoDataConnection | None:
    query = select(DemoDataConnection).where(DemoDataConnection.tenant_id == tenant_id)
    return session.scalar(
        query.with_for_update().execution_options(populate_existing=True)
        if lock
        else query
    )


def _locked(session: Session, tenant_id: str):
    connection = _connection(session, tenant_id)
    if connection is None:
        raise core.NotFound("Demo Data is not connected.")
    schedule_id = connection.current_schedule_id
    schedule = None
    if schedule_id:
        schedule = session.scalar(
            select(ScheduledJob)
            .where(ScheduledJob.tenant_id == tenant_id, ScheduledJob.id == schedule_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        session.scalar(
            select(ScheduledJobRun)
            .where(
                ScheduledJobRun.tenant_id == tenant_id,
                ScheduledJobRun.schedule_id == schedule_id,
                ScheduledJobRun.status.in_(
                    {"pending", "retry", "running", "unresolved"}
                ),
            )
            .with_for_update()
        )
    connection = _connection(session, tenant_id, lock=True)
    if connection.current_schedule_id != schedule_id:
        raise core.Conflict("Demo Data changed; reload its current state.")
    _settlement_schedule(session, tenant_id, connection, lock=True)
    return connection, schedule


def _settlement_schedule(
    session: Session, tenant_id: str, connection, *, lock: bool = False
) -> ScheduledJob | None:
    if not connection.settlement_schedule_id:
        return None
    query = select(ScheduledJob).where(
        ScheduledJob.tenant_id == tenant_id,
        ScheduledJob.id == connection.settlement_schedule_id,
    )
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    return session.scalar(query)


def preview(session: Session, tenant_id: str, actor_id: str) -> dict:
    eligible(session, tenant_id, actor_id)
    items = list(session.scalars(select(Item).where(Item.tenant_id == tenant_id)))
    parties = list(session.scalars(select(Party).where(Party.tenant_id == tenant_id)))
    locations = list(
        session.scalars(select(Location).where(Location.tenant_id == tenant_id))
    )
    add = {"items": [], "parties": [], "locations": []}
    refs = {"items": {}, "parties": {}, "locations": {}}
    if not items and not parties and not locations:
        if session.scalar(
            select(SourceRecord.id).where(SourceRecord.tenant_id == tenant_id).limit(1)
        ):
            raise core.InvalidOperation(
                "This company is not empty; Demo Data needs compatible references."
            )
        add = {
            "items": [
                {"key": key, "name": name, "unit": unit, "category": category}
                for key, name, unit, category in ITEMS
                if key in MINIMAL_ITEMS
            ],
            "parties": [
                {"key": "company", "name": "Harbor Supply", "role": "company"},
                *(
                    {"key": key, "name": name, "role": "customer"}
                    for key, name in DEMO_DATA_CUSTOMERS
                ),
            ],
            "locations": [{"key": "A", "name": "Rotterdam Warehouse"}],
        }
    else:

        def match(rows, *, required=True, **values):
            matches = [
                row
                for row in rows
                if all(getattr(row, k) == v for k, v in values.items())
            ]
            if not matches and not required:
                return None
            if len(matches) != 1:
                raise core.InvalidOperation(
                    "Existing company references are not compatible with Demo Data."
                )
            row = matches[0]
            source = session.scalar(
                select(SourceRecord).where(
                    SourceRecord.tenant_id == tenant_id,
                    SourceRecord.id == row.source_record_id,
                )
            )
            if not source or source.source_system not in {"demo_profile", "demo_data"}:
                raise core.InvalidOperation(
                    "Demo Data cannot remap existing business references."
                )
            return row.id

        refs["items"] = {
            key: match(items, sku=item_number(key), name=name, unit=unit)
            for key, name, unit, _ in ITEMS
            if key in MINIMAL_ITEMS
        }
        refs["parties"] = {"company": match(parties, name="Harbor Supply")}
        # Pool customers that a profile already seeded are reused; the rest are
        # added, so a populated Sandbox still receives varied demand.
        for key, name in DEMO_DATA_CUSTOMERS:
            party_id = match(parties, name=name, required=False)
            if party_id is None:
                add["parties"].append({"key": key, "name": name, "role": "customer"})
            else:
                refs["parties"][key] = party_id
        refs["locations"] = {"A": match(locations, name="Rotterdam Warehouse")}
    # The invoices' payment term is a prerequisite in every company: matched by
    # code when present, added otherwise (feature 168).
    term = session.scalar(
        select(PaymentTerm).where(
            PaymentTerm.tenant_id == tenant_id,
            PaymentTerm.code == DEMO_DATA_PAYMENT_TERM["code"],
        )
    )
    add["payment_terms"] = [] if term else [dict(DEMO_DATA_PAYMENT_TERM)]
    refs["payment_terms"] = {term.code: term.id} if term else {}
    body = {
        "tenant_id": tenant_id,
        "profile_version": 1,
        "add": add,
        "references": refs,
    }
    return {**body, "fingerprint": _digest(body)}


def _atomic_control(operation):
    @wraps(operation)
    def wrapped(session, *args, **kwargs):
        commit = kwargs.pop("_commit", True)
        with session.begin_nested():
            result = operation(session, *args, **kwargs)
        if commit:
            session.commit()
        return result

    return wrapped


def _materialize(session: Session, run: PlaygroundRun, actor_id: str, proposed: dict):
    """Create the previewed missing references; the intake itself never may."""
    tenant_id = run.tenant_id
    with _bound_profile_scope(session, run, actor_id, _CONNECT_OPERATIONS):
        for row in proposed["add"]["parties"]:
            core.create_party(
                session,
                tenant_id,
                row["name"],
                row["role"],
                source_system="demo_data",
                external_id=f"master:{row['key']}",
                source_payload={**row, "synthetic": True},
                _commit=False,
            )
        for row in proposed["add"]["locations"]:
            core.create_location(
                session,
                tenant_id,
                row["name"],
                source_system="demo_data",
                external_id=f"master:{row['key']}",
                source_payload={**row, "synthetic": True},
                _commit=False,
            )
        for row in proposed["add"]["items"]:
            core.create_item(
                session,
                tenant_id,
                item_number(row["key"]),
                row["name"],
                row["unit"],
                source_system="demo_data",
                external_id=f"master:{row['key']}",
                source_payload={**row, "synthetic": True},
                _commit=False,
            )
        for row in proposed["add"].get("payment_terms", []):
            core.create_payment_term(
                session,
                tenant_id,
                row["code"],
                row["name"],
                row["due_days"],
                source_system="demo_data",
                external_id=f"master:term:{row['code']}",
                source_payload={**row, "synthetic": True},
                discount_percent=row["discount_percent"],
                discount_days=row["discount_days"],
                _commit=False,
            )


@_atomic_control
def connect(
    session: Session,
    tenant_id: str,
    actor_id: str,
    request_key: str,
    preview_fingerprint: str,
    *,
    confirmed: bool = False,
) -> dict:
    if not confirmed:
        raise core.InvalidOperation("Confirm the exact Demo Data prerequisites first.")
    jobs._key(request_key)
    run = eligible(session, tenant_id, actor_id)
    existing = _connection(session, tenant_id)
    if existing:
        if (
            existing.last_request_key == request_key
            and existing.last_request_fingerprint
            == _digest({"connect": preview_fingerprint})
        ):
            return status(session, tenant_id, actor_id)
        raise core.Conflict("Demo Data is already connected; use its controls.")
    session.scalar(select(Tenant).where(Tenant.id == tenant_id).with_for_update())
    if _connection(session, tenant_id):
        raise core.Conflict("Demo Data was connected concurrently; reload its status.")
    proposed = preview(session, tenant_id, actor_id)
    if proposed["fingerprint"] != preview_fingerprint:
        raise core.Conflict("Demo Data prerequisites changed; review the new preview.")
    _materialize(session, run, actor_id, proposed)
    with _bound_profile_scope(session, run, actor_id, _CONNECT_OPERATIONS):
        source = core.create_source_system(
            session,
            tenant_id,
            "demo_data",
            "Demo Data",
            "Synthetic incoming orders, invoices and customer payments. "
            "No external provider or credentials.",
            _commit=False,
        )
        for source_type, target in _DOCUMENT_TYPES.items():
            core.create_source_capability(
                session, tenant_id, source.id, source_type, target, _commit=False
            )
    connection = DemoDataConnection(
        id=uid("ddc"),
        tenant_id=tenant_id,
        source_system_id=source.id,
        state="stopped",
        revision=1,
        last_request_key=request_key,
        last_request_fingerprint=_digest({"connect": preview_fingerprint}),
    )
    session.add(connection)
    session.flush()
    return status(session, tenant_id, actor_id)


@_atomic_control
def control(
    session: Session,
    tenant_id: str,
    actor_id: str,
    action: str,
    expected_revision: int,
    request_key: str,
    *,
    confirmed: bool = False,
    rate: int | None = None,
) -> dict:
    if not confirmed:
        raise core.InvalidOperation("Confirm this Demo Data change first.")
    jobs._key(request_key)
    run = eligible(session, tenant_id, actor_id)
    if action not in {
        "start",
        "pause",
        "resume",
        "stop",
        "disconnect",
        "reconnect",
        "set_rate",
    } or (rate is not None and rate not in RATES):
        raise core.InvalidOperation("Unsupported Demo Data control or rate.")
    connection, schedule = _locked(session, tenant_id)
    fingerprint = _digest(
        {"action": action, "revision": expected_revision, "rate": rate}
    )
    if connection.last_request_key == request_key:
        if connection.last_request_fingerprint != fingerprint:
            raise core.Conflict("Request key belongs to different controls.")
        return status(session, tenant_id, actor_id)
    if connection.revision != expected_revision:
        raise core.Conflict("Demo Data changed; reload its current state.")
    allowed = {
        "start": {"stopped"},
        "pause": {"running"},
        "resume": {"paused"},
        "stop": {"running", "paused"},
        "disconnect": {"stopped", "running", "paused"},
        "reconnect": {"disconnected"},
        "set_rate": {"stopped", "running", "paused"},
    }
    if connection.state not in allowed[action]:
        raise core.Conflict("Control is unavailable in the current state.")
    selected_rate = rate or (
        schedule.configuration["arguments"]["rate"] if schedule else 60
    )
    settlement = _settlement_schedule(session, tenant_id, connection)
    settlement_key = f"settle:{request_key}"[:128]
    if action in {"pause", "stop", "disconnect", "set_rate"} and schedule:
        jobs.cancel_queued_run(
            session, tenant_id, actor_id, schedule.id, schedule.revision, request_key
        )
    if action in {"pause", "stop", "disconnect"} and settlement:
        jobs.cancel_queued_run(
            session,
            tenant_id,
            actor_id,
            settlement.id,
            settlement.revision,
            settlement_key,
        )
    if action == "start" or (action == "set_rate" and schedule is None):
        # A new run captures every pool customer, adding those that a connection
        # made before the pool grew does not have yet.
        _materialize(session, run, actor_id, preview(session, tenant_id, actor_id))
        config = {
            "connection_id": connection.id,
            "profile_version": 1,
            "seed": uuid4().hex,
            "rate": selected_rate,
            "references": preview(session, tenant_id, actor_id)["references"],
        }
        schedule = jobs.create_schedule(
            session,
            tenant_id,
            actor_id,
            "demo.generate_orders",
            config,
            request_id=request_key,
            interval_seconds=RATES[selected_rate],
            initial_offsets_seconds=(0, 12, 24) if action == "start" else (),
        )
        connection.current_schedule_id = schedule.id
        session.flush()
    if action == "start":
        # Every start mints a new settlement schedule beside the order schedule;
        # it recomputes each order's plan from the order schedule's own seed.
        settlement = jobs.create_schedule(
            session,
            tenant_id,
            actor_id,
            "demo.settle_orders",
            {
                "connection_id": connection.id,
                "profile_version": 1,
                "references": config["references"],
            },
            request_id=settlement_key,
            interval_seconds=SETTLEMENT_INTERVAL,
        )
        connection.settlement_schedule_id = settlement.id
        session.flush()
    elif action == "set_rate":
        jobs.control_schedule(
            session,
            tenant_id,
            actor_id,
            schedule.id,
            "update",
            schedule.revision,
            f"rate:{request_key}"[:128],
            {
                "config": {
                    **schedule.configuration["arguments"],
                    "rate": selected_rate,
                },
                "interval_seconds": RATES[selected_rate],
            },
        )
    if action in {"start", "resume"} or (
        action == "set_rate" and connection.state == "running"
    ):
        pressure = _counts(session, tenant_id, source_types=SYNTHETIC_TYPES)
        if pressure["pending"] + pressure["failed"] >= 20:
            raise core.Conflict(
                "Resolve pending or failed demo imports before resuming."
            )
        jobs.control_schedule(
            session,
            tenant_id,
            actor_id,
            schedule.id,
            "resume",
            schedule.revision,
            f"resume:{request_key}"[:128],
        )
        if settlement and action != "set_rate":
            jobs.control_schedule(
                session,
                tenant_id,
                actor_id,
                settlement.id,
                "resume",
                settlement.revision,
                f"resume:{settlement_key}"[:128],
            )
    if action != "set_rate":
        connection.state = {
            "start": "running",
            "resume": "running",
            "pause": "paused",
            "stop": "stopped",
            "disconnect": "disconnected",
            "reconnect": "stopped",
        }[action]
    source = session.scalar(
        select(SourceSystem).where(
            SourceSystem.tenant_id == tenant_id,
            SourceSystem.id == connection.source_system_id,
        )
    )
    source.is_active = connection.state != "disconnected"
    connection.revision += 1
    connection.updated_at = now()
    connection.last_request_key, connection.last_request_fingerprint = (
        request_key,
        fingerprint,
    )
    session.flush()
    return status(session, tenant_id, actor_id)


def _imports(
    session: Session, tenant_id: str, *, source_types: tuple[str, ...] = ("order",)
):
    """Synthetic imports of this connection; identities start with an order schedule id.

    Invoice and payment identities extend their order's identity, so the same
    join attributes them to the connection through the order schedule.
    """
    return (
        select(ImportJob)
        .join(
            SourceRecord,
            (SourceRecord.id == ImportJob.source_record_id)
            & (SourceRecord.tenant_id == ImportJob.tenant_id),
        )
        .join(
            ScheduledJob,
            (ScheduledJob.tenant_id == SourceRecord.tenant_id)
            & SourceRecord.external_id.like(ScheduledJob.id + ":%"),
        )
        .join(
            DemoDataConnection,
            (DemoDataConnection.tenant_id == ScheduledJob.tenant_id)
            & (
                ScheduledJob.configuration["arguments"]["connection_id"].astext
                == DemoDataConnection.id
            ),
        )
        .where(
            ImportJob.tenant_id == tenant_id,
            SourceRecord.tenant_id == tenant_id,
            ScheduledJob.tenant_id == tenant_id,
            DemoDataConnection.tenant_id == tenant_id,
            ScheduledJob.job_type == "demo.generate_orders",
            SourceRecord.source_system == "demo_data",
            SourceRecord.source_type.in_(source_types),
        )
    )


def _import_classification(tenant_id: str, source_types: tuple[str, ...] = ("order",)):
    from sqlalchemy import and_, case, exists

    from reality.db.core import InterpretationOutcome

    interpreted = exists(
        select(InterpretationOutcome.id).where(
            InterpretationOutcome.tenant_id == tenant_id,
            InterpretationOutcome.import_job_id == ImportJob.id,
            InterpretationOutcome.classification == "interpreted",
        )
    )
    documented = exists(
        select(Document.id).where(
            Document.tenant_id == tenant_id,
            Document.source_record_id == ImportJob.source_record_id,
            Document.type.in_([_DOCUMENT_TYPES[kind] for kind in source_types]),
        )
    )
    return case(
        (and_(ImportJob.status == "completed", interpreted, documented), "imported"),
        (ImportJob.status == "failed", "failed"),
        else_="pending",
    )


def _counts(
    session: Session, tenant_id: str, *, source_types: tuple[str, ...] = ("order",)
) -> dict:
    classification = _import_classification(tenant_id, source_types)
    rows = session.execute(
        _imports(session, tenant_id, source_types=source_types)
        .with_only_columns(classification, func.count())
        .group_by(classification)
    ).all()
    values = dict(rows)
    return {
        "generated": sum(values.values()),
        "imported": values.get("imported", 0),
        "failed": values.get("failed", 0),
        "pending": values.get("pending", 0),
    }


def status(session: Session, tenant_id: str, actor_id: str) -> dict:
    eligible(session, tenant_id, actor_id)
    connection = _connection(session, tenant_id)
    if not connection:
        return {
            "state": "not_connected",
            "revision": 0,
            "rate": 60,
            "next_arrival": None,
            **_counts(session, tenant_id),
        }
    schedule = (
        session.scalar(
            select(ScheduledJob).where(
                ScheduledJob.tenant_id == tenant_id,
                ScheduledJob.id == connection.current_schedule_id,
            )
        )
        if connection.current_schedule_id
        else None
    )
    counts = _counts(session, tenant_id)
    last_success = session.scalar(
        _imports(session, tenant_id)
        .with_only_columns(func.max(ImportJob.completed_at))
        .where(_import_classification(tenant_id) == "imported")
    )
    latest = (
        session.scalar(
            select(ScheduledJobRun)
            .where(
                ScheduledJobRun.tenant_id == tenant_id,
                ScheduledJobRun.schedule_id == connection.current_schedule_id,
            )
            .order_by(ScheduledJobRun.created_at.desc())
        )
        if schedule
        else None
    )
    pressure = _counts(session, tenant_id, source_types=SYNTHETIC_TYPES)
    derived = (
        "throttled"
        if pressure["pending"] + pressure["failed"] >= 20
        else (
            "error"
            if latest and latest.status in {"failed", "unresolved"}
            else connection.state
        )
    )
    return {
        "id": connection.id,
        "state": connection.state,
        "derived_state": derived,
        "last_success": last_success,
        "scheduler_error": latest.last_error_code if latest else None,
        "revision": connection.revision,
        "rate": schedule.configuration["arguments"]["rate"] if schedule else 60,
        "schedule_id": connection.current_schedule_id,
        "next_arrival": schedule.next_run_at if schedule and schedule.enabled else None,
        "last_request_key": connection.last_request_key,
        "settlement_schedule_id": connection.settlement_schedule_id,
        "order_to_cash": order_to_cash(session, tenant_id, connection),
        **counts,
    }


def order_to_cash(session: Session, tenant_id: str, connection) -> dict:
    """Observations over synthetic invoices and payments; nothing here is stored."""
    settlement = _settlement_schedule(session, tenant_id, connection)
    invoice_jobs = _counts(session, tenant_id, source_types=("invoice",))
    payment_jobs = _counts(session, tenant_id, source_types=("payment",))
    synthetic_documents = {
        kind: set(
            session.scalars(
                select(Document.id)
                .join(
                    SourceRecord,
                    (SourceRecord.id == Document.source_record_id)
                    & (SourceRecord.tenant_id == Document.tenant_id),
                )
                .where(
                    Document.tenant_id == tenant_id,
                    Document.type == _DOCUMENT_TYPES[kind],
                    SourceRecord.source_system == "demo_data",
                    SourceRecord.source_type == kind,
                )
            )
        )
        for kind in ("invoice", "payment")
    }
    open_items = [
        row
        for row in core.financial_open_items(session, tenant_id)
        if row["document"].id in synthetic_documents["invoice"]
    ]
    payments = [
        row
        for row in core.payment_rows(session, tenant_id)
        if row["document"] is not None
        and row["document"].id in synthetic_documents["payment"]
    ]
    last = session.scalar(
        _imports(session, tenant_id, source_types=("invoice", "payment"))
        .with_only_columns(func.max(ImportJob.completed_at))
        .where(_import_classification(tenant_id, ("invoice", "payment")) == "imported")
    )
    return {
        "invoices_issued": invoice_jobs["imported"],
        "payments_received": payment_jobs["imported"],
        "payments_allocated": sum(1 for row in payments if row["allocated"] > 0),
        "invoices_settled": sum(1 for row in open_items if row["status"] == "paid"),
        "open_residuals": sum(1 for row in open_items if row["status"] == "partial"),
        "credit_created": str(
            sum((row["unallocated"] for row in payments), Decimal(0))
        ),
        "unmatched_payments": sum(
            1 for row in payments if row["allocated"] == 0 and row["unallocated"] > 0
        ),
        "failed": invoice_jobs["failed"] + payment_jobs["failed"],
        "last_settlement": last,
        "next_settlement": (
            settlement.next_run_at if settlement and settlement.enabled else None
        ),
    }


@contextmanager
def intake_scope(
    session: Session, tenant_id: str, actor_id: str, *, settlement: bool = False
):
    """Bound authority for one synthetic delivery; `settlement` admits posting money."""
    run = eligible(session, tenant_id, actor_id)
    connection = _connection(session, tenant_id)
    source = (
        session.scalar(
            select(SourceSystem).where(
                SourceSystem.tenant_id == tenant_id,
                SourceSystem.id == connection.source_system_id,
            )
        )
        if connection
        else None
    )
    if (
        not connection
        or connection.state == "disconnected"
        or not source
        or not source.is_active
    ):
        raise PlaygroundOperationDenied("Demo Data source is inactive.")
    with _bound_profile_scope(
        session,
        run,
        actor_id,
        _SETTLEMENT_OPERATIONS if settlement else _INTAKE_OPERATIONS,
    ):
        yield


def settlement_scope(session: Session, tenant_id: str, actor_id: str):
    return intake_scope(session, tenant_id, actor_id, settlement=True)


def imports(
    session: Session,
    tenant_id: str,
    actor_id: str,
    *,
    cursor: str = "",
    limit: int = 25,
    recent: bool = False,
) -> dict:
    import base64

    eligible(session, tenant_id, actor_id)
    connection = _connection(session, tenant_id)
    if connection is None:
        raise core.NotFound("Demo Data is not connected.")
    if not 1 <= limit <= 100:
        raise core.InvalidOperation("Page size must be between 1 and 100.")
    if recent and cursor:
        raise core.InvalidOperation("Recent activity does not accept a history cursor.")
    after = ""
    if len(cursor) > 2048:
        raise core.InvalidOperation("Invalid Demo Data cursor.")
    if cursor:
        try:
            scope, after = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if scope != f"{tenant_id}:{connection.id}" or not isinstance(after, str):
                raise ValueError()
        except (ValueError, TypeError, UnicodeError):
            raise core.InvalidOperation("Invalid Demo Data cursor.") from None
    rows = list(
        session.scalars(
            _imports(session, tenant_id)
            .where(ImportJob.id > after)
            .order_by(
                *(
                    (ImportJob.created_at.desc(), ImportJob.id.desc())
                    if recent
                    else (ImportJob.id,)
                )
            )
            .limit(limit + 1)
        )
    )
    from reality.db.core import Document, InterpretationOutcome

    entries = []
    for row in rows[:limit]:
        outcome = session.scalar(
            select(InterpretationOutcome)
            .where(
                InterpretationOutcome.tenant_id == tenant_id,
                InterpretationOutcome.import_job_id == row.id,
            )
            .order_by(InterpretationOutcome.attempt.desc())
        )
        document = session.scalar(
            select(Document).where(
                Document.tenant_id == tenant_id,
                Document.source_record_id == row.source_record_id,
            )
        )
        entries.append(
            {
                "id": row.id,
                "source_record_id": row.source_record_id,
                "status": row.status,
                "outcome_id": outcome.id if outcome else None,
                "document_id": document.id if document else None,
                "document_number": document.number if document else None,
                "created_at": row.created_at,
                "completed_at": row.completed_at,
            }
        )
    next_cursor = (
        base64.urlsafe_b64encode(
            json.dumps([f"{tenant_id}:{connection.id}", rows[limit - 1].id]).encode()
        ).decode()
        if len(rows) > limit and not recent
        else None
    )
    return {"items": entries, "next_cursor": next_cursor, "has_more": len(rows) > limit}


@_atomic_control
def retry_import(
    session: Session,
    tenant_id: str,
    actor_id: str,
    import_id: str,
    *,
    confirmed: bool = False,
) -> dict:
    if not confirmed:
        raise core.InvalidOperation("Confirm retrying this import first.")
    eligible(session, tenant_id, actor_id)
    _locked(session, tenant_id)
    job = session.scalar(
        _imports(session, tenant_id, source_types=SYNTHETIC_TYPES).where(
            ImportJob.id == import_id
        )
    )
    if job is None:
        raise core.NotFound("Demo import not found.")
    source = session.get(
        SourceRecord, {"tenant_id": job.tenant_id, "id": job.source_record_id}
    )
    with intake_scope(
        session, tenant_id, actor_id, settlement=source.source_type != "order"
    ):
        core.process_import_job_bound(session, tenant_id, job.id)
    return {"id": job.id, "status": job.status}


def read_import(
    session: Session, tenant_id: str, actor_id: str, import_id: str
) -> dict:
    """Read one connection-owned immutable input and its interpretation evidence."""
    from reality.db.core import Document, InterpretationOutcome

    eligible(session, tenant_id, actor_id)
    job = session.scalar(_imports(session, tenant_id).where(ImportJob.id == import_id))
    if job is None:
        raise core.NotFound("Demo import not found.")
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id, SourceRecord.id == job.source_record_id
        )
    )
    outcomes = list(
        session.scalars(
            select(InterpretationOutcome)
            .where(
                InterpretationOutcome.tenant_id == tenant_id,
                InterpretationOutcome.import_job_id == job.id,
            )
            .order_by(InterpretationOutcome.attempt.desc())
            .limit(100)
        )
    )
    document = session.scalar(
        select(Document.id).where(
            Document.tenant_id == tenant_id, Document.source_record_id == source.id
        )
    )
    return {
        "id": job.id,
        "status": job.status,
        "source_record_id": source.id,
        "external_id": source.external_id,
        "received_at": source.received_at,
        "payload": json.loads(source.payload),
        "document_id": document,
        "outcomes": [
            {
                "id": row.id,
                "classification": row.classification,
                "attempt": row.attempt,
                "summary": row.summary,
            }
            for row in outcomes
        ],
    }


def settlement_work(
    session: Session, tenant_id: str, at: datetime, *, limit: int = SETTLEMENT_BATCH
) -> list[dict]:
    """Invoices and payments due at `at` for this connection's recent orders.

    Every order's story is recomputed from its order schedule's seed; the
    existence of a SourceRecord is the only idempotency marker. Only orders
    that can still owe a record are loaded: without an invoice, with an
    invoice but without a first payment, or received within the last hours so
    a second payment may still follow. Oldest due first, at most `limit`.
    """
    from sqlalchemy import exists, or_
    from sqlalchemy.orm import aliased

    from reality.integrations import demo_data as synthetic

    invoice_record = aliased(SourceRecord)
    first_payment = aliased(SourceRecord)
    documented = exists(
        select(Document.id).where(
            Document.tenant_id == tenant_id,
            Document.source_record_id == SourceRecord.id,
            Document.type == "sales_order",
        )
    )
    rows = session.execute(
        select(
            SourceRecord,
            ScheduledJob.id,
            ScheduledJob.configuration["arguments"]["seed"].astext,
        )
        .join(
            ScheduledJob,
            (ScheduledJob.tenant_id == SourceRecord.tenant_id)
            & SourceRecord.external_id.like(ScheduledJob.id + ":%"),
        )
        .join(
            DemoDataConnection,
            (DemoDataConnection.tenant_id == ScheduledJob.tenant_id)
            & (
                ScheduledJob.configuration["arguments"]["connection_id"].astext
                == DemoDataConnection.id
            ),
        )
        .outerjoin(
            invoice_record,
            (invoice_record.tenant_id == SourceRecord.tenant_id)
            & (invoice_record.source_system == "demo_data")
            & (invoice_record.source_type == "invoice")
            & (invoice_record.external_id == SourceRecord.external_id + ":invoice"),
        )
        .outerjoin(
            first_payment,
            (first_payment.tenant_id == SourceRecord.tenant_id)
            & (first_payment.source_system == "demo_data")
            & (first_payment.source_type == "payment")
            & (first_payment.external_id == SourceRecord.external_id + ":payment:1"),
        )
        .where(
            SourceRecord.tenant_id == tenant_id,
            ScheduledJob.tenant_id == tenant_id,
            DemoDataConnection.tenant_id == tenant_id,
            ScheduledJob.job_type == "demo.generate_orders",
            SourceRecord.source_system == "demo_data",
            SourceRecord.source_type == "order",
            SourceRecord.received_at >= at - SETTLEMENT_WINDOW,
            documented,
            or_(
                invoice_record.id.is_(None),
                first_payment.id.is_(None),
                SourceRecord.received_at >= at - SETTLEMENT_RECENT,
            ),
        )
        .order_by(SourceRecord.received_at, SourceRecord.id)
    ).all()
    if not rows:
        return []
    plans = []
    expected: list[str] = []
    for source, schedule_id, seed in rows:
        order = json.loads(source.payload)
        plan = synthetic.settlement_plan(seed, schedule_id, source.external_id, order)
        plans.append((source, order, plan))
        expected.append(synthetic.invoice_external_id(source.external_id))
        expected += [
            synthetic.payment_external_id(source.external_id, payment.index)
            for payment in plan.payments
        ]
    existing = set(
        session.scalars(
            select(SourceRecord.external_id).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == "demo_data",
                SourceRecord.source_type.in_(("invoice", "payment")),
                SourceRecord.external_id.in_(expected),
            )
        )
    )
    due: list[dict] = []
    for source, order, plan in plans:
        invoice_id = synthetic.invoice_external_id(source.external_id)
        if invoice_id not in existing:
            if plan.invoice_at <= at:
                due.append(
                    {
                        "due_at": plan.invoice_at,
                        "source_type": "invoice",
                        "external_id": invoice_id,
                        "payload": synthetic.produce_invoice(
                            order, source.external_id, plan
                        ),
                    }
                )
            continue
        invoice_payload = synthetic.produce_invoice(order, source.external_id, plan)
        for payment in plan.payments:
            payment_id = synthetic.payment_external_id(
                source.external_id, payment.index
            )
            if payment_id in existing:
                continue
            if payment.at <= at:
                due.append(
                    {
                        "due_at": payment.at,
                        "source_type": "payment",
                        "external_id": payment_id,
                        "payload": synthetic.produce_payment(
                            order, invoice_payload, plan, payment.index
                        ),
                    }
                )
            # Payments stay in order: nothing after the first missing one.
            break
    due.sort(key=lambda item: (item["due_at"], item["external_id"]))
    return due[:limit]
