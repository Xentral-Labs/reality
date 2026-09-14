"""Opt-in database-only retention job; never delivers email."""

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from reality.jobs.registry import (
    JobContext,
    JobDefinition,
    JobResult,
    require_company_owner,
)


class CleanupConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


def cleanup(session: Session, context: JobContext, config: CleanupConfig) -> JobResult:
    from reality.services.notifications import cleanup_terminal_invitations

    return JobResult(
        counts={
            "invitations_removed": cleanup_terminal_invitations(
                session, tenant_id=context.tenant_id, limit=100
            )
        }
    )


CLEANUP = JobDefinition(
    "invitations.cleanup", 1, CleanupConfig, require_company_owner, cleanup
)
