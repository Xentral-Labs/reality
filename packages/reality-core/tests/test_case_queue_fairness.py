"""Default database coordination cannot starve ordinary shared-queue work."""

from datetime import timedelta

from sqlalchemy import select

from reality.db.core import now, uid
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services import scheduled_jobs as jobs
from reality.services.case_jobs import enqueue_case_run


def internal(session, tenant, index):
    run = ScheduledJobRun(
        id=uid("case_queue"), tenant_id=tenant, actor_id=None,
        job_type="operational_cases.reconcile",
        configuration={"version": 1, "arguments": {"limit": 1}},
        request_id=f"case-{index}", request_fingerprint="case",
        next_attempt_at=now() - timedelta(days=1),
    )
    session.add(run)
    session.flush()
    return run


def ordinary(session, tenant, actor, key):
    return jobs.create_manual_run(
        session, tenant, actor, "invitations.cleanup", {}, request_id=key,
    )


def test_claims_alternate_before_the_bounded_candidate_selection(
    session, business, scheduled_owner
):
    tenant = business.tenant.id
    backlog = [internal(session, tenant, i) for i in range(101)]
    first = ordinary(session, tenant, scheduled_owner.id, "first")
    second = ordinary(session, tenant, scheduled_owner.id, "second")
    assert jobs.claim_next(session, tenant).id == first.id
    claimed = jobs.claim_next(session, tenant)
    assert claimed.id in {run.id for run in backlog}
    assert claimed.actor_id is None
    assert jobs.claim_next(session, tenant).id == second.id
    assert jobs.claim_next(session, tenant).job_type == "operational_cases.reconcile"
    # New enqueues do not manufacture a claim turn.
    third = ordinary(session, tenant, scheduled_owner.id, "third")
    internal(session, tenant, 102)
    assert jobs.claim_next(session, tenant).id == third.id


def test_locked_preferred_work_allows_the_other_class(scheduled_database):
    _, factory, tenant, actor = scheduled_database
    with factory() as db:
        first = ordinary(db, tenant, actor, "locked-first")
        case = enqueue_case_run(db, tenant)
        first_id, case_id = first.id, case.id
        db.commit()
    with factory() as locked, factory() as worker:
        locked.scalar(select(ScheduledJobRun).where(
            ScheduledJobRun.tenant_id == tenant,
            ScheduledJobRun.id == first_id,
        ).with_for_update())
        assert jobs.claim_next(worker, tenant).id == case_id
        worker.commit()
        assert locked.get(ScheduledJobRun, (tenant, first_id)).status == "pending"
    with factory() as worker:
        assert jobs.claim_next(worker, tenant).id == first_id


def test_alternation_preserves_due_retries_and_expired_claim_identity(
    session, business, scheduled_owner
):
    tenant = business.tenant.id
    expired = internal(session, tenant, "expired")
    expired.status = "running"
    expired.started_at = now() - timedelta(minutes=2)
    expired.lease_expires_at = now() - timedelta(seconds=1)
    expired.claim_token = "expired-token"
    expired.attempt_count = 1
    unresolved = internal(session, tenant, "unresolved")
    unresolved.status = "unresolved"
    future = ordinary(session, tenant, scheduled_owner.id, "future")
    future.status = "retry"
    future.next_attempt_at = now() + timedelta(hours=1)
    due = ordinary(session, tenant, scheduled_owner.id, "due")
    session.flush()
    assert jobs.claim_next(session, tenant).id == due.id
    recovered = jobs.claim_next(session, tenant)
    assert recovered.id == expired.id
    assert recovered.attempt_count == 2
    assert recovered.claim_token != "expired-token"
    assert jobs.claim_next(session, tenant) is None
    assert unresolved.status == "unresolved" and unresolved.started_at is None
    assert future.status == "retry" and future.attempt_count == 0
