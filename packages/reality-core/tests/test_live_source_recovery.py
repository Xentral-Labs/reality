"""An infrastructure failure suspends a schedule; it never ends a live source.

Spec 256 FR-006, FR-007, FR-007a.
"""

from datetime import timedelta

from sqlalchemy import func, select

from reality.db.core import now
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services import scheduled_jobs as jobs


def running_schedule(session, business, scheduled_owner, key="recovery"):
    row = jobs.create_schedule(
        session,
        business.tenant.id,
        scheduled_owner.id,
        "invitations.cleanup",
        {},
        request_id=key,
        interval_seconds=60,
    )
    jobs.control_schedule(
        session,
        business.tenant.id,
        scheduled_owner.id,
        row.id,
        "resume",
        row.revision,
        f"{key}-resume",
    )
    row.next_run_at = now()
    session.flush()
    return row


def fail_occurrence(session, business, code, *, retryable=True):
    """Exhaust one occurrence's immediate attempts with the same failure."""
    assert jobs.materialize_due(session, business.tenant.id) == 1
    run = session.scalar(
        select(ScheduledJobRun).where(ScheduledJobRun.tenant_id == business.tenant.id)
    )
    for attempt in range(1, 4):
        claim = jobs.claim_next(session, business.tenant.id)
        assert claim is not None and claim.attempt_count == attempt
        status = jobs.record_failure(
            session,
            business.tenant.id,
            claim.id,
            claim.claim_token,
            code,
            retryable=retryable,
            detail=f"{code} detail",
        )
        if status != "retry":
            break
        claim.next_attempt_at = now() - timedelta(seconds=1)
        session.flush()
    return run


def test_database_failure_suspends_with_a_recovery_moment(
    session, business, scheduled_owner
):
    row = running_schedule(session, business, scheduled_owner)
    run = fail_occurrence(session, business, "database_error")
    session.refresh(row)
    assert run.status == "failed" and run.failure_detail == "database_error detail"
    assert row.enabled is False
    assert row.resume_after is not None
    waiting = (row.resume_after - now()).total_seconds()
    assert jobs.RECOVERY_MIN_SECONDS - 60 <= waiting <= jobs.RECOVERY_MAX_SECONDS


def test_business_failure_stops_the_schedule_for_good(
    session, business, scheduled_owner
):
    row = running_schedule(session, business, scheduled_owner)
    fail_occurrence(session, business, "handler_failed", retryable=False)
    session.refresh(row)
    assert row.enabled is False and row.resume_after is None
    assert jobs.materialize_due(session, business.tenant.id) == 0


def test_recovery_resumes_production_without_replaying_the_pause(
    session, business, scheduled_owner
):
    row = running_schedule(session, business, scheduled_owner)
    run = fail_occurrence(session, business, "database_error")
    # Five hours of outage: the schedule waited, it did not queue five hours of work.
    row.resume_after = now() - timedelta(seconds=1)
    run.status, run.finished_at = "succeeded", now()
    session.flush()
    assert jobs.materialize_due(session, business.tenant.id) == 1
    session.refresh(row)
    assert row.enabled is True and row.resume_after is None
    assert row.next_run_at > now()
    occurrences = session.scalar(
        select(func.count(ScheduledJobRun.id)).where(
            ScheduledJobRun.tenant_id == business.tenant.id
        )
    )
    assert occurrences == 2


def test_a_persisting_failure_suspends_again(session, business, scheduled_owner):
    row = running_schedule(session, business, scheduled_owner)
    run = fail_occurrence(session, business, "database_error")
    first = row.resume_after
    row.resume_after = now() - timedelta(seconds=1)
    run.status, run.finished_at = "succeeded", now()
    session.flush()
    jobs.materialize_due(session, business.tenant.id)
    fresh = session.scalar(
        select(ScheduledJobRun)
        .where(
            ScheduledJobRun.tenant_id == business.tenant.id,
            ScheduledJobRun.status == "pending",
        )
        .order_by(ScheduledJobRun.created_at.desc())
    )
    for _ in range(3):
        claim = jobs.claim_next(session, business.tenant.id)
        jobs.record_failure(
            session,
            business.tenant.id,
            claim.id,
            claim.claim_token,
            "database_error",
            retryable=True,
        )
        claim.next_attempt_at = now() - timedelta(seconds=1)
        session.flush()
    session.refresh(row)
    assert fresh is not None
    assert row.enabled is False and row.resume_after is not None
    assert row.resume_after != first


def test_an_owner_control_settles_the_suspension(session, business, scheduled_owner):
    row = running_schedule(session, business, scheduled_owner)
    fail_occurrence(session, business, "database_error")
    session.refresh(row)
    assert row.resume_after is not None
    jobs.control_schedule(
        session,
        business.tenant.id,
        scheduled_owner.id,
        row.id,
        "pause",
        row.revision,
        "owner-pause",
    )
    session.refresh(row)
    assert row.resume_after is None and row.enabled is False
    assert jobs.materialize_due(session, business.tenant.id) == 0
