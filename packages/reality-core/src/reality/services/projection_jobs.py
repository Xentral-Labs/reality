"""Committed outbox eligibility; only the shared scheduler dispatches cache work."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Tenant
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services import projections, scheduled_jobs


def enqueue_due_projections(session: Session, tenant_id: str) -> ScheduledJobRun | None:
    """Coalesce dirty projections; an unavailable/full queue cannot affect writers."""
    tenant = session.scalar(
        select(Tenant).where(Tenant.id == tenant_id).with_for_update(skip_locked=True)
    )
    if tenant is None or tenant.archived_at is not None:
        return None
    if session.scalar(
        select(ScheduledJobRun.id)
        .where(
            ScheduledJobRun.tenant_id == tenant_id,
            ScheduledJobRun.job_type == "projections.refresh",
            ScheduledJobRun.status.in_(scheduled_jobs.UNFINISHED),
        )
        .limit(1)
    ):
        return None
    names = []
    # Each query is bounded metadata, not a derivation or a business-row load.
    for name in projections.MATERIALIZED_PROJECTIONS:
        expressions = projections.projection_state_expressions(tenant_id, name)
        values = (
            session.execute(
                select(*(value.label(key) for key, value in expressions.items()))
            )
            .mappings()
            .one()
        )
        if projections.projection_metadata(name, values)["state"] in {
            "pending",
            "uninitialized",
        }:
            names.append(name)
    if not names:
        return None
    return scheduled_jobs.enqueue_projection_run(session, tenant_id, names)


def _prefer_projection(session: Session, tenant_id: str) -> bool:
    """Alternate eligible work classes using retained history, including cold ticks."""
    latest = session.scalar(
        select(ScheduledJobRun.job_type)
        .where(
            ScheduledJobRun.tenant_id == tenant_id,
        )
        .order_by(ScheduledJobRun.created_at.desc(), ScheduledJobRun.id.desc())
        .limit(1)
    )
    return latest is not None and latest != "projections.refresh"
