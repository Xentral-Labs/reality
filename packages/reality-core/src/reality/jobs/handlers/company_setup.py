"""Seed a confirmed company profile outside the request that asked for it.

Feature 199: creation commits the tenant, membership and run metadata and enqueues
this run. The handler performs the same seeding the request used to do, so a slow
profile can no longer take a browser connection with it.
"""

import json
import logging

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from reality.jobs.registry import JobContext, JobDefinition, JobError, JobResult

JOB_TYPE = "company_setup.initialize"
logger = logging.getLogger("reality.background")


def _interruption_code(stage: str, error: Exception) -> str:
    sqlstate = getattr(getattr(error, "orig", None), "sqlstate", None)
    suffix = (
        "lock_timeout"
        if sqlstate == "55P03"
        else "statement_timeout"
        if sqlstate == "57014"
        else "job_contract"
        if isinstance(error, JobError)
        else "business_rule"
        if type(error).__name__
        in {"Conflict", "InvalidOperation", "NotFound", "PlaygroundOperationDenied"}
        else "database"
        if type(error).__name__.endswith("Error") and hasattr(error, "statement")
        else "pool_timeout"
        if type(error).__name__ == "TimeoutError"
        else "incomplete"
    )
    return f"setup_{stage}_{suffix}"


class SetupConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(min_length=1, max_length=128)


def require_setup_owner(session: Session, tenant_id: str, actor_id: str | None) -> None:
    """The company's own playground owner, not `require_company_owner`.

    A verified account pending admission may create a Sandbox, so account admission is
    not the boundary here. Ownership of this tenant's playground run is: the run is
    resolved from the tenant and the actor, and then checked in full.
    """
    from sqlalchemy import select

    from reality.db.core import PlaygroundRun
    from reality.services.core import RealityError
    from reality.services.tenant_policy import require_playground_run

    if not actor_id:
        raise JobError("not_authorized")
    run_id = session.scalar(
        select(PlaygroundRun.id).where(
            PlaygroundRun.tenant_id == tenant_id,
            PlaygroundRun.owner_user_id == actor_id,
        )
    )
    if run_id is None:
        raise JobError("not_authorized")
    try:
        require_playground_run(session, run_id, actor_id)
    except RealityError as error:
        raise JobError("not_authorized") from error


def authorize(session: Session, context: JobContext, config: SetupConfig) -> None:
    from reality.db.core import Tenant
    from reality.services.core import RealityError
    from reality.services.tenant_policy import require_playground_run

    require_setup_owner(session, context.tenant_id, context.actor_id)
    try:
        run = require_playground_run(session, config.run_id, context.actor_id)
    except RealityError as error:
        raise JobError("not_authorized") from error
    tenant = session.get(Tenant, context.tenant_id)
    if run.tenant_id != context.tenant_id or tenant is None or tenant.archived_at:
        raise JobError("not_authorized")


def initialize(session: Session, context: JobContext, config: SetupConfig) -> JobResult:
    """Seed the profile, complete live setup and publish initial read projections."""
    from reality.services.company_setup import _finish_live_setup, initialize_profile
    from reality.services.projections import (
        MATERIALIZED_PROJECTIONS,
        rebuild_projections,
    )

    # The canonical profile is a bounded but broad transaction. It can briefly
    # overlap the tenant's freshly queued projection work, so the generic 2-second
    # worker lock budget is too small even though the 20-second statement and
    # 30-second child-process bounds still apply.
    session.execute(text("SET LOCAL lock_timeout = '10s'"))
    try:
        run = initialize_profile(session, config.run_id, context.actor_id, _commit=False)
    except Exception as error:
        logger.warning(
            json.dumps(
                {
                    "event": "company_setup_interrupted",
                    "stage": "profile",
                    "exception_type": type(error).__name__,
                    "sqlstate": getattr(getattr(error, "orig", None), "sqlstate", None),
                }
            )
        )
        raise JobError(_interruption_code("profile", error), retryable=True) from error
    try:
        _finish_live_setup(session, run, context.actor_id, _commit=False)
    except Exception as error:
        logger.warning(
            json.dumps(
                {
                    "event": "company_setup_interrupted",
                    "stage": "live_setup",
                    "exception_type": type(error).__name__,
                    "sqlstate": getattr(getattr(error, "orig", None), "sqlstate", None),
                }
            )
        )
        raise JobError(_interruption_code("live", error), retryable=True) from error
    progress = run.initialization_progress
    if (
        progress.get("creation_intent", {}).get("live_simulation")
        and not progress.get("live_setup_complete")
    ):
        raise JobError("setup_live_incomplete", retryable=True)
    try:
        rebuild_projections(
            session,
            context.tenant_id,
            MATERIALIZED_PROJECTIONS,
            force=True,
        )
    except Exception as error:
        logger.warning(
            json.dumps(
                {
                    "event": "company_setup_interrupted",
                    "stage": "calculation",
                    "exception_type": type(error).__name__,
                    "sqlstate": getattr(getattr(error, "orig", None), "sqlstate", None),
                }
            )
        )
        raise JobError(_interruption_code("calculation", error), retryable=True) from error
    return JobResult(
        counts={"initialized": 1},
        references=[{"record_type": "playground_run", "id": run.id}],
    )


INITIALIZE = JobDefinition(
    name=JOB_TYPE,
    version=1,
    config_model=SetupConfig,
    authorize=authorize,
    handler=initialize,
)
