"""A company stops keeping every run it ever made (spec 181 FR-005).

The job history was the one table in the schema that grew without any bound at
all. The development database held 81,710 `projections.refresh` rows against
38,454 source records — more than two rows of bookkeeping for every record
interpreted — and nothing ever removed one.

These tests are almost entirely about what is *kept*. Deleting rows is easy; the
value of this change is that it never deletes something a reader can still be
shown, and each of the things below is one somebody would otherwise lose.
"""

from datetime import timedelta

import pytest

from reality.db.core import now
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services.scheduled_jobs import cleanup_finished_runs


def _refresh(session, tenant_id, projection, *, age_days, status="succeeded"):
    """One finished refresh of one projection, as the scheduler leaves it."""
    finished = now() - timedelta(days=age_days)
    # The schema demands either a schedule or a request, and a refresh has no
    # schedule and no actor, so it invents a key nobody ever quotes back.
    serial = uid_counter()
    run = ScheduledJobRun(
        id=f"run_{projection}_{age_days}_{status}_{serial}",
        tenant_id=tenant_id,
        actor_id=None,
        job_type="projections.refresh",
        configuration={"arguments": {"names": [projection]}},
        request_id=f"projection_{serial}",
        request_fingerprint=f"{serial:064d}",
        status=status,
        created_at=finished,
        finished_at=finished
        if status in ("succeeded", "cancelled", "failed")
        else None,
    )
    session.add(run)
    return run


_counter = [0]


def uid_counter() -> int:
    _counter[0] += 1
    return _counter[0]


def _ids(session, tenant_id) -> set[str]:
    return set(
        session.scalars(
            ScheduledJobRun.__table__.select()
            .with_only_columns(ScheduledJobRun.id)
            .where(ScheduledJobRun.tenant_id == tenant_id)
        )
    )


def test_a_company_keeps_the_most_recent_runs_of_each_kind(session, business):
    """An age alone cannot bound this table, so a count does.

    A time-sensitive projection refreshes about twice a minute. Ninety days of
    that is a quarter of a million rows, which is why what is kept is counted
    rather than dated.
    """
    tenant = business.tenant.id
    for age in range(40, 10, -1):
        _refresh(session, tenant, "journal", age_days=age)
    session.flush()

    removed = cleanup_finished_runs(session, tenant_id=tenant, keep=20)
    session.flush()

    assert removed == 10
    assert len(_ids(session, tenant)) == 20


def test_each_projection_is_counted_on_its_own(session, business):
    """Twelve projections share a job type; twenty of them together would keep
    twenty of whichever refreshes most often and none of the quiet ones."""
    tenant = business.tenant.id
    for age in range(30, 10, -1):
        _refresh(session, tenant, "journal", age_days=age)
    for age in range(30, 27, -1):
        _refresh(session, tenant, "inventory", age_days=age)
    session.flush()

    cleanup_finished_runs(session, tenant_id=tenant, keep=5)
    session.flush()

    kept = list(
        session.scalars(
            ScheduledJobRun.__table__.select()
            .with_only_columns(ScheduledJobRun.configuration)
            .where(ScheduledJobRun.tenant_id == tenant)
        )
    )
    names = [row["arguments"]["names"][0] for row in kept]
    assert names.count("journal") == 5
    assert names.count("inventory") == 3, "a quiet projection keeps all it has"


def test_a_failure_is_never_forgotten(session, business):
    """A projection's freshness is read from its failures.

    `projection_state_expressions` takes the newest failed or unresolved run as
    `failed_at`, so forgetting one would make a company look like it never had a
    failure — the projection would report itself healthy on the strength of a
    deleted row.
    """
    tenant = business.tenant.id
    for age in range(40, 10, -1):
        _refresh(session, tenant, "journal", age_days=age, status="failed")
    session.flush()

    assert cleanup_finished_runs(session, tenant_id=tenant, keep=5) == 0
    assert len(_ids(session, tenant)) == 30


def test_an_unfinished_run_is_the_queue_and_stays(session, business):
    """The queue itself is never forgotten — and it cannot grow anyway.

    `uq_projection_run_unfinished` permits one unfinished refresh per projection
    per company (spec 181 FR-004), so waiting work is bounded by construction.
    Everything this cleanup is for is behind it, already finished.
    """
    tenant = business.tenant.id
    waiting = _refresh(session, tenant, "journal", age_days=40, status="pending")
    for age in range(39, 10, -1):
        _refresh(session, tenant, "journal", age_days=age)
    session.flush()

    cleanup_finished_runs(session, tenant_id=tenant, keep=1)
    session.flush()

    assert waiting.id in _ids(session, tenant)


