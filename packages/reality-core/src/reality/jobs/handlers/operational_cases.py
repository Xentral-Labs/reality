"""Database-only coordination consumer, under the confirmed adoption owner."""

from pydantic import BaseModel, ConfigDict, Field

from reality.jobs.registry import JobDefinition, JobResult, require_company_owner
from reality.services.operational_cases import reconcile_events


class CaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: int = Field(default=100, ge=1, le=100)


def reconcile(session, context, config):
    count = reconcile_events(
        session, context.tenant_id, limit=config.limit, _commit=False
    )
    return JobResult(counts={"incorporated": count})


RECONCILE = JobDefinition(
    "operational_cases.reconcile", 1, CaseConfig, require_company_owner, reconcile
)
