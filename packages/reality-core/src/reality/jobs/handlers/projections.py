"""Allowlisted infrastructure capability: rebuild disposable tenant caches only."""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.jobs.registry import JobContext, JobDefinition, JobError, JobResult


class ProjectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    names: list[str] = Field(min_length=1, max_length=12)

    @field_validator("names")
    @classmethod
    def known_unique(cls, names: list[str]) -> list[str]:
        from reality.services.projections import MATERIALIZED_PROJECTIONS

        if len(set(names)) != len(names) or not set(names) <= set(
            MATERIALIZED_PROJECTIONS
        ):
            raise ValueError("Unknown or duplicate projection.")
        return names


def authorize(session: Session, context: JobContext, config: ProjectionConfig) -> None:
    from reality.db.core import Tenant
    from reality.db.scheduled_jobs import ScheduledJobRun

    tenant = session.scalar(select(Tenant).where(Tenant.id == context.tenant_id))
    run = session.scalar(
        select(ScheduledJobRun).where(
            ScheduledJobRun.tenant_id == context.tenant_id,
            ScheduledJobRun.id == context.run_id,
            ScheduledJobRun.job_type == "projections.refresh",
            ScheduledJobRun.actor_id.is_(None),
            ScheduledJobRun.schedule_id.is_(None),
        )
    )
    if (
        context.actor_id is not None
        or tenant is None
        or tenant.archived_at is not None
        or run is None
    ):
        raise JobError("not_authorized")


def refresh(
    session: Session, context: JobContext, config: ProjectionConfig
) -> JobResult:
    from reality.services.projections import rebuild_projections

    count = rebuild_projections(session, context.tenant_id, config.names)
    return JobResult(counts={"projections": len(config.names), "rows": count})


REFRESH = JobDefinition(
    name="projections.refresh",
    version=1,
    config_model=ProjectionConfig,
    authorize=authorize,
    handler=refresh,
)
