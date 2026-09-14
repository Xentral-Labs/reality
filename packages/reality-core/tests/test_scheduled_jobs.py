from datetime import timedelta

import pytest
from sqlalchemy import select

from reality.db.core import TenantMembership, now
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services import scheduled_jobs as jobs


def schedule(session, business, scheduled_owner, key="create"):
    return jobs.create_schedule(
        session,
        business.tenant.id,
        scheduled_owner.id,
        "invitations.cleanup",
        {},
        request_id=key,
        interval_seconds=12,
    )


def test_schedule_create_preview_replay_and_control(session, business, scheduled_owner):
    row = schedule(session, business, scheduled_owner)
    assert not row.enabled and row.next_run_at is None
    assert schedule(session, business, scheduled_owner).id == row.id
    assert (
        len(
            jobs.preview_schedule(
                session, business.tenant.id, scheduled_owner.id, row.id
            )
        )
        == 5
    )
    with pytest.raises(jobs.JobError):
        jobs.create_schedule(
            session,
            business.tenant.id,
            scheduled_owner.id,
            "invitations.cleanup",
            {},
            request_id="create",
            interval_seconds=60,
        )
    jobs.control_schedule(
        session, business.tenant.id, scheduled_owner.id, row.id, "resume", 1, "resume"
    )
    assert row.enabled and row.revision == 2
    jobs.control_schedule(
        session, business.tenant.id, scheduled_owner.id, row.id, "resume", 1, "resume"
    )
    assert row.revision == 2
    with pytest.raises(jobs.JobError):
        jobs.control_schedule(
            session, business.tenant.id, scheduled_owner.id, row.id, "pause", 1, "stale"
        )


def test_materialization_is_separate_and_coalesces(session, business, scheduled_owner):
    row = schedule(session, business, scheduled_owner)
    jobs.control_schedule(
        session, business.tenant.id, scheduled_owner.id, row.id, "resume", 1, "start"
    )
    row.next_run_at = now() - timedelta(hours=1)
    session.flush()
    assert jobs.materialize_due(session, business.tenant.id) == 1
    assert jobs.materialize_due(session, business.tenant.id) == 0
    run = session.scalar(
        select(ScheduledJobRun).where(ScheduledJobRun.tenant_id == business.tenant.id)
    )
    assert run.status == "pending" and run.attempt_count == 0
    assert row.next_run_at > now()
    assert jobs.claim_next(session, business.tenant.id).id == run.id
    assert run.status == "running"
    assert (
        jobs.execute_claim(session, business.tenant.id, run.id, run.claim_token)
        == "succeeded"
    )
    assert run.result == {"counts": {"invitations_removed": 0}, "references": []}


def test_pause_preserves_pending_and_edits_are_refused(
    session, business, scheduled_owner
):
    row = schedule(session, business, scheduled_owner)
    jobs.control_schedule(
        session, business.tenant.id, scheduled_owner.id, row.id, "resume", 1, "start"
    )
    row.next_run_at = now() - timedelta(seconds=1)
    jobs.materialize_due(session, business.tenant.id)
    jobs.control_schedule(
        session, business.tenant.id, scheduled_owner.id, row.id, "pause", 2, "pause"
    )
    assert jobs.claim_next(session, business.tenant.id) is None
    with pytest.raises(jobs.JobError):
        jobs.control_schedule(
            session,
            business.tenant.id,
            scheduled_owner.id,
            row.id,
            "update",
            3,
            "edit",
            {"interval_seconds": 60},
        )
    jobs.control_schedule(
        session, business.tenant.id, scheduled_owner.id, row.id, "resume", 3, "resume2"
    )
    assert jobs.claim_next(session, business.tenant.id) is not None


def test_manual_idempotency_scope_and_revocation(session, business, scheduled_owner):
    a = jobs.create_manual_run(
        session,
        business.tenant.id,
        scheduled_owner.id,
        "invitations.cleanup",
        {},
        request_id="manual",
    )
    assert (
        jobs.create_manual_run(
            session,
            business.tenant.id,
            scheduled_owner.id,
            "invitations.cleanup",
            {},
            request_id="manual",
        ).id
        == a.id
    )
    with pytest.raises(jobs.JobError):
        jobs.get_run(session, "foreign", scheduled_owner.id, a.id)
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    membership.status = "removed"
    session.flush()
    assert jobs.claim_next(session, business.tenant.id) is None
    assert a.status == "failed"
    assert a.last_error_code == "not_authorized"


