"""Feature 199: the creation request commits the company, the worker seeds it."""

import pytest
from conftest import record_by_id, seed_company
from sqlalchemy import func, select

from reality.db.core import Document, PlaygroundRun, ProjectionCheckpoint, ProjectionRow
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services import company_setup
from reality.services import scheduled_jobs as jobs
from reality.services.projections import OPEN_FINANCIAL_ITEMS

JOB_TYPE = "company_setup.initialize"
INTERNATIONAL_V10_DOCUMENT_COUNT = 108


def _create(session, owner, key="deferred", content="international_demo"):
    return company_setup.create_company(
        session,
        owner.id,
        key,
        "Harbor Supply",
        "sandbox",
        content,
        confirmed=True,
    )


def _queued(session, tenant_id):
    return list(
        session.scalars(
            select(ScheduledJobRun).where(
                ScheduledJobRun.tenant_id == tenant_id,
                ScheduledJobRun.job_type == JOB_TYPE,
            )
        )
    )


def _documents(session, tenant_id):
    return session.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.tenant_id == tenant_id)
    )


def _work(session, tenant_id):
    run = jobs.claim_next(session, tenant_id)
    assert run is not None, "the queued initialization must be claimable"
    return jobs.execute_claim(session, tenant_id, run.id, run.claim_token)


def test_creation_answers_before_the_profile_is_seeded(session, scheduled_owner):
    result = _create(session, scheduled_owner)
    assert result["status"] == "initializing"
    assert result["destination"] is None
    tenant = result["tenant_id"]
    assert _documents(session, tenant) == 0
    assert len(_queued(session, tenant)) == 1
    assert _work(session, tenant) == "succeeded"
    assert record_by_id(session, PlaygroundRun, result["run_id"]).status == "active"
    receipt = company_setup.read_request(session, scheduled_owner.id, "deferred")
    assert receipt["status"] == "ready" and receipt["destination"]
    assert _documents(session, tenant) == INTERNATIONAL_V10_DOCUMENT_COUNT
    checkpoint = session.scalar(
        select(ProjectionCheckpoint).where(
            ProjectionCheckpoint.tenant_id == tenant,
            ProjectionCheckpoint.projection_name == OPEN_FINANCIAL_ITEMS,
        )
    )
    assert checkpoint is not None and checkpoint.status == "ready"
    assert (
        session.scalar(
            select(func.count())
            .select_from(ProjectionRow)
            .where(
                ProjectionRow.tenant_id == tenant,
                ProjectionRow.projection_name == OPEN_FINANCIAL_ITEMS,
            )
        )
        == 34
    )


def test_repeated_request_queues_one_initialization(session, scheduled_owner):
    first = _create(session, scheduled_owner)
    again = _create(session, scheduled_owner)
    assert again["tenant_id"] == first["tenant_id"]
    assert again["status"] == "initializing"
    assert len(_queued(session, first["tenant_id"])) == 1


def test_failed_worker_setup_is_retryable_and_rolls_back_for_the_next_attempt(
    session, scheduled_owner, monkeypatch
):
    from reality.services import demo_profile

    result = _create(session, scheduled_owner, key="worker-retry")
    original = demo_profile.seed_profile

    def fail(*args, **kwargs):
        raise RuntimeError("injected setup interruption")

    monkeypatch.setattr(demo_profile, "seed_profile", fail)
    with pytest.raises(jobs.JobError) as raised, session.begin_nested():
        _work(session, result["tenant_id"])
    assert raised.value.code == "setup_profile_incomplete"
    assert raised.value.retryable is True
    assert (
        record_by_id(session, PlaygroundRun, result["run_id"]).status == "initializing"
    )
    assert _documents(session, result["tenant_id"]) == 0

    monkeypatch.setattr(demo_profile, "seed_profile", original)
    assert _work(session, result["tenant_id"]) == "succeeded"
    assert record_by_id(session, PlaygroundRun, result["run_id"]).status == "active"


def test_failed_worker_live_start_is_retryable_and_keeps_setup_incomplete(
    session, scheduled_owner, monkeypatch
):
    from reality.services import demo_data

    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "worker-live-retry",
        "Live Retry",
        "sandbox",
        "international_demo",
        live_simulation=True,
        confirmed=True,
    )

    def fail(*args, **kwargs):
        raise RuntimeError("injected live start interruption")

    monkeypatch.setattr(demo_data, "control", fail)
    with pytest.raises(jobs.JobError) as raised, session.begin_nested():
        _work(session, result["tenant_id"])
    assert raised.value.code == "setup_live_incomplete"
    assert raised.value.retryable is True
    run = record_by_id(session, PlaygroundRun, result["run_id"])
    assert run.status == "initializing"
    assert run.initialization_progress.get("live_setup_complete") is not True
    assert _documents(session, result["tenant_id"]) == 0


def test_failed_initial_calculation_is_retryable_and_keeps_setup_atomic(
    session, scheduled_owner, monkeypatch
):
    from reality.services import projections

    result = _create(session, scheduled_owner, key="calculation-retry")

    def fail(*args, **kwargs):
        raise RuntimeError("injected initial calculation interruption")

    monkeypatch.setattr(projections, "rebuild_projections", fail)
    with pytest.raises(jobs.JobError) as raised, session.begin_nested():
        _work(session, result["tenant_id"])
    assert raised.value.code == "setup_calculation_incomplete"
    assert raised.value.retryable is True
    assert (
        record_by_id(session, PlaygroundRun, result["run_id"]).status == "initializing"
    )
    assert _documents(session, result["tenant_id"]) == 0


