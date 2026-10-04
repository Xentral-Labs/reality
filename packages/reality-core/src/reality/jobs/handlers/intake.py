"""Execute a fixed approved intake manifest; the worker never grants approval."""

import json

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from reality.db.core import Tenant
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.jobs.registry import JobDefinition, JobError, JobResult


class BatchConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    batch_id: str = Field(min_length=1, max_length=128)
    manifest_revision: int = Field(ge=1)
    continuation_id: str = Field(min_length=1, max_length=128)


def authorize(session, context, config):
    from reality.services.intake_batches import _batch, _manifest

    tenant = session.scalar(select(Tenant).where(Tenant.id == context.tenant_id))
    if tenant is None or tenant.archived_at is not None:
        raise JobError("not_authorized")
    batch = _batch(session, context.tenant_id, config.batch_id)
    _, manifest = _manifest(batch)
    progress = json.loads(batch.output)
    authority = progress.get("authorization", {})
    if (
        batch.status not in {"executing", "executed"}
        or manifest.revision != config.manifest_revision
        or authority.get("reviewer_user_id") != context.actor_id
    ):
        raise JobError("not_authorized")
    if context.run_id:
        run = session.scalar(
            select(ScheduledJobRun).where(
                ScheduledJobRun.tenant_id == context.tenant_id,
                ScheduledJobRun.id == context.run_id,
            )
        )
        if (
            run is None
            or run.actor_id != context.actor_id
            or run.job_type != "intake.batch_apply"
            or run.configuration.get("arguments") != config.model_dump()
        ):
            raise JobError("not_authorized")
    # Current membership/token/financial authority is checked per child, so a
    # revoked reviewer produces retained no-effect dispositions, not a stuck run.


def settle(session, context, config):
    from reality.services.business_locks import lock_delivery_state
    from reality.services.finance.accounts import lock_finance
    from reality.services.intake_batches import _batch, settle_chunk
    from reality.services.scheduled_jobs import enqueue_intake_batch_run

    lock_delivery_state(session, context.tenant_id)
    lock_finance(session, context.tenant_id)
    batch = _batch(session, context.tenant_id, config.batch_id, lock=True)
    progress = json.loads(batch.output)
    if (
        batch.status == "executed"
        or progress.get("continuation_id") != config.continuation_id
    ):
        return JobResult(
            counts={"settled": 0},
            references=[{"record_type": "change_proposal", "id": batch.id}],
        )
    result = settle_chunk(
        session,
        context.tenant_id,
        config.batch_id,
        continuation_id=config.continuation_id,
    )
    if not result["terminal"]:
        enqueue_intake_batch_run(session, context.tenant_id, batch.id)
    progress = json.loads(batch.output)
    recent = progress["results"][-result["settled"] :]
    counts = {"settled": result["settled"]}
    for row in recent:
        name = row["disposition"]
        counts[name] = counts.get(name, 0) + 1
    return JobResult(
        counts=counts, references=[{"record_type": "change_proposal", "id": batch.id}]
    )


BATCH = JobDefinition("intake.batch_apply", 1, BatchConfig, authorize, settle)