def test_read_only_scoped_pagination(session, business, scheduled_owner):
    for i in range(3):
        jobs.create_manual_run(
            session,
            business.tenant.id,
            scheduled_owner.id,
            "invitations.cleanup",
            {},
            request_id=f"m{i}",
        )
    session.flush()
    first = jobs.list_runs(session, business.tenant.id, scheduled_owner.id, limit=2)
    second = jobs.list_runs(
        session,
        business.tenant.id,
        scheduled_owner.id,
        limit=2,
        cursor=first["next_cursor"],
    )
    assert first["has_more"] and not second["has_more"]
    assert len({r["id"] for r in first["items"] + second["items"]}) == 3
    assert not session.new and not session.dirty


def test_update_rejects_two_timing_sources(session, business, scheduled_owner):
    row = schedule(session, business, scheduled_owner)
    with pytest.raises(jobs.JobError):
        jobs.control_schedule(
            session,
            business.tenant.id,
            scheduled_owner.id,
            row.id,
            "update",
            1,
            "ambiguous",
            {"interval_seconds": 60, "cron_expression": "* * * * *"},
        )
    assert row.revision == 1 and row.interval_seconds == 12


def test_all_operator_boundaries_reject_foreign_scope(
    session, business, scheduled_owner
):
    row = schedule(session, business, scheduled_owner)
    actor = scheduled_owner.id
    operations = [
        lambda: jobs.create_schedule(
            session,
            "foreign",
            actor,
            "invitations.cleanup",
            {},
            request_id="x",
            interval_seconds=5,
        ),
        lambda: jobs.preview_schedule(session, "foreign", actor, row.id),
        lambda: jobs.control_schedule(
            session, "foreign", actor, row.id, "resume", 1, "x"
        ),
        lambda: jobs.create_manual_run(
            session, "foreign", actor, "invitations.cleanup", {}, request_id="x"
        ),
        lambda: jobs.cancel_queued_run(session, "foreign", actor, row.id, 1, "foreign-cancel"),
        lambda: jobs.get_run(session, "foreign", actor, "run_unknown"),
        lambda: jobs.list_runs(session, "foreign", actor),
        lambda: jobs.list_schedules(session, "foreign", actor),
    ]
    for operation in operations:
        with pytest.raises(jobs.JobError):
            operation()
    assert not row.enabled and row.revision == 1


def test_execution_boundaries_reject_foreign_records(
    session, business, scheduled_owner
):
    run = jobs.create_manual_run(
        session,
        business.tenant.id,
        scheduled_owner.id,
        "invitations.cleanup",
        {},
        request_id="scope",
    )
    claim = jobs.claim_next(session, business.tenant.id)
    assert jobs.materialize_due(session, "foreign") == 0
    assert jobs.claim_next(session, "foreign") is None
    assert not jobs.has_due_schedule(session, "foreign")
    with pytest.raises(jobs.JobError, match="not_found"):
        jobs.execute_claim(session, "foreign", run.id, claim.claim_token)
    with pytest.raises(jobs.JobError, match="not_found"):
        jobs.record_failure(session, "foreign", run.id, claim.claim_token, "failure")
    assert run.status == "running"


def test_catalog_discovers_only_bounded_identifiers(session, business):
    identifiers = jobs.tenant_catalog(session, limit=1)
    assert len(identifiers) == 1 and isinstance(identifiers[0], str)
    assert jobs.tenant_catalog(session, after="zzzz") == []


def test_paused_backlog_does_not_starve_manual_work(session, business, scheduled_owner):
    tenant, actor = business.tenant.id, scheduled_owner.id
    for index in range(101):
        row = schedule(session, business, scheduled_owner, key=f"paused-{index}")
        jobs.control_schedule(
            session, tenant, actor, row.id, "resume", 1, f"resume-{index}"
        )
        row.next_run_at = now() - timedelta(seconds=1)
        jobs.materialize_due(session, tenant)
        jobs.control_schedule(
            session, tenant, actor, row.id, "pause", 2, f"pause-{index}"
        )
    manual = jobs.create_manual_run(
        session, tenant, actor, "invitations.cleanup", {}, request_id="behind-paused"
    )
    assert jobs.claim_next(session, tenant).id == manual.id
