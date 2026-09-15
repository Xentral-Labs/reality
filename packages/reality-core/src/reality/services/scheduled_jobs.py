"""Shared tenant-scoped scheduling and transactional execution services.

Callers own transactions. Only tenant_catalog may enumerate across tenants; it reads
identity metadata, never job/business rows. Scheduler and worker use separate services.
"""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import and_, event, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from reality.db.core import SecurityAuditEvent, Tenant, now, uid
from reality.db.scheduled_jobs import ScheduledJob, ScheduledJobRun
from reality.jobs.registry import (
    JobContext,
    JobError,
    JobResult,
    get_definition,
    require_company_owner,
)
from reality.scheduling.timing import (
    next_initial_time,
    next_time,
    preview,
    validate_initial_offsets,
    validate_timing,
)

UNFINISHED = ("pending", "running", "retry", "unresolved")
QUEUE_LIMIT = 1000


def _key(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise JobError("invalid_request_id")
    return value


def _fingerprint(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _context(
    tenant_id: str, actor_id: str | None, run: ScheduledJobRun | None = None
) -> JobContext:
    return JobContext(
        tenant_id,
        actor_id,
        run.id if run else "",
        run.scheduled_for if run else None,
        now() + timedelta(seconds=30),
    )


DEMO_JOB_TYPES = frozenset({"demo.generate_orders", "demo.settle_orders"})
SETUP_JOB_TYPE = "company_setup.initialize"


def _owner(
    session: Session, tenant_id: str, actor_id: str, job_type: str | None = None
) -> None:
    if job_type == "projections.refresh":
        raise JobError("not_authorized")
    if job_type in DEMO_JOB_TYPES:
        from reality.services.demo_data import eligible

        eligible(session, tenant_id, actor_id)
        return
    if job_type == SETUP_JOB_TYPE:
        # A verified account pending admission may create a Sandbox, so company
        # setup authorizes by the run's own owner (feature 199).
        from reality.jobs.handlers.company_setup import require_setup_owner

        require_setup_owner(session, tenant_id, actor_id)
        return
    require_company_owner(session, _context(tenant_id, actor_id))


def _tenant_lock(
    session: Session, tenant_id: str, *, skip: bool = False
) -> Tenant | None:
    return session.scalar(
        select(Tenant)
        .where(Tenant.id == tenant_id)
        .with_for_update(skip_locked=skip)
        .execution_options(populate_existing=True)
    )


def _schedule(
    session: Session,
    tenant_id: str,
    schedule_id: str,
    *,
    lock: bool = False,
    skip: bool = False,
) -> ScheduledJob | None:
    statement = select(ScheduledJob).where(
        ScheduledJob.tenant_id == tenant_id, ScheduledJob.id == schedule_id
    )
    if lock:
        statement = statement.with_for_update(skip_locked=skip).execution_options(
            populate_existing=True
        )
    return session.scalar(statement)


def _run(
    session: Session,
    tenant_id: str,
    run_id: str,
    *,
    lock: bool = False,
    skip: bool = False,
) -> ScheduledJobRun | None:
    statement = select(ScheduledJobRun).where(
        ScheduledJobRun.tenant_id == tenant_id, ScheduledJobRun.id == run_id
    )
    if lock:
        statement = statement.with_for_update(skip_locked=skip).execution_options(
            populate_existing=True
        )
    return session.scalar(statement)


def _unfinished(
    session: Session, tenant_id: str, schedule_id: str
) -> ScheduledJobRun | None:
    return session.scalar(
        select(ScheduledJobRun)
        .where(
            ScheduledJobRun.tenant_id == tenant_id,
            ScheduledJobRun.schedule_id == schedule_id,
            ScheduledJobRun.status.in_(UNFINISHED),
        )
        .limit(1)
        .with_for_update()
    )


def _capacity(session: Session, tenant_id: str) -> bool:
    return (
        session.scalar(
            select(func.count())
            .select_from(ScheduledJobRun)
            .where(
                ScheduledJobRun.tenant_id == tenant_id,
                ScheduledJobRun.status.in_(UNFINISHED),
            )
        )
        < QUEUE_LIMIT
    )


def _audit(
    session: Session, tenant_id: str, actor_id: str, subject: str, action: str
) -> None:
    session.add(
        SecurityAuditEvent(
            id=uid("sec"),
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            subject_type="scheduled_job",
            subject_id=subject,
            event_type=f"scheduled_job.{action}",
            outcome="recorded",
            detail="{}",
        )
    )


def _validated(
    session: Session, tenant_id: str, actor_id: str, job_type: str, config: dict
) -> dict:
    definition = get_definition(job_type)
    parsed = definition.validate(config)
    definition.authorize(session, _context(tenant_id, actor_id), parsed)
    return {"version": definition.version, "arguments": parsed.model_dump(mode="json")}


def create_schedule(
    session: Session,
    tenant_id: str,
    actor_id: str,
    job_type: str,
    config: dict,
    *,
    request_id: str,
    interval_seconds: int | None = None,
    cron_expression: str | None = None,
    initial_offsets_seconds: tuple[int, ...] = (),
) -> ScheduledJob:
    _owner(session, tenant_id, actor_id, job_type)
    _key(request_id)
    try:
        validate_timing(
            interval_seconds=interval_seconds, cron_expression=cron_expression
        )
        validate_initial_offsets(initial_offsets_seconds, interval_seconds)
    except ValueError as error:
        raise JobError("invalid_timing") from error
    envelope = _validated(session, tenant_id, actor_id, job_type, config)
    if initial_offsets_seconds:
        envelope["initial_offsets_seconds"] = list(initial_offsets_seconds)
    fingerprint = _fingerprint(
        {
            "actor": actor_id,
            "type": job_type,
            "configuration": envelope,
            "interval": interval_seconds,
            "cron": cron_expression,
        }
    )
    _tenant_lock(session, tenant_id)
    existing = session.scalar(
        select(ScheduledJob).where(
            ScheduledJob.tenant_id == tenant_id,
            ScheduledJob.create_request_id == request_id,
        )
    )
    if existing:
        if existing.create_fingerprint != fingerprint:
            raise JobError("request_conflict")
        return existing
    row = ScheduledJob(
        id=f"sch_{uuid4().hex}",
        tenant_id=tenant_id,
        actor_id=actor_id,
        job_type=job_type,
        configuration=envelope,
        interval_seconds=interval_seconds,
        cron_expression=cron_expression,
        create_request_id=request_id,
        create_fingerprint=fingerprint,
    )
    session.add(row)
    session.flush()
    _audit(session, tenant_id, actor_id, row.id, "created")
    return row


def preview_schedule(
    session: Session, tenant_id: str, actor_id: str, schedule_id: str
) -> list[datetime]:
    _owner(session, tenant_id, actor_id)
    row = _schedule(session, tenant_id, schedule_id)
    if row is None:
        raise JobError("not_found")
    offsets = row.configuration.get("initial_offsets_seconds")
    if offsets:
        at = now()
        anchor = datetime.fromisoformat(
            row.configuration.get("initial_started_at", at.isoformat())
        )
        earliest = max(at, row.next_run_at or at)
        result = [
            anchor + timedelta(seconds=offset)
            for offset in offsets
            if anchor + timedelta(seconds=offset) >= earliest
        ][:5]
        while len(result) < 5:
            following, _ = next_initial_time(
                result[-1] if result else at,
                anchor,
                offsets,
                row.interval_seconds,
            )
            result.append(following)
        return result
    return preview(
        now(),
        interval_seconds=row.interval_seconds,
        cron_expression=row.cron_expression,
    )


def control_schedule(
    session: Session,
    tenant_id: str,
    actor_id: str,
    schedule_id: str,
    action: str,
    expected_revision: int,
    request_id: str,
    changes: dict | None = None,
) -> ScheduledJob:
    _key(request_id)
    changes = changes or {}
    fingerprint = _fingerprint(
        {
            "actor": actor_id,
            "action": action,
            "revision": expected_revision,
            "changes": changes,
        }
    )
    row = _schedule(session, tenant_id, schedule_id, lock=True)
    if row is None:
        raise JobError("not_found")
    _owner(session, tenant_id, actor_id, row.job_type)
    if row.last_control_request_id == request_id:
        if row.last_control_fingerprint != fingerprint:
            raise JobError("request_conflict")
        return row
    if expected_revision != row.revision:
        raise JobError("stale_revision")
    unfinished = _unfinished(session, tenant_id, row.id)
    if action == "pause":
        if changes:
            raise JobError("invalid_control")
        row.enabled = False
        row.configuration = _without_initial_timing(row.configuration)
    elif action == "resume":
        if changes:
            raise JobError("invalid_control")
        if unfinished and unfinished.status == "unresolved":
            raise JobError("unresolved_run")
        _authorize_run_or_schedule(session, row)
        row.enabled = True
        offsets = row.configuration.get("initial_offsets_seconds")
        if offsets and "initial_started_at" not in row.configuration and not unfinished:
            anchor = now()
            row.configuration = {
                **row.configuration,
                "initial_started_at": anchor.isoformat(),
            }
            row.next_run_at = anchor + timedelta(seconds=offsets[0])
        else:
            row.configuration = _without_initial_timing(row.configuration)
            if not unfinished:
                row.next_run_at = next_time(
                    now(),
                    interval_seconds=row.interval_seconds,
                    cron_expression=row.cron_expression,
                )
    elif action == "update":
        if unfinished:
            raise JobError("unfinished_run")
        if set(changes) - {"config", "actor_id", "interval_seconds", "cron_expression"}:
            raise JobError("invalid_control")
        if (
            changes.get("interval_seconds") is not None
            and changes.get("cron_expression") is not None
        ):
            raise JobError("invalid_timing")
        interval = changes.get("interval_seconds", row.interval_seconds)
        cron = changes.get("cron_expression", row.cron_expression)
        if "interval_seconds" in changes and interval is not None:
            cron = None
        if "cron_expression" in changes and cron is not None:
            interval = None
        validate_timing(interval_seconds=interval, cron_expression=cron)
        actor = changes.get("actor_id", row.actor_id)
        _owner(session, tenant_id, actor, row.job_type)
        envelope = _validated(
            session,
            tenant_id,
            actor,
            row.job_type,
            changes.get("config", row.configuration["arguments"]),
        )
        row.actor_id, row.configuration = actor, envelope
        row.interval_seconds, row.cron_expression = interval, cron
        row.next_run_at = (
            next_time(now(), interval_seconds=interval, cron_expression=cron)
            if row.enabled
            else None
        )
    else:
        raise JobError("invalid_control")
    row.revision += 1
    row.updated_at = now()
    row.last_control_request_id, row.last_control_fingerprint = request_id, fingerprint
    _audit(session, tenant_id, actor_id, row.id, action)
    session.flush()
    return row


def _without_initial_timing(configuration: dict) -> dict:
    return {
        key: value
        for key, value in configuration.items()
        if key not in {"initial_offsets_seconds", "initial_started_at"}
    }


def _authorize_run_or_schedule(session: Session, row: ScheduledJob | ScheduledJobRun):
    definition = get_definition(row.job_type)
    envelope = row.configuration
    if envelope.get("version") != definition.version:
        raise JobError("unsupported_job_version")
    parsed = definition.validate(envelope.get("arguments"))
    definition.authorize(
        session,
        _context(
            row.tenant_id,
            row.actor_id,
            row if isinstance(row, ScheduledJobRun) else None,
        ),
        parsed,
    )
    return definition, parsed


def create_manual_run(
    session: Session,
    tenant_id: str,
    actor_id: str,
    job_type: str,
    config: dict,
    *,
    request_id: str,
) -> ScheduledJobRun:
    # The job type decides the ownership rule, exactly as it does for a schedule; a
    # manual run must not be authorized differently from the same job on a timer.
    _owner(session, tenant_id, actor_id, job_type)
    _key(request_id)
    envelope = _validated(session, tenant_id, actor_id, job_type, config)
    fingerprint = _fingerprint(
        {"actor": actor_id, "type": job_type, "configuration": envelope}
    )
    _tenant_lock(session, tenant_id)
    old = session.scalar(
        select(ScheduledJobRun).where(
            ScheduledJobRun.tenant_id == tenant_id,
            ScheduledJobRun.request_id == request_id,
        )
    )
    if old:
        if old.request_fingerprint != fingerprint:
            raise JobError("request_conflict")
        return old
    if not _capacity(session, tenant_id):
        raise JobError("queue_full")
    run = ScheduledJobRun(
        id=f"run_{uuid4().hex}",
        tenant_id=tenant_id,
        actor_id=actor_id,
        job_type=job_type,
        configuration=envelope,
        request_id=request_id,
        request_fingerprint=fingerprint,
    )
    session.add(run)
    session.flush()
    _audit(session, tenant_id, actor_id, run.id, "enqueued")
    return run


def materialize_due(
    session: Session, tenant_id: str, *, outcomes: dict[str, int] | None = None
) -> int:
    """One occurrence per tenant per sweep; never execute or claim a handler."""
    if _tenant_lock(session, tenant_id, skip=True) is None or not _capacity(
        session, tenant_id
    ):
        return 0
    unfinished = (
        select(ScheduledJobRun.id)
        .where(
            ScheduledJobRun.tenant_id == tenant_id,
            ScheduledJobRun.schedule_id == ScheduledJob.id,
            ScheduledJobRun.status.in_(UNFINISHED),
        )
        .exists()
    )
    row = session.scalar(
        select(ScheduledJob)
        .where(
            ScheduledJob.tenant_id == tenant_id,
            ScheduledJob.enabled.is_(True),
            ScheduledJob.next_run_at <= now(),
            ~unfinished,
        )
        .order_by(ScheduledJob.next_run_at, ScheduledJob.id)
        .with_for_update(skip_locked=True)
        .limit(1)
        .execution_options(populate_existing=True)
    )
    if row is None:
        return 0
    try:
        _authorize_run_or_schedule(session, row)
    except JobError as error:
        row.enabled = False
        session.add(
            ScheduledJobRun(
                id=f"run_{uuid4().hex}",
                tenant_id=tenant_id,
                schedule_id=row.id,
                actor_id=row.actor_id,
                job_type=row.job_type,
                configuration=row.configuration,
                schedule_revision=row.revision,
                scheduled_for=row.next_run_at,
                status="failed",
                last_error_code=error.code,
                finished_at=now(),
            )
        )
        session.flush()
        if outcomes is not None:
            outcomes["failed"] += 1
        return 0
    initial = row.configuration.get("initial_offsets_seconds")
    run_configuration = _without_initial_timing(row.configuration)
    if initial:
        run_configuration = {**run_configuration, "initial_occurrence": True}
    run = ScheduledJobRun(
        id=f"run_{uuid4().hex}",
        tenant_id=tenant_id,
        schedule_id=row.id,
        actor_id=row.actor_id,
        job_type=row.job_type,
        configuration=run_configuration,
        schedule_revision=row.revision,
        scheduled_for=row.next_run_at,
    )
    session.add(run)
    if initial:
        row.next_run_at, remaining = next_initial_time(
            now(),
            datetime.fromisoformat(row.configuration["initial_started_at"]),
            initial,
            row.interval_seconds,
        )
        if not remaining:
            row.configuration = _without_initial_timing(row.configuration)
    else:
        row.next_run_at = next_time(
            now(),
            interval_seconds=row.interval_seconds,
            cron_expression=row.cron_expression,
            previous=row.next_run_at,
        )
    session.flush()
    return 1


def _eligible(run: ScheduledJobRun) -> bool:
    return (run.status in ("pending", "retry") and run.next_attempt_at <= now()) or (
        run.status == "running"
        and run.lease_expires_at is not None
        and run.lease_expires_at <= now()
    )


def _failed(
    session: Session,
    run: ScheduledJobRun,
    schedule: ScheduledJob | None,
    code: str,
    status: str = "failed",
) -> None:
    run.status, run.last_error_code = status, code
    run.finished_at = now() if status == "failed" else None
    run.claim_token = None
    run.lease_expires_at = None
    if schedule:
        schedule.enabled = False
    session.flush()


def claim_next(
    session: Session, tenant_id: str, *, outcomes: dict[str, int] | None = None
) -> ScheduledJobRun | None:
    """Claim one queued occurrence; never create a timed occurrence."""
    eligible = _claimable()
    candidates = session.execute(
        select(ScheduledJobRun.id, ScheduledJobRun.schedule_id)
        .where(
            ScheduledJobRun.tenant_id == tenant_id,
            eligible,
            or_(
                ScheduledJobRun.schedule_id.is_(None),
                select(ScheduledJob.id)
                .where(
                    ScheduledJob.tenant_id == tenant_id,
                    ScheduledJob.id == ScheduledJobRun.schedule_id,
                    ScheduledJob.enabled.is_(True),
                )
                .exists(),
            ),
        )
        .order_by(ScheduledJobRun.next_attempt_at, ScheduledJobRun.id)
        .limit(100)
    ).all()
    for run_id, schedule_id in candidates:
        schedule = (
            _schedule(session, tenant_id, schedule_id, lock=True, skip=True)
            if schedule_id
            else None
        )
        if schedule_id and (schedule is None or not schedule.enabled):
            continue
        run = _run(session, tenant_id, run_id, lock=True, skip=True)
        if run is None or not _eligible(run):
            continue
        try:
            _authorize_run_or_schedule(session, run)
        except JobError as error:
            _failed(session, run, schedule, error.code)
            if outcomes is not None:
                outcomes["failed"] += 1
            return None
        if run.attempt_count >= 3:
            _failed(session, run, schedule, "attempts_exhausted")
            if outcomes is not None:
                outcomes["failed"] += 1
            return None
        run.attempt_count += 1
        run.claim_token = uuid4().hex
        run.lease_expires_at = now() + timedelta(seconds=60)
        run.status, run.started_at = "running", now()
        session.flush()
        return run
    return None


def _locked_claim(session: Session, tenant_id: str, run_id: str):
    # Resolve identity before acquiring locks; re-read under locks below.
    identity = session.execute(
        select(ScheduledJobRun.schedule_id).where(
            ScheduledJobRun.tenant_id == tenant_id, ScheduledJobRun.id == run_id
        )
    ).first()
    if identity is None:
        raise JobError("not_found")
    schedule = (
        _schedule(session, tenant_id, identity[0], lock=True) if identity[0] else None
    )
    run = _run(session, tenant_id, run_id, lock=True)
    return schedule, run


def execute_claim(
    session: Session, tenant_id: str, run_id: str, claim_token: str
) -> str:
    """Effects and success share the caller's transaction. Handler cannot commit."""
    schedule, run = _locked_claim(session, tenant_id, run_id)
    if run.status == "succeeded":
        return "succeeded"
    if (
        run.status != "running"
        or not claim_token
        or run.claim_token != claim_token
        or run.lease_expires_at <= now()
    ):
        raise JobError("stale_claim")
    if schedule and not schedule.enabled:
        run.status = "retry"
        run.claim_token = None
        run.lease_expires_at = None
        return "retry"
    definition, parsed = _authorize_run_or_schedule(session, run)
    context = _context(tenant_id, run.actor_id, run)

    def reject_commit(_session):
        if _session.in_nested_transaction():
            return
        raise JobError("handler_commit_forbidden")

    event.listen(session, "before_commit", reject_commit)
    try:
        result = definition.handler(session, context, parsed)
        result = JobResult.model_validate(result)
        session.flush()
        if now() >= context.deadline or now() >= run.lease_expires_at:
            raise JobError("handler_timeout")
    finally:
        event.remove(session, "before_commit", reject_commit)
    run.result = result.model_dump(mode="json")
    run.status, run.finished_at, run.last_error_code = "succeeded", now(), None
    run.claim_token, run.lease_expires_at = None, None
    session.flush()
    return "succeeded"


def record_failure(
    session: Session,
    tenant_id: str,
    run_id: str,
    claim_token: str,
    code: str,
    *,
    retryable: bool = False,
    uncertain: bool = False,
) -> str:
    schedule, run = _locked_claim(session, tenant_id, run_id)
    if run.status != "running" or run.claim_token != claim_token:
        return run.status
    if uncertain:
        _failed(session, run, schedule, "outcome_unresolved", "unresolved")
    elif retryable and run.attempt_count < 3:
        run.status = "retry"
        run.next_attempt_at = now() + timedelta(
            seconds=(30, 120)[run.attempt_count - 1]
        )
        run.last_error_code = code
        run.claim_token, run.lease_expires_at = None, None
        session.flush()
    else:
        _failed(session, run, schedule, code)
    return run.status


def tenant_catalog(session: Session, after: str = "", limit: int = 100) -> list[str]:
    """Trusted process discovery of identity metadata only, not business rows."""
    if not 1 <= limit <= 100:
        raise JobError("invalid_limit")
    return list(
        session.scalars(
            select(Tenant.id).where(Tenant.id > after).order_by(Tenant.id).limit(limit)
        )
    )


def _claimable() -> ColumnElement[bool]:
    """Exactly what `claim_next` will take; discovery must not promise more."""
    return or_(
        and_(
            ScheduledJobRun.status.in_(("pending", "retry")),
            ScheduledJobRun.next_attempt_at <= now(),
        ),
        and_(
            ScheduledJobRun.status == "running",
            ScheduledJobRun.lease_expires_at <= now(),
        ),
    )


def due_tenants(session: Session, after: str = "", limit: int = 100) -> list[str]:
    """The tenants a worker has reason to visit (feature 201).

    An idle installation costs one query instead of one per tenant, which is what
    makes a short poll interval affordable.
    """
    if not 1 <= limit <= 100:
        raise JobError("invalid_limit")
    return list(
        session.scalars(
            select(ScheduledJobRun.tenant_id)
            .where(ScheduledJobRun.tenant_id > after, _claimable())
            .group_by(ScheduledJobRun.tenant_id)
            .order_by(ScheduledJobRun.tenant_id)
            .limit(limit)
        )
    )


def describe(row: ScheduledJob | ScheduledJobRun) -> dict:
    common = {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "actor_id": row.actor_id,
        "job_type": row.job_type,
        "created_at": row.created_at.isoformat(),
    }
    if isinstance(row, ScheduledJob):
        common.update(
            enabled=row.enabled,
            revision=row.revision,
            interval_seconds=row.interval_seconds,
            cron_expression=row.cron_expression,
            next_run_at=row.next_run_at.isoformat() if row.next_run_at else None,
        )
    else:
        common.update(
            schedule_id=row.schedule_id,
            status=row.status,
            attempt_count=row.attempt_count,
            scheduled_for=row.scheduled_for.isoformat() if row.scheduled_for else None,
            next_attempt_at=row.next_attempt_at.isoformat(),
            last_error_code=row.last_error_code,
            result=row.result,
        )
    return common


def get_run(session: Session, tenant_id: str, actor_id: str, run_id: str) -> dict:
    _owner(session, tenant_id, actor_id)
    row = _run(session, tenant_id, run_id)
    if row is None:
        raise JobError("not_found")
    return describe(row)


def _list(
    session: Session,
    model,
    tenant_id: str,
    actor_id: str,
    *,
    limit: int = 50,
    cursor: str | None = None,
    schedule_id: str | None = None,
) -> dict:
    _owner(session, tenant_id, actor_id)
    if not 1 <= limit <= 200:
        raise JobError("invalid_limit")
    scope = [model.__tablename__, tenant_id, schedule_id]
    stmt = select(model).where(model.tenant_id == tenant_id)
    if schedule_id:
        if _schedule(session, tenant_id, schedule_id) is None:
            raise JobError("not_found")
        stmt = stmt.where(model.schedule_id == schedule_id)
    if cursor:
        try:
            if len(cursor) > 2048:
                raise ValueError()
            data = json.loads(base64.urlsafe_b64decode(cursor))
            if data["scope"] != scope:
                raise ValueError()
            date = datetime.fromisoformat(data["at"])
            if date.tzinfo is None:
                raise ValueError()
            stmt = stmt.where(
                or_(
                    model.created_at > date,
                    and_(model.created_at == date, model.id > data["id"]),
                )
            )
        except (ValueError, KeyError, TypeError) as error:
            raise JobError("invalid_cursor") from error
    rows = list(
        session.scalars(stmt.order_by(model.created_at, model.id).limit(limit + 1))
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    token = None
    if has_more:
        token = base64.urlsafe_b64encode(
            json.dumps(
                {
                    "scope": scope,
                    "at": rows[-1].created_at.isoformat(),
                    "id": rows[-1].id,
                }
            ).encode()
        ).decode()
    return {
        "items": [describe(row) for row in rows],
        "has_more": has_more,
        "next_cursor": token,
        "tenant_id": tenant_id,
        "observed_at": now().isoformat(),
    }


def list_runs(session: Session, tenant_id: str, actor_id: str, **kwargs) -> dict:
    return _list(session, ScheduledJobRun, tenant_id, actor_id, **kwargs)


def list_schedules(session: Session, tenant_id: str, actor_id: str, **kwargs) -> dict:
    return _list(session, ScheduledJob, tenant_id, actor_id, **kwargs)


def has_due_schedule(session: Session, tenant_id: str) -> bool:
    return (
        session.scalar(
            select(ScheduledJob.id)
            .where(
                ScheduledJob.tenant_id == tenant_id,
                ScheduledJob.enabled.is_(True),
                ScheduledJob.next_run_at <= now(),
            )
            .limit(1)
        )
        is not None
    )


def cancel_queued_run(
    session: Session,
    tenant_id: str,
    actor_id: str,
    schedule_id: str,
    expected_revision: int,
    request_id: str,
) -> ScheduledJob:
    """Pause and cancel only undispatched work, retaining every occurrence."""
    _key(request_id)
    row = _schedule(session, tenant_id, schedule_id, lock=True)
    if row is None:
        raise JobError("not_found")
    fingerprint = _fingerprint(
        {"actor": actor_id, "action": "cancel_queued", "revision": expected_revision}
    )
    _owner(session, tenant_id, actor_id, row.job_type)
    if row.last_control_request_id == request_id:
        if row.last_control_fingerprint != fingerprint:
            raise JobError("request_conflict")
        return row
    if row.revision != expected_revision:
        raise JobError("stale_revision")
    unfinished = _unfinished(session, tenant_id, row.id)
    if unfinished and unfinished.status not in {"pending", "retry"}:
        raise JobError("unfinished_run")
    if unfinished:
        unfinished.status = "cancelled"
        unfinished.finished_at = now()
        unfinished.claim_token = None
        unfinished.lease_expires_at = None
    row.enabled, row.next_run_at = False, None
    row.revision += 1
    row.updated_at = now()
    row.last_control_request_id, row.last_control_fingerprint = request_id, fingerprint
    _audit(session, tenant_id, actor_id, row.id, "cancel_queued")
    session.flush()
    return row


def enqueue_projection_run(
    session: Session, tenant_id: str, names: list[str]
) -> ScheduledJobRun | None:
    """Internal scheduler producer; NULL actor grants only the registered cache job."""
    definition = get_definition("projections.refresh")
    parsed = definition.validate({"names": names})
    tenant = _tenant_lock(session, tenant_id, skip=True)
    if tenant is None or tenant.archived_at is not None:
        return None
    if session.scalar(
        select(ScheduledJobRun.id)
        .where(
            ScheduledJobRun.tenant_id == tenant_id,
            ScheduledJobRun.job_type == definition.name,
            ScheduledJobRun.status.in_(UNFINISHED),
        )
        .limit(1)
    ) or not _capacity(session, tenant_id):
        return None
    envelope = {"version": definition.version, "arguments": parsed.model_dump()}
    run = ScheduledJobRun(
        id=uid("run"),
        tenant_id=tenant_id,
        actor_id=None,
        job_type=definition.name,
        configuration=envelope,
        request_id=uid("projection"),
        request_fingerprint=_fingerprint(envelope),
    )
    session.add(run)
    session.flush()
    _authorize_run_or_schedule(session, run)
    return run
