from datetime import timedelta

import pytest
from sqlalchemy import select

from reality.db.core import SecurityAuditEvent, now
from reality.jobs.registry import JobDefinition, JobError, JobResult, definitions
from reality.services import scheduled_jobs as jobs


def manual(session, business, owner, key="recovery"):
    return jobs.create_manual_run(
        session, business.tenant.id, owner.id, "invitations.cleanup", {}, request_id=key
    )


def test_expired_claim_keeps_identity_and_fences_old_worker(
    session, business, scheduled_owner
):
    run = manual(session, business, scheduled_owner)
    claim = jobs.claim_next(session, business.tenant.id)
    old = claim.claim_token
    claim.lease_expires_at = now() - timedelta(seconds=1)
    session.flush()
    recovered = jobs.claim_next(session, business.tenant.id)
    assert recovered.id == run.id and recovered.attempt_count == 2
    assert recovered.claim_token != old
    with pytest.raises(JobError, match="stale_claim"):
        jobs.execute_claim(session, business.tenant.id, run.id, old)
    assert (
        jobs.record_failure(session, business.tenant.id, run.id, old, "old")
        == "running"
    )
    assert (
        jobs.execute_claim(session, business.tenant.id, run.id, recovered.claim_token)
        == "succeeded"
    )


def test_retry_budget_and_backoff(session, business, scheduled_owner):
    run = manual(session, business, scheduled_owner)
    for attempt in range(1, 4):
        claim = jobs.claim_next(session, business.tenant.id)
        assert claim.attempt_count == attempt
        status = jobs.record_failure(
            session,
            business.tenant.id,
            run.id,
            claim.claim_token,
            "transient",
            retryable=True,
        )
        if attempt < 3:
            assert status == "retry"
            assert run.next_attempt_at > now()
            run.next_attempt_at = now() - timedelta(seconds=1)
            session.flush()
        else:
            assert status == "failed"
    assert jobs.claim_next(session, business.tenant.id) is None


def test_handler_effect_rolls_back_with_failed_completion(
    session, business, scheduled_owner, monkeypatch
):
    from reality.jobs import registry

    definition = definitions()["invitations.cleanup"]
    marker = "scheduler_atomic_proof"

    def failed_handler(db, context, config):
        db.add(
            SecurityAuditEvent(
                id=marker, tenant_id=context.tenant_id, event_type="test"
            )
        )
        db.flush()
        raise JobError("simulated_failure")

    monkeypatch.setitem(
        registry._REGISTRY,
        definition.name,
        JobDefinition(
            definition.name,
            1,
            definition.config_model,
            definition.authorize,
            failed_handler,
        ),
    )
    run = manual(session, business, scheduled_owner)
    claim = jobs.claim_next(session, business.tenant.id)
    token = claim.claim_token
    with pytest.raises(JobError), session.begin_nested():
        jobs.execute_claim(session, business.tenant.id, run.id, token)
    assert (
        session.scalar(
            select(SecurityAuditEvent).where(
                SecurityAuditEvent.tenant_id == business.tenant.id,
                SecurityAuditEvent.id == marker,
            )
        )
        is None
    )
    session.refresh(run)
    assert run.status == "running"


def test_handler_cannot_commit(session, business, scheduled_owner, monkeypatch):
    from reality.jobs import registry

    definition = definitions()["invitations.cleanup"]

    def committing(db, context, config):
        db.commit()
        return JobResult()

    monkeypatch.setitem(
        registry._REGISTRY,
        definition.name,
        JobDefinition(
            definition.name,
            1,
            definition.config_model,
            definition.authorize,
            committing,
        ),
    )
    run = manual(session, business, scheduled_owner)
    claim = jobs.claim_next(session, business.tenant.id)
    with pytest.raises(JobError, match="commit_forbidden"):
        jobs.execute_claim(session, business.tenant.id, run.id, claim.claim_token)


def test_committed_effect_survives_lost_acknowledgement(scheduled_database):
    from test_scheduled_invitation_cleanup import invitation

    from reality.db.core import CompanyInvitation

    _engine, factory, tenant, actor = scheduled_database
    with factory.begin() as s:
        target = invitation(s, tenant, actor)
        target_id = target.id
        run = jobs.create_manual_run(
            s, tenant, actor, "invitations.cleanup", {}, request_id="lost-ack"
        )
        claim = jobs.claim_next(s, tenant)
        run_id, token = run.id, claim.claim_token
    with factory.begin() as s:
        assert jobs.execute_claim(s, tenant, run_id, token) == "succeeded"
    with factory.begin() as s:
        assert (
            jobs.record_failure(
                s, tenant, run_id, token, "child_exited", retryable=True
            )
            == "succeeded"
        )
        assert jobs.claim_next(s, tenant) is None
        assert s.get(CompanyInvitation, target_id) is None


