from datetime import UTC, datetime, timedelta

import pytest

from reality.services import scheduled_jobs as jobs


@pytest.fixture
def clock(monkeypatch):
    value = [datetime.now(UTC) + timedelta(seconds=1)]
    monkeypatch.setattr(jobs, "now", lambda: value[0])
    return value


def start(session, business, owner):
    row = jobs.create_schedule(
        session,
        business.tenant.id,
        owner.id,
        "invitations.cleanup",
        {},
        request_id="initial",
        interval_seconds=60,
        initial_offsets_seconds=(0, 12, 24),
    )
    jobs.control_schedule(
        session, business.tenant.id, owner.id, row.id, "resume", row.revision, "start"
    )
    return row


def test_initial_offsets_then_regular_timing_and_frozen_inputs(
    session, business, scheduled_owner, clock
):
    row = start(session, business, scheduled_owner)
    anchor = clock[0]
    assert row.next_run_at == anchor
    assert jobs.preview_schedule(
        session, business.tenant.id, scheduled_owner.id, row.id
    ) == [anchor + timedelta(seconds=offset) for offset in (0, 12, 24, 84, 144)]
    frozen = []
    for offset, following in [(0, 12), (12, 24), (24, 84), (84, 144)]:
        clock[0] = anchor + timedelta(seconds=offset)
        assert jobs.materialize_due(session, business.tenant.id) == 1
        assert jobs.materialize_due(session, business.tenant.id) == 0
        run = jobs.claim_next(session, business.tenant.id)
        assert bool(run.configuration.get("initial_occurrence")) == (offset < 84)
        frozen.append(run)
        assert (
            jobs.execute_claim(session, business.tenant.id, run.id, run.claim_token)
            == "succeeded"
        )
        assert row.next_run_at == anchor + timedelta(seconds=following)
    session.expire_all()
    assert all(run.configuration.get("initial_occurrence") for run in frozen[:3])
    assert "initial_offsets_seconds" not in row.configuration


def test_delayed_start_coalesces_without_catchup(
    session, business, scheduled_owner, clock
):
    row = start(session, business, scheduled_owner)
    clock[0] += timedelta(seconds=70)
    assert jobs.materialize_due(session, business.tenant.id) == 1
    run = jobs.claim_next(session, business.tenant.id)
    assert (
        jobs.execute_claim(session, business.tenant.id, run.id, run.claim_token)
        == "succeeded"
    )
    assert jobs.materialize_due(session, business.tenant.id) == 0
    assert row.next_run_at > clock[0]
    assert "initial_offsets_seconds" not in row.configuration


@pytest.mark.parametrize("action", ["pause", "update"])
def test_control_discards_startup_and_resume_does_not_rearm(
    session, business, scheduled_owner, clock, action
):
    row = start(session, business, scheduled_owner)
    kwargs = {"changes": {"interval_seconds": 60}} if action == "update" else {}
    jobs.control_schedule(
        session,
        business.tenant.id,
        scheduled_owner.id,
        row.id,
        action,
        row.revision,
        "change",
        **kwargs,
    )
    jobs.control_schedule(
        session,
        business.tenant.id,
        scheduled_owner.id,
        row.id,
        "resume",
        row.revision,
        "again",
    )
    assert row.next_run_at == clock[0] + timedelta(seconds=60)
    assert "initial_offsets_seconds" not in row.configuration


@pytest.mark.parametrize(
    "offsets", [(0, 1), (12, 0), (-1,), (True,), tuple(range(0, 60, 5)), (0, 3601)]
)
def test_invalid_initial_offsets_are_rejected(
    session, business, scheduled_owner, offsets
):
    with pytest.raises(jobs.JobError, match="invalid_timing"):
        jobs.create_schedule(
            session,
            business.tenant.id,
            scheduled_owner.id,
            "invitations.cleanup",
            {},
            request_id="bad",
            interval_seconds=60,
            initial_offsets_seconds=offsets,
        )


def test_initial_retry_survives_pause_without_rearming_sequence(
    session, business, scheduled_owner, clock
):
    row = start(session, business, scheduled_owner)
    tenant = business.tenant.id
    assert jobs.materialize_due(session, tenant) == 1
    run = jobs.claim_next(session, tenant)
    run_id = run.id
    assert (
        jobs.record_failure(
            session, tenant, run.id, run.claim_token, "transient", retryable=True
        )
        == "retry"
    )
    jobs.control_schedule(
        session,
        tenant,
        scheduled_owner.id,
        row.id,
        "pause",
        row.revision,
        "pause-retry",
    )
    clock[0] += timedelta(seconds=35)
    assert jobs.claim_next(session, tenant) is None
    jobs.control_schedule(
        session,
        tenant,
        scheduled_owner.id,
        row.id,
        "resume",
        row.revision,
        "resume-retry",
    )
    retry = jobs.claim_next(session, tenant)
    assert retry.id == run_id and retry.configuration["initial_occurrence"] is True
    assert "initial_offsets_seconds" not in row.configuration
    assert (
        jobs.execute_claim(session, tenant, retry.id, retry.claim_token) == "succeeded"
    )


def test_initial_start_replay_and_capacity_do_not_advance_timing(
    session, business, scheduled_owner, clock, monkeypatch
):
    row = start(session, business, scheduled_owner)
    anchor = row.next_run_at
    same = jobs.create_schedule(
        session,
        business.tenant.id,
        scheduled_owner.id,
        "invitations.cleanup",
        {},
        request_id="initial",
        interval_seconds=60,
        initial_offsets_seconds=(0, 12, 24),
    )
    assert same.id == row.id
    jobs.control_schedule(
        session, business.tenant.id, scheduled_owner.id, row.id, "resume", 1, "start"
    )
    assert row.next_run_at == anchor
    monkeypatch.setattr(jobs, "QUEUE_LIMIT", 0)
    assert jobs.materialize_due(session, business.tenant.id) == 0
    assert row.next_run_at == anchor


def test_cron_cannot_have_initial_offsets(session, business, scheduled_owner):
    with pytest.raises(jobs.JobError, match="invalid_timing"):
        jobs.create_schedule(
            session,
            business.tenant.id,
            scheduled_owner.id,
            "invitations.cleanup",
            {},
            request_id="initial-cron",
            cron_expression="* * * * *",
            initial_offsets_seconds=(0, 12, 24),
        )
