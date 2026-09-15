"""Feature 199: the creation request commits the company, the worker seeds it."""

import pytest
from conftest import seed_company
from sqlalchemy import func, select

from reality.db.core import Document, PlaygroundRun
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services import company_setup
from reality.services import scheduled_jobs as jobs

JOB_TYPE = "company_setup.initialize"


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
    assert session.get(PlaygroundRun, result["run_id"]).status == "active"
    receipt = company_setup.read_request(session, scheduled_owner.id, "deferred")
    assert receipt["status"] == "ready" and receipt["destination"]
    assert _documents(session, tenant) == 62


def test_repeated_request_queues_one_initialization(session, scheduled_owner):
    first = _create(session, scheduled_owner)
    again = _create(session, scheduled_owner)
    assert again["tenant_id"] == first["tenant_id"]
    assert again["status"] == "initializing"
    assert len(_queued(session, first["tenant_id"])) == 1


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
    assert _documents(session, result["tenant_id"]) == 62
    assert _work(session, result["tenant_id"]) == "succeeded"
    assert _documents(session, result["tenant_id"]) == 62


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
