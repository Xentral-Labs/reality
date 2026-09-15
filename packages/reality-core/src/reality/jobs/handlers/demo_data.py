"""One bounded synthetic intake per durable scheduler occurrence."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from reality.db.core import SourceRecord, SourceSystem
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.integrations import demo_data as synthetic
from reality.jobs.registry import JobDefinition, JobError, JobResult, RecordReference


class DemoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    connection_id: str
    profile_version: Literal[1] = 1
    seed: str = Field(min_length=1, max_length=128)
    rate: Literal[10, 60, 300] = 60
    references: dict[str, dict[str, str]]


def authorize(session, context, config):
    from reality.services import demo_data
    from reality.services.core import RealityError

    try:
        demo_data.eligible(session, context.tenant_id, context.actor_id)
        connection = demo_data._connection(session, context.tenant_id)
        if (
            not connection
            or connection.id != config.connection_id
            or connection.state == "disconnected"
        ):
            raise JobError("not_authorized")
        source = session.scalar(
            select(SourceSystem).where(
                SourceSystem.tenant_id == context.tenant_id,
                SourceSystem.id == connection.source_system_id,
            )
        )
        if not source or not source.is_active:
            raise JobError("inactive_source")
        current = demo_data.preview(session, context.tenant_id, context.actor_id)[
            "references"
        ]
        # Every reference the schedule captured must still resolve to the same
        # row; references added later (new pool customers) do not invalidate it.
        if any(
            current.get(kind, {}).get(key) != value
            for kind, rows in config.references.items()
            for key, value in rows.items()
        ):
            raise JobError("incompatible_references")
        if context.run_id:
            run = session.scalar(
                select(ScheduledJobRun).where(
                    ScheduledJobRun.tenant_id == context.tenant_id,
                    ScheduledJobRun.id == context.run_id,
                )
            )
            if (
                not run
                or not run.schedule_id
                or connection.current_schedule_id != run.schedule_id
                or connection.state != "running"
            ):
                raise JobError("inactive_connection")
    except RealityError as error:
        raise JobError("not_authorized") from error


def _throttle(connection, schedule, counts: dict, settlement=None) -> bool:
    if counts["pending"] + counts["failed"] < 20:
        return False
    connection.state, schedule.enabled, schedule.next_run_at = "paused", False, None
    if settlement is not None:
        settlement.enabled, settlement.next_run_at = False, None
    connection.revision += 1
    return True


def generate(session, context, config):
    import json

    from reality.services import core, demo_data

    connection, schedule = demo_data._locked(session, context.tenant_id)
    authorize(session, context, config)
    delivery = session.scalar(
        select(ScheduledJobRun).where(
            ScheduledJobRun.tenant_id == context.tenant_id,
            ScheduledJobRun.id == context.run_id,
        )
    )
    inputs = (
        schedule.id,
        context.run_id,
        config.seed,
        delivery.created_at,
        config.references,
    )
    planned = (
        [synthetic.produce(*inputs)]
        if delivery.configuration.get("initial_occurrence")
        else synthetic.plan(*inputs)
    )
    counts = {"generated": 0, "imported": 0, "failed": 0}
    references: list[RecordReference] = []

    settlement = demo_data._settlement_schedule(session, context.tenant_id, connection)

    def throttled() -> bool:
        return _throttle(
            connection,
            schedule,
            demo_data._counts(
                session, context.tenant_id, source_types=demo_data.SYNTHETIC_TYPES
            ),
            settlement,
        )

    for position, payload in enumerate(planned, 1):
        if throttled():
            counts["throttled"] = 1
            break
        # The first order keeps the historical identity; later orders in the
        # same delivery append their position.
        external_id = f"{schedule.id}:{context.run_id}" + (
            f":{position}" if position > 1 else ""
        )
        existing = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == context.tenant_id,
                SourceRecord.source_system == "demo_data",
                SourceRecord.source_type == "order",
                SourceRecord.external_id == external_id,
            )
        )
        if existing:
            payload = json.loads(existing.payload)
        with demo_data.intake_scope(session, context.tenant_id, context.actor_id):
            source, job = core.enqueue_source(
                session,
                context.tenant_id,
                "demo_data",
                "order",
                external_id,
                payload,
                _commit=False,
            )
            result = core.process_import_job_bound(session, context.tenant_id, job.id)
        counts["generated"] += 1
        counts["imported"] += int(result is not None)
        counts["failed"] += int(result is None)
        references += [
            RecordReference(record_type="source_record", id=source.id),
            RecordReference(record_type="import_job", id=job.id),
        ]
    if "throttled" not in counts and throttled():
        counts["throttled"] = 1
    return JobResult(counts=counts, references=references)


DEMO = JobDefinition("demo.generate_orders", 1, DemoConfig, authorize, generate)


# --- Feature 168: the settlement stream ------------------------------------------


class SettleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    connection_id: str
    profile_version: Literal[1] = 1
    references: dict[str, dict[str, str]]


def authorize_settle(session, context, config):
    """Owner, connection, source and reference checks, bound to the settlement schedule."""
    from reality.services import demo_data
    from reality.services.core import RealityError

    try:
        demo_data.eligible(session, context.tenant_id, context.actor_id)
        connection = demo_data._connection(session, context.tenant_id)
        if (
            not connection
            or connection.id != config.connection_id
            or connection.state == "disconnected"
        ):
            raise JobError("not_authorized")
        source = session.scalar(
            select(SourceSystem).where(
                SourceSystem.tenant_id == context.tenant_id,
                SourceSystem.id == connection.source_system_id,
            )
        )
        if not source or not source.is_active:
            raise JobError("inactive_source")
        current = demo_data.preview(session, context.tenant_id, context.actor_id)[
            "references"
        ]
        if any(
            current.get(kind, {}).get(key) != value
            for kind, rows in config.references.items()
            for key, value in rows.items()
        ):
            raise JobError("incompatible_references")
        if context.run_id:
            run = session.scalar(
                select(ScheduledJobRun).where(
                    ScheduledJobRun.tenant_id == context.tenant_id,
                    ScheduledJobRun.id == context.run_id,
                )
            )
            if (
                not run
                or not run.schedule_id
                or connection.settlement_schedule_id != run.schedule_id
                or connection.state != "running"
            ):
                raise JobError("inactive_connection")
    except RealityError as error:
        raise JobError("not_authorized") from error


def settle(session, context, config):
    """Emit the invoices and payments that are due, oldest first, at most a batch."""
    import json

    from reality.services import core, demo_data

    connection, schedule = demo_data._locked(session, context.tenant_id)
    settlement = demo_data._settlement_schedule(session, context.tenant_id, connection)
    authorize_settle(session, context, config)
    occurrence = session.scalar(
        select(ScheduledJobRun).where(
            ScheduledJobRun.tenant_id == context.tenant_id,
            ScheduledJobRun.id == context.run_id,
        )
    )
    counts = {"invoices": 0, "payments": 0, "imported": 0, "failed": 0}
    references: list[RecordReference] = []

    def throttled() -> bool:
        return _throttle(
            connection,
            schedule,
            demo_data._counts(
                session, context.tenant_id, source_types=demo_data.SYNTHETIC_TYPES
            ),
            settlement,
        )

    if throttled():
        return JobResult(counts={**counts, "throttled": 1}, references=references)
    work = demo_data.settlement_work(
        session,
        context.tenant_id,
        occurrence.created_at,
        limit=demo_data.SETTLEMENT_BATCH,
    )
    for item in work:
        if throttled():
            counts["throttled"] = 1
            break
        existing = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == context.tenant_id,
                SourceRecord.source_system == "demo_data",
                SourceRecord.source_type == item["source_type"],
                SourceRecord.external_id == item["external_id"],
            )
        )
        payload = json.loads(existing.payload) if existing else item["payload"]
        with demo_data.settlement_scope(session, context.tenant_id, context.actor_id):
            source, job = core.enqueue_source(
                session,
                context.tenant_id,
                "demo_data",
                item["source_type"],
                item["external_id"],
                payload,
                _commit=False,
            )
            result = core.process_import_job_bound(session, context.tenant_id, job.id)
        counts["invoices" if item["source_type"] == "invoice" else "payments"] += 1
        counts["imported"] += int(result is not None)
        counts["failed"] += int(result is None)
        references += [
            RecordReference(record_type="source_record", id=source.id),
            RecordReference(record_type="import_job", id=job.id),
        ]
    if "throttled" not in counts and throttled():
        counts["throttled"] = 1
    return JobResult(counts=counts, references=references)


SETTLE = JobDefinition("demo.settle_orders", 1, SettleConfig, authorize_settle, settle)