def test_unresolved_run_pauses_and_requires_review(session, business, scheduled_owner):
    from test_scheduled_jobs import schedule

    tenant, actor = business.tenant.id, scheduled_owner.id
    row = schedule(session, business, scheduled_owner)
    jobs.control_schedule(session, tenant, actor, row.id, "resume", 1, "start")
    row.next_run_at = now() - timedelta(seconds=1)
    jobs.materialize_due(session, tenant)
    run = jobs.claim_next(session, tenant)
    assert (
        jobs.record_failure(
            session, tenant, run.id, run.claim_token, "unknown", uncertain=True
        )
        == "unresolved"
    )
    assert not row.enabled
    assert jobs.claim_next(session, tenant) is None
    with pytest.raises(JobError, match="unresolved_run"):
        jobs.control_schedule(
            session, tenant, actor, row.id, "resume", 2, "unsafe-resume"
        )


def test_pause_after_claim_defers_effect_and_preserves_snapshot(
    session, business, scheduled_owner
):
    from test_scheduled_jobs import schedule

    tenant, actor = business.tenant.id, scheduled_owner.id
    row = schedule(session, business, scheduled_owner)
    jobs.control_schedule(session, tenant, actor, row.id, "resume", 1, "start")
    row.next_run_at = now() - timedelta(seconds=1)
    jobs.materialize_due(session, tenant)
    run = jobs.claim_next(session, tenant)
    snapshot = (run.id, run.configuration.copy(), run.schedule_revision)
    token = run.claim_token
    jobs.control_schedule(session, tenant, actor, row.id, "pause", 2, "pause")
    assert jobs.execute_claim(session, tenant, run.id, token) == "retry"
    assert run.result is None and jobs.claim_next(session, tenant) is None
    jobs.control_schedule(session, tenant, actor, row.id, "resume", 3, "resume")
    claim = jobs.claim_next(session, tenant)
    assert (claim.id, claim.configuration, claim.schedule_revision) == snapshot
    assert (
        jobs.execute_claim(session, tenant, claim.id, claim.claim_token) == "succeeded"
    )


def test_unknown_version_is_terminal_and_other_work_remains_available(
    session, business, scheduled_owner
):
    run = manual(session, business, scheduled_owner, "bad-version")
    run.configuration = {"version": 999, "arguments": {}}
    good = manual(session, business, scheduled_owner, "good-version")
    assert jobs.claim_next(session, business.tenant.id) is None
    assert run.status == "failed" and run.last_error_code == "unsupported_job_version"
    claim = jobs.claim_next(session, business.tenant.id)
    assert claim.id == good.id
    assert (
        jobs.execute_claim(session, business.tenant.id, good.id, claim.claim_token)
        == "succeeded"
    )


def test_cancel_queued_occurrence_keeps_audit_and_refuses_claimed(session, business, scheduled_owner):
    tenant, actor = business.tenant.id, scheduled_owner.id
    schedule = jobs.create_schedule(session, tenant, actor, "invitations.cleanup", {}, request_id="cancel-schedule", interval_seconds=60)
    jobs.control_schedule(session, tenant, actor, schedule.id, "resume", schedule.revision, "enable-cancel")
    schedule.next_run_at = now() - timedelta(seconds=1)
    session.flush()
    jobs.materialize_due(session, tenant)
    from reality.db.scheduled_jobs import ScheduledJobRun
    run = session.scalar(select(ScheduledJobRun).where(ScheduledJobRun.tenant_id == tenant, ScheduledJobRun.schedule_id == schedule.id))
    jobs.cancel_queued_run(session, tenant, actor, schedule.id, schedule.revision, "cancel-queued")
    assert run.status == "cancelled" and not schedule.enabled
    assert run.finished_at is not None
    assert jobs.claim_next(session, tenant) is None
    jobs.control_schedule(session, tenant, actor, schedule.id, "resume", schedule.revision, "resume-cancel")
    schedule.next_run_at = now() - timedelta(seconds=1)
    session.flush()
    jobs.materialize_due(session, tenant)
    claim = jobs.claim_next(session, tenant)
    assert claim is not None
    with pytest.raises(JobError, match="unfinished_run"):
        jobs.cancel_queued_run(session, tenant, actor, schedule.id, schedule.revision, "refuse-running")
    assert schedule.enabled and claim.status == "running"


def test_handler_cannot_commit_root_from_nested_scope(session, business, scheduled_owner, monkeypatch):
    from reality.jobs import registry
    definition = definitions()["invitations.cleanup"]
    def committing(db, context, config):
        with db.begin_nested():
            db.commit()
        return JobResult()
    monkeypatch.setitem(registry._REGISTRY, definition.name, JobDefinition(definition.name, 1, definition.config_model, definition.authorize, committing))
    run = manual(session, business, scheduled_owner, "nested-commit")
    claim = jobs.claim_next(session, business.tenant.id)
    with pytest.raises(JobError, match="handler_commit_forbidden"):
        jobs.execute_claim(session, business.tenant.id, run.id, claim.claim_token)
    session.rollback()
