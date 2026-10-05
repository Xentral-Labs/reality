"""Version-owned database coordination through the existing shared queue."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from reality.db.core import Tenant, TenantEventProgress, uid
from reality.db.operational_cases import CaseConsumerCheckpoint, CaseRollout
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services import scheduled_jobs


def due_case_tenants(session: Session, after: str = "", limit: int = 100):
    from reality.services.operational_cases import schema_available

    if not schema_available(session):
        raise scheduled_jobs.JobError("case_schema_not_ready")
    return list(
        session.scalars(
            select(Tenant.id)
            .outerjoin(CaseRollout, CaseRollout.tenant_id == Tenant.id)
            .outerjoin(
                CaseConsumerCheckpoint, CaseConsumerCheckpoint.tenant_id == Tenant.id
            )
            .outerjoin(TenantEventProgress, TenantEventProgress.tenant_id == Tenant.id)
            .where(
                Tenant.id > after,
                Tenant.archived_at.is_(None),
                or_(
                    CaseRollout.tenant_id.is_(None),
                    CaseRollout.completed_at.is_(None),
                    CaseConsumerCheckpoint.tenant_id.is_(None),
                    TenantEventProgress.last_event_sequence
                    > CaseConsumerCheckpoint.incorporated_sequence,
                ),
            )
            .order_by(Tenant.id)
            .limit(limit)
        )
    )


def enqueue_case_run(session: Session, tenant_id: str):
    tenant = scheduled_jobs._tenant_lock(session, tenant_id, skip=True)
    if tenant is None or tenant.archived_at is not None:
        return None
    from reality.services.operational_cases import coordination_status

    if coordination_status(session, tenant_id)["coverage_ready"]:
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
        recoverable = latest.status == "failed" and (
            latest.last_error_code
            in scheduled_jobs.INFRASTRUCTURE_CODES | {"attempts_exhausted"}
            or (
                latest.actor_id is not None
                and latest.last_error_code == "not_authorized"
            )
        )
        if not recoverable:
            return None  # Preserve unresolved outcomes and non-infrastructure verdicts.
    # This allowlisted handler has database-only effects. Failed transactions rolled
    # back; resume traversal with platform attribution while retaining history.
    if not scheduled_jobs._capacity(session, tenant_id):
        return None
    envelope = {"version": 1, "arguments": {"limit": 100}}
    run = ScheduledJobRun(
        id=uid("run"),
        tenant_id=tenant_id,
        actor_id=None,
        job_type="operational_cases.reconcile",
        configuration=envelope,
        request_id=uid("case_job"),
        request_fingerprint=scheduled_jobs._fingerprint(envelope),
    )
    session.add(run)
    session.flush()
    scheduled_jobs._authorize_run_or_schedule(session, run)
    return run
