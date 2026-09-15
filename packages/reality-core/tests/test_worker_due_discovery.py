"""Feature 201: the worker looks only where there is work, so it can look often."""

from datetime import timedelta

from reality.db.core import now
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services import scheduled_jobs as jobs


def _manual(session, tenant_id, owner, key):
    return jobs.create_manual_run(
        session, tenant_id, owner.id, "invitations.cleanup", {}, request_id=key
    )


def test_discovery_returns_only_tenants_with_claimable_work(
    session, business, scheduled_owner
):
    tenant = business.tenant.id
    assert jobs.due_tenants(session) == []
    assert tenant in jobs.tenant_catalog(session), "the scheduler still sees every tenant"
    run = _manual(session, tenant, scheduled_owner, "due-one")
    session.flush()
    assert jobs.due_tenants(session) == [tenant]
    claimed = jobs.claim_next(session, tenant)
    assert claimed.id == run.id
    assert jobs.due_tenants(session) == [], "a claimed run is nobody else's work"
    session.get(ScheduledJobRun, run.id).lease_expires_at = now() - timedelta(seconds=1)
    session.flush()
    assert jobs.due_tenants(session) == [tenant], "an expired lease is work again"
    recovered = jobs.claim_next(session, tenant)
    jobs.execute_claim(session, tenant, run.id, recovered.claim_token)
    session.flush()
    assert jobs.due_tenants(session) == []
    assert tenant in jobs.tenant_catalog(session)


def test_discovery_skips_a_run_whose_attempt_time_has_not_come(
    session, business, scheduled_owner
):
    tenant = business.tenant.id
    run = _manual(session, tenant, scheduled_owner, "later")
    run.next_attempt_at = now() + timedelta(minutes=5)
    session.flush()
    assert jobs.due_tenants(session) == []
    run.next_attempt_at = now()
    session.flush()
    assert jobs.due_tenants(session) == [tenant]


def test_discovery_pages_like_the_catalog(session, business, scheduled_owner):
    tenant = business.tenant.id
    _manual(session, tenant, scheduled_owner, "paged")
    session.flush()
    assert jobs.due_tenants(session, tenant) == [], "the cursor excludes what was seen"
    assert jobs.due_tenants(session, "", 1) == [tenant]
    for limit in (0, 101):
        try:
            jobs.due_tenants(session, "", limit)
        except jobs.JobError as error:
            assert error.code == "invalid_limit"
        else:  # pragma: no cover - the bound must hold
            raise AssertionError(f"limit {limit} was accepted")


def test_the_worker_sweep_visits_only_tenants_with_work(
    session, business, scheduled_owner, monkeypatch
):
    """The sweep's own discovery, not just the service beneath it."""
    from reality.jobs.runtime import ProcessLoop

    visited = []
    monkeypatch.setattr(
        jobs, "tenant_catalog", lambda *args, **kwargs: visited.append("catalog") or []
    )
    monkeypatch.setattr(jobs, "due_tenants", lambda *args, **kwargs: ["ten_with_work"])
    loop = ProcessLoop("worker")
    with_work = []
    monkeypatch.setattr(
        jobs, "claim_next", lambda _s, tenant_id, **kwargs: with_work.append(tenant_id)
    )
    loop.sweep(session.get_bind(), max_runs=1, max_seconds=1)
    assert with_work == ["ten_with_work"]
    assert visited == [], "an idle worker must not ask every tenant"