def test_nothing_recent_is_taken_however_many_there_are(session, business):
    """A run somebody is looking at right now does not vanish under them."""
    tenant = business.tenant.id
    for _ in range(30):
        _refresh(session, tenant, "journal", age_days=0)
    session.flush()

    assert cleanup_finished_runs(session, tenant_id=tenant, keep=1) == 0
    assert len(_ids(session, tenant)) == 30


def test_a_run_an_analysis_points_at_is_kept(session, business, scheduled_owner):
    """Forgetting it would break a reference rather than free a row."""
    from reality.db.analytics import AnalysisRequest

    tenant = business.tenant.id
    runs = [_refresh(session, tenant, "journal", age_days=40 - n) for n in range(5)]
    session.flush()
    session.add(
        AnalysisRequest(
            id="anareq_probe",
            tenant_id=tenant,
            requested_by_user_id=scheduled_owner.id,
            question={"kind": "probe"},
            model_version="1",
            deferred_reason="too_large",
            run_id=runs[0].id,
            request_id="req_probe",
            expires_at=now() + timedelta(days=1),
        )
    )
    session.flush()

    cleanup_finished_runs(session, tenant_id=tenant, keep=1)
    session.flush()

    assert runs[0].id in _ids(session, tenant)


def test_the_batch_is_bounded(session, business):
    """A sweep has a budget; forgetting is done a little at a time."""
    tenant = business.tenant.id
    for age in range(60, 10, -1):
        _refresh(session, tenant, "journal", age_days=age)
    session.flush()

    assert cleanup_finished_runs(session, tenant_id=tenant, keep=1, limit=10) == 10


def test_an_impossible_batch_is_refused(session, business):
    with pytest.raises(ValueError, match="between 1 and 1000"):
        cleanup_finished_runs(session, tenant_id=business.tenant.id, limit=0)
    with pytest.raises(ValueError, match="at least one"):
        cleanup_finished_runs(session, tenant_id=business.tenant.id, keep=0)


def test_another_company_is_never_touched(session, business):
    from reality.services.core import create_tenant

    tenant = business.tenant.id
    other = create_tenant(session, "Zweite Firma", _commit=False).id
    for age in range(40, 10, -1):
        _refresh(session, tenant, "journal", age_days=age)
        _refresh(session, other, "journal", age_days=age)
    session.flush()

    cleanup_finished_runs(session, tenant_id=tenant, keep=1)
    session.flush()

    assert len(_ids(session, other)) == 30


def test_a_run_a_person_asked_for_keeps_its_request_key(
    session, business, scheduled_owner
):
    """Forgetting a manual run turns a retry into a second execution.

    `create_manual_run` answers a repeated `request_id` by handing back the row
    it made the first time. That row *is* the idempotency record, so it outlives
    the count — unlike a refresh, which invents a key nobody ever quotes back.
    """
    from reality.services.scheduled_jobs import create_manual_run

    tenant = business.tenant.id
    asked = create_manual_run(
        session,
        tenant,
        scheduled_owner.id,
        "invitations.cleanup",
        {},
        request_id="req_the_same_one_twice",
    )
    asked.status = "succeeded"
    asked.finished_at = now() - timedelta(days=40)
    # A newer one of the same kind, so the old one is past the count and would
    # be forgotten if being asked for by a person did not keep it.
    newer = create_manual_run(
        session,
        tenant,
        scheduled_owner.id,
        "invitations.cleanup",
        {},
        request_id="req_a_later_one",
    )
    newer.status = "succeeded"
    newer.finished_at = now() - timedelta(days=39)
    session.flush()

    cleanup_finished_runs(
        session, tenant_id=tenant, keep=0 + 1, minimum_age=timedelta()
    )
    session.flush()

    again = create_manual_run(
        session,
        tenant,
        scheduled_owner.id,
        "invitations.cleanup",
        {},
        request_id="req_the_same_one_twice",
    )
    assert again.id == asked.id, "the repeat was executed a second time"


def test_a_refresh_forgets_a_few_on_its_way_out(session, business):
    """The work that makes the history is the work that tidies it.

    A retention rule nobody calls is a function, not a policy. This holds the
    wiring: the handler that fills this table is the one that empties it, so the
    tidying keeps pace with the mess and an idle company pays nothing for it.
    """
    from reality.jobs.handlers.projections import ProjectionConfig, refresh
    from reality.jobs.registry import JobContext

    tenant = business.tenant.id
    for age in range(60, 10, -1):
        _refresh(session, tenant, "journal", age_days=age)
    session.flush()
    before = len(_ids(session, tenant))

    result = refresh(
        session,
        JobContext(tenant, None, "run_probe", None, now() + timedelta(seconds=30)),
        ProjectionConfig(names=["journal"]),
    )
    session.flush()

    assert result.counts["runs_forgotten"] == 20
    assert len(_ids(session, tenant)) == before - 20