def test_seeding_twice_changes_nothing(session, scheduled_owner):
    result = _create(session, scheduled_owner)
    tenant = result["tenant_id"]
    _work(session, tenant)
    seeded = _documents(session, tenant)
    repeated = jobs.create_manual_run(
        session,
        tenant,
        scheduled_owner.id,
        JOB_TYPE,
        {"run_id": result["run_id"]},
        request_id="second-initialization",
    )
    assert (
        jobs.execute_claim(
            session, tenant, repeated.id, jobs.claim_next(session, tenant).claim_token
        )
        == "succeeded"
    )
    assert _documents(session, tenant) == seeded


def test_initialization_refuses_a_foreign_actor(session, scheduled_owner, business):
    from reality.db.core import AppUser, now, uid

    result = _create(session, scheduled_owner)
    stranger = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(stranger)
    session.flush()
    with pytest.raises(jobs.JobError):
        jobs.create_manual_run(
            session,
            result["tenant_id"],
            stranger.id,
            JOB_TYPE,
            {"run_id": result["run_id"]},
            request_id="foreign",
        )
    with pytest.raises(jobs.JobError):
        jobs.create_manual_run(
            session,
            result["tenant_id"],
            scheduled_owner.id,
            JOB_TYPE,
            {"run_id": "pgr_absent"},
            request_id="absent-run",
        )


def test_explicit_retry_completes_without_a_worker(session, scheduled_owner):
    result = _create(session, scheduled_owner)
    retried = company_setup.retry_request(
        session, scheduled_owner.id, "deferred", confirmed=True
    )
    assert retried["status"] == "ready"
    assert retried["tenant_id"] == result["tenant_id"]
    assert _documents(session, result["tenant_id"]) == INTERNATIONAL_V10_DOCUMENT_COUNT
    assert _work(session, result["tenant_id"]) == "succeeded"
    assert _documents(session, result["tenant_id"]) == INTERNATIONAL_V10_DOCUMENT_COUNT


def test_a_small_profile_is_still_ready_when_the_request_answers(
    session, scheduled_owner
):
    """Only the international profile is worth deferring."""
    result = _create(session, scheduled_owner, key="empty", content="empty")
    assert result["status"] == "ready" and result["destination"]
    assert _queued(session, result["tenant_id"]) == []
    baseline = _create(session, scheduled_owner, key="baseline")
    assert seed_company(session, baseline["tenant_id"]) == "succeeded"
    execution = company_setup.create_execution(
        session, scheduled_owner.id, "baseline", "practice", "Practice", confirmed=True
    )
    assert execution["status"] == "ready" and execution["destination"]
    assert _queued(session, execution["tenant_id"]) == []


def test_claim_refuses_an_initialization_whose_company_was_archived(
    session, scheduled_owner
):
    """Authorization is revalidated at claim, not only at enqueue."""
    from reality.db.core import Tenant, now

    result = _create(session, scheduled_owner)
    tenant = result["tenant_id"]
    assert jobs.claim_next(session, tenant) is not None
    session.rollback()
    session.get(Tenant, tenant).archived_at = now()
    session.flush()
    assert jobs.claim_next(session, tenant) is None
    assert _documents(session, tenant) == 0


def test_setup_job_ownership_is_not_weaker_than_the_shared_rule(
    session, scheduled_owner, business
):
    """The job type's own rule must hold wherever the queue asks for ownership."""
    from reality.db.core import AppUser, now, uid
    from reality.services.scheduled_jobs import _owner

    result = _create(session, scheduled_owner)
    stranger = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(stranger)
    session.flush()
    _owner(session, result["tenant_id"], scheduled_owner.id, JOB_TYPE)
    for tenant_id, actor in [
        (result["tenant_id"], stranger.id),
        (result["tenant_id"], None),
        (business.tenant.id, scheduled_owner.id),
    ]:
        with pytest.raises(jobs.JobError):
            _owner(session, tenant_id, actor, JOB_TYPE)


def test_receipt_says_whether_anyone_is_preparing_the_company(session, scheduled_owner):
    """Feature 201: queued and being prepared are different answers."""
    result = _create(session, scheduled_owner)
    assert result["preparation"] == "queued"
    read = company_setup.read_request(session, scheduled_owner.id, "deferred")
    assert read["preparation"] == "queued"
    run = jobs.claim_next(session, result["tenant_id"])
    assert (
        company_setup.read_request(session, scheduled_owner.id, "deferred")[
            "preparation"
        ]
        == "preparing"
    )
    jobs.execute_claim(session, result["tenant_id"], run.id, run.claim_token)
    finished = company_setup.read_request(session, scheduled_owner.id, "deferred")
    assert finished["status"] == "ready" and finished["preparation"] is None


def test_receipt_explains_an_automatic_setup_retry(session, scheduled_owner):
    result = _create(session, scheduled_owner, key="retry-progress")
    run = jobs.claim_next(session, result["tenant_id"])
    assert (
        jobs.record_failure(
            session,
            result["tenant_id"],
            run.id,
            run.claim_token,
            "setup_incomplete",
            retryable=True,
        )
        == "retry"
    )

    read = company_setup.read_request(session, scheduled_owner.id, "retry-progress")
    assert read["preparation"] == "retrying"
    assert read["preparation_attempt"] == 2
    assert read["preparation_max_attempts"] == 3
    assert read["preparation_next_attempt_at"]

    run.status = "failed"
    run.attempt_count = 3
    session.flush()
    exhausted = company_setup.read_request(
        session, scheduled_owner.id, "retry-progress"
    )
    assert exhausted["status"] == "initialization_failed"
    assert exhausted["error_code"] == "setup_incomplete"
    assert exhausted["preparation"] is None


def test_a_company_nobody_prepares_reports_no_preparation(session, scheduled_owner):
    result = _create(session, scheduled_owner, key="empty", content="empty")
    assert result["status"] == "ready" and result["preparation"] is None
