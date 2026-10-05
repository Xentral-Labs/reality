"""Database-only coordination; platform authority never grants business effects."""

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from reality.db.core import Tenant
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.jobs.registry import (
    JobDefinition,
    JobError,
    JobResult,
    require_company_owner,
)
from reality.services.operational_cases import reconcile_events


class CaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: int = Field(default=100, ge=1, le=100)


def authorize(session, context, config):
    if context.actor_id is not None:
        # Retained pre-upgrade owner jobs keep their original authority.
        require_company_owner(session, context, config)
        return
    tenant = session.get(Tenant, context.tenant_id)
    run = session.scalar(
        select(ScheduledJobRun).where(
            ScheduledJobRun.tenant_id == context.tenant_id,
            ScheduledJobRun.id == context.run_id,
            ScheduledJobRun.job_type == "operational_cases.reconcile",
            ScheduledJobRun.actor_id.is_(None),
            ScheduledJobRun.schedule_id.is_(None),
        )
    )
    if tenant is None or tenant.archived_at is not None or run is None:
        raise JobError("not_authorized")


def reconcile(session, context, config):
    count = reconcile_events(
        session, context.tenant_id, limit=config.limit, _commit=False
    )
    return JobResult(counts={"incorporated": count})


RECONCILE = JobDefinition(
    "operational_cases.reconcile", 1, CaseConfig, authorize, reconcile
)
