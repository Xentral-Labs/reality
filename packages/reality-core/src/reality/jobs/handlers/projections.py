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


#: How many finished runs one refresh forgets on its way out. The work that
#: makes the history is the work that tidies it, so the tidying keeps pace with
#: the mess by construction and costs an idle company nothing. Small, because it
#: shares the handler's thirty-second budget with the refresh itself.
FORGET_PER_REFRESH = 20


def refresh(
    session: Session, context: JobContext, config: ProjectionConfig
) -> JobResult:
    from reality.services.projections import rebuild_projections
    from reality.services.scheduled_jobs import cleanup_finished_runs

    count = rebuild_projections(session, context.tenant_id, config.names)
    # Spec 181 FR-005: this table was the one thing in the schema that grew
    # without any bound, and refreshes are what fill it. A company that refreshes
    # often forgets often; one that has stopped has nothing left to forget.
    forgotten = cleanup_finished_runs(
        session, tenant_id=context.tenant_id, limit=FORGET_PER_REFRESH
    )
    return JobResult(
        counts={
            "projections": len(config.names),
            "rows": count,
            "runs_forgotten": forgotten,
        }
    )


REFRESH = JobDefinition(
    name="projections.refresh",
    version=1,
    config_model=ProjectionConfig,
    authorize=authorize,
    handler=refresh,
)
