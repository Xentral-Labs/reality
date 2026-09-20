"""Committed outbox eligibility; only the shared scheduler dispatches cache work."""

from datetime import timedelta

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import (
    ProjectionCheckpoint,
    Tenant,
    TenantEventProgress,
    now,
)
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services import projections, scheduled_jobs


def enqueue_due_projections(
    session: Session, tenant_id: str
) -> list[ScheduledJobRun]:
    """One run per projection that is behind (spec 181 FR-004).

    The twelve used to share a run. Their checkpoints, statuses and errors were
    already their own, but the *job* was not: a builder that exceeded the budget
    failed a run that had covered several projections, so the others' work was
    recorded as failed with it and recovery could not name one of them.

    A projection that already has an unfinished run is not enqueued again — that is
    the coalescing the shared run used to give, kept per projection rather than per
    company. A quiet company still produces nothing at all.
    """
    tenant = session.scalar(
        select(Tenant).where(Tenant.id == tenant_id).with_for_update(skip_locked=True)
    )
    if tenant is None or tenant.archived_at is not None:
        return []
    names = due_projections(session, tenant_id)
    if not names:
        return []
    queued = queued_projections(session, tenant_id)
    runs = []
    for name in names:
        if name in queued:
            continue
        run = scheduled_jobs.enqueue_projection_run(
            session, tenant_id, [name], queued=queued
        )
        if run is None:
            continue
        runs.append(run)
        queued.add(name)
    return runs


def queued_projections(session: Session, tenant_id: str) -> set[str]:
    """Which projections of this company already have a run waiting or running.

    Read from the runs' own configuration rather than from a new column: there are
    at most as many unfinished refresh runs as there are projections, so this is one
    read of a handful of rows, and the queue stays the single source of truth about
    what is already promised.
    """
    unfinished = session.scalars(
        select(ScheduledJobRun).where(
            ScheduledJobRun.tenant_id == tenant_id,
            ScheduledJobRun.job_type == "projections.refresh",
            ScheduledJobRun.status.in_(scheduled_jobs.UNFINISHED),
        )
    )
    return {
        name
        for run in unfinished
        for name in (run.configuration or {}).get("arguments", {}).get("names", [])
    }


def due_projections(session: Session, tenant_id: str) -> list[str]:
    """Which projections of one company are behind — the same answer, in one round trip.

    The rules are unchanged and deliberately so: a projection is behind when its row
    shape is old, when the events *it depends on* have moved past it, or when it is
    time-sensitive and the cadence has come round; and a projection whose last run
    failed is not behind, it is broken, and waits for someone to recover it.

    What changes is that the twelve were asked one statement at a time (spec 181
    FR-004). They are scalar expressions over the same snapshot, so they can be asked
    together, and a company that has nothing to do now says so in a single read.
    """
    columns = []
    for index, name in enumerate(projections.MATERIALIZED_PROJECTIONS):
        for key, value in projections.projection_state_expressions(
            tenant_id, name
        ).items():
            columns.append(value.label(f"p{index}_{key}"))
    values = session.execute(select(*columns)).mappings().one()
    behind = []
    for index, name in enumerate(projections.MATERIALIZED_PROJECTIONS):
        state = projections.projection_metadata(
            name,
            {
                key: values[f"p{index}_{key}"]
                for key in projections.projection_state_expressions(tenant_id, name)
            },
        )["state"]
        if state in {"pending", "uninitialized"}:
            behind.append(name)
    return behind


#: How long a time-sensitive projection may sit before the cadence comes round. It is
#: the interval `rebuild_projections` applies; naming it beside the selection keeps the
#: two from drifting apart about what "due" means.
CADENCE_SECONDS = 60


def due_projection_tenants(
    session: Session, after: str = "", limit: int = 100
) -> list[str]:
    """Companies that might have a projection to refresh, asked of all of them at once.

    Spec 181 FR-004: "a company with no change and no due date MUST cause no work".
    The scheduler used to walk every company and ask twelve questions about each, so ten
    thousand quiet companies cost a hundred and twenty thousand reads a sweep. This is
    one indexed read that skips the quiet ones entirely.

    It is a filter, not a decision. It answers *might*: the comparison is against the
    company's latest event rather than the latest event each projection depends on,
    because that distinction needs the event types and cannot be made across companies
    in one read. So it over-selects and never under-selects — the direction that would
    leave a projection stale — and `due_projections` then makes the precise decision for
    the few companies it returns.
    """
    total = len(projections.MATERIALIZED_PROJECTIONS)
    checkpoints = (
        select(
            ProjectionCheckpoint.tenant_id.label("tenant_id"),
            func.count(ProjectionCheckpoint.id).label("built"),
            func.min(ProjectionCheckpoint.observed_event_sequence).label("looked_at"),
            func.min(ProjectionCheckpoint.projection_version).label("oldest_version"),
            func.min(
                case(
                    (
                        ProjectionCheckpoint.projection_name.in_(
                            projections.TIME_SENSITIVE_PROJECTIONS
                        ),
                        ProjectionCheckpoint.updated_at,
                    ),
                    else_=None,
                )
            ).label("cadence_at"),
        )
        .where(
            ProjectionCheckpoint.projection_name.in_(
                projections.MATERIALIZED_PROJECTIONS
            )
        )
        .group_by(ProjectionCheckpoint.tenant_id)
        .subquery()
    )
    cadence = now() - timedelta(seconds=CADENCE_SECONDS)
    return list(
        session.scalars(
            select(Tenant.id)
            .outerjoin(checkpoints, checkpoints.c.tenant_id == Tenant.id)
            .outerjoin(TenantEventProgress, TenantEventProgress.tenant_id == Tenant.id)
            .where(
                Tenant.id > after,
                Tenant.archived_at.is_(None),
                or_(
                    checkpoints.c.built.is_(None),
                    checkpoints.c.built < total,
                    checkpoints.c.looked_at
                    < func.coalesce(TenantEventProgress.last_event_sequence, 0),
                    checkpoints.c.oldest_version != projections.PROJECTION_VERSION,
                    checkpoints.c.cadence_at <= cadence,
                ),
            )
            .order_by(Tenant.id)
            .limit(limit)
        )
    )


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
