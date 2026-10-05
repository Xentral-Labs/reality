"""Reuse the shared queue; no per-case timer or external-effect worker."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, Tenant, TenantEventProgress, uid
from reality.db.operational_cases import CaseAdoption, CaseConsumerCheckpoint
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services import scheduled_jobs


def due_case_tenants(session: Session, after: str = "", limit: int = 100):
    from reality.services.operational_cases import schema_available

    if not schema_available(session):
        return []
    return list(
        session.scalars(
            select(CaseAdoption.tenant_id)
            .join(
                CaseConsumerCheckpoint,
                CaseConsumerCheckpoint.tenant_id == CaseAdoption.tenant_id,
            )
            .join(
                TenantEventProgress,
                TenantEventProgress.tenant_id == CaseAdoption.tenant_id,
            )
            .join(Tenant, Tenant.id == CaseAdoption.tenant_id)
            .where(
                CaseAdoption.tenant_id > after,
                Tenant.archived_at.is_(None),
                TenantEventProgress.last_event_sequence
                > CaseConsumerCheckpoint.incorporated_sequence,
            )
            .order_by(CaseAdoption.tenant_id)
            .limit(limit)
        )
    )


def enqueue_case_run(session: Session, tenant_id: str):
    tenant = scheduled_jobs._tenant_lock(session, tenant_id, skip=True)
    if tenant is None or tenant.archived_at is not None:
        return None
    from reality.services.operational_cases import adoption

    scope = adoption(session, tenant_id)
    if scope is None:
        return None
    checkpoint = session.get(CaseConsumerCheckpoint, (tenant_id, 1))
    progress = session.get(TenantEventProgress, tenant_id)
    if (
        scope is None
        or checkpoint is None
        or progress is None
        or progress.last_event_sequence <= checkpoint.incorporated_sequence
    ):
        return None
    latest = session.scalar(
        select(ScheduledJobRun)
        .where(
            ScheduledJobRun.tenant_id == tenant_id,
            ScheduledJobRun.job_type == "operational_cases.reconcile",
        )
        .order_by(ScheduledJobRun.created_at.desc(), ScheduledJobRun.id.desc())
        .limit(1)
    )
    if latest is not None and latest.status not in {"succeeded", "cancelled"}:
        return None  # Shared recovery owns failed/unresolved runs.
    decision = session.get(ChangeProposal, (tenant_id, scope.decision_id))
    if decision is None or not decision.decided_by_user_id:
        return None
    if not scheduled_jobs._capacity(session, tenant_id):
        return None
    envelope = {"version": 1, "arguments": {"limit": 100}}
    run = ScheduledJobRun(
        id=uid("run"),
        tenant_id=tenant_id,
        actor_id=decision.decided_by_user_id,
        job_type="operational_cases.reconcile",
        configuration=envelope,
        request_id=uid("case_job"),
        request_fingerprint=scheduled_jobs._fingerprint(envelope),
    )
    session.add(run)
    session.flush()
    try:
        scheduled_jobs._authorize_run_or_schedule(session, run)
    except scheduled_jobs.JobError as error:
        run.status = "failed"
        run.last_error_code = error.code
    return run
