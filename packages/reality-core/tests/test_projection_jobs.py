"""Background materialization preserves committed authority and read-only consumers."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from reality.db.core import ProjectionCheckpoint, ProjectionRow, now
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.jobs.registry import JobError
from reality.services import projections, scheduled_jobs
from reality.services.core import create_item, record_movement


def dispatch(session, tenant_id):
    from reality.services.projection_jobs import enqueue_due_projections

    return enqueue_due_projections(session, tenant_id)


def complete(session, tenant_id):
    run = scheduled_jobs.claim_next(session, tenant_id)
    assert run is not None
    assert (
        scheduled_jobs.execute_claim(session, tenant_id, run.id, run.claim_token)
        == "succeeded"
    )
    session.flush()
    return run


def test_bootstrap_coalesces_and_catches_later_events(session, business):
    tenant = business.tenant.id
    first = dispatch(session, tenant)
    assert first and first.actor_id is None
    assert dispatch(session, tenant) is None
    run = complete(session, tenant)
    assert run.id == first.id
    assert dispatch(session, tenant) is None
    record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "3",
        to_location_id=business.location.id,
    )
    second = dispatch(session, tenant)
    assert second and second.id != first.id
    complete(session, tenant)
    assert (
        projections.projection_rows(session, tenant, projections.INVENTORY)[0][
            "physical"
        ]
        == "3.0000"
    )


def test_refresh_is_transaction_bound_and_does_not_run_unrelated_builders(
    session, business, monkeypatch
):
    def unrelated(*args, **kwargs):
        pytest.fail("Inventory refresh derived financial data")

    monkeypatch.setattr(projections, "_build_financial_rows", unrelated)
    monkeypatch.setattr(projections, "_build_payment_rows", unrelated)
    projections.rebuild_projections(
        session, business.tenant.id, [projections.INVENTORY]
    )
    assert {
        c.projection_name
        for c in session.scalars(
            select(ProjectionCheckpoint).where(
                ProjectionCheckpoint.tenant_id == business.tenant.id
            )
        )
    } == {projections.INVENTORY}


def test_time_only_refresh_is_scoped_and_archive_stops_dispatch(
    session, business, monkeypatch
):
    tenant = business.tenant.id
    dispatch(session, tenant)
    complete(session, tenant)
    later = now() + timedelta(seconds=61)
    monkeypatch.setattr(projections, "now", lambda: later)
    run = dispatch(session, tenant)
    assert set(run.configuration["arguments"]["names"]) == set(
        projections.TIME_SENSITIVE_PROJECTIONS
    )
    business.tenant.archived_at = now()
    session.flush()
    assert scheduled_jobs.claim_next(session, tenant) is None


def test_internal_job_cannot_be_requested_as_user_job(
    session, business, scheduled_owner
):
    with pytest.raises(JobError):
        scheduled_jobs.create_manual_run(
            session,
            business.tenant.id,
            scheduled_owner.id,
            "projections.refresh",
            {"names": ["inventory"]},
            request_id="forbidden",
        )
    with pytest.raises(JobError):
        scheduled_jobs.create_schedule(
            session,
            business.tenant.id,
            scheduled_owner.id,
            "projections.refresh",
            {"names": ["inventory"]},
            request_id="forbidden-schedule",
            interval_seconds=5,
        )


def test_stored_reads_never_refresh_or_write_and_report_initial_state(
    session, business, monkeypatch
):
    def forbidden(*args, **kwargs):
        pytest.fail("Read invoked materialization")

    monkeypatch.setattr(projections, "rebuild_projections", forbidden)
    assert (
        projections.projection_rows(session, business.tenant.id, projections.INVENTORY)
        == []
    )
    snapshot = projections.projection_snapshot(
        session, business.tenant.id, projections.INVENTORY
    )
    assert snapshot["items"] == []
    assert snapshot["metadata"]["state"] == "uninitialized"
    assert (
        list(
            session.scalars(
                select(ProjectionRow).where(
                    ProjectionRow.tenant_id == business.tenant.id
                )
            )
        )
        == []
    )


def test_pending_snapshot_retains_completed_rows_and_is_tenant_scoped(
    session, business
):
    tenant = business.tenant.id
    dispatch(session, tenant)
    complete(session, tenant)
    ready = projections.projection_snapshot(session, tenant, projections.INVENTORY)
    assert ready["metadata"]["state"] == "ready"
    create_item(session, tenant, "NEW", "New item")
    old = projections.projection_snapshot(session, tenant, projections.INVENTORY)
    assert old["items"] == ready["items"]
    assert old["metadata"]["state"] == "pending"
    assert (
        old["metadata"]["target_event_sequence"]
        > old["metadata"]["processed_event_sequence"]
    )
    dispatch(session, tenant)
    complete(session, tenant)
    assert (
        len(
            projections.projection_snapshot(session, tenant, projections.INVENTORY)[
                "items"
            ]
        )
        == 2
    )
    from reality.services.core import NotFound

    with pytest.raises(NotFound):
        projections.projection_snapshot(session, "absent-tenant", projections.INVENTORY)


def test_queue_cap_defers_without_advancing_checkpoint(session, business, monkeypatch):
    monkeypatch.setattr(scheduled_jobs, "QUEUE_LIMIT", 0)
    assert dispatch(session, business.tenant.id) is None
    assert (
        session.scalar(
            select(ProjectionCheckpoint).where(
                ProjectionCheckpoint.tenant_id == business.tenant.id
            )
        )
        is None
    )
    assert (
        session.scalar(
            select(ScheduledJobRun).where(
                ScheduledJobRun.tenant_id == business.tenant.id
            )
        )
        is None
    )


def test_real_scheduler_and_worker_publish_without_a_user_actor(scheduled_database):
    from reality.jobs.runtime import ProcessLoop

    engine, factory, tenant, _actor = scheduled_database
    with factory() as db:
        create_item(db, tenant, "AUTO", "Automatic inventory")
    assert (
        ProcessLoop("scheduler", tenant_id=tenant).sweep(
            engine, max_runs=1, max_seconds=25
        )["materialized"]
        == 1
    )
    assert (
        ProcessLoop("worker", tenant_id=tenant).sweep(
            engine, max_runs=1, max_seconds=25
        )["succeeded"]
        == 1
    )
    with factory() as db:
        response = projections.projection_snapshot(db, tenant, projections.INVENTORY)
        assert response["metadata"]["state"] == "ready"
        assert response["items"][0]["sku"] == "AUTO"
        run = db.scalar(
            select(ScheduledJobRun).where(ScheduledJobRun.tenant_id == tenant)
        )
        assert run.actor_id is None and run.status == "succeeded"


def test_repeatable_publication_does_not_swallow_concurrent_business_event(
    scheduled_database, monkeypatch
):
    """A writer commits mid-build; its event stays ahead of the published snapshot."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from sqlalchemy.orm import Session

    engine, factory, tenant, _actor = scheduled_database
    with factory() as db:
        create_item(db, tenant, "BEFORE", "Before snapshot")
    started, release = Event(), Event()
    original = projections.derive_projection_rows

    def paused(db, tenant_id, name):
        rows = original(db, tenant_id, name)
        started.set()
        assert release.wait(10)
        return rows

    monkeypatch.setattr(projections, "derive_projection_rows", paused)

    def publish():
        with (
            Session(engine.execution_options(isolation_level="REPEATABLE READ")) as db,
            db.begin(),
        ):
            projections.rebuild_projections(db, tenant, [projections.INVENTORY])

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(publish)
        try:
            assert started.wait(10)
            with factory() as db:
                create_item(db, tenant, "DURING", "Committed during calculation")
        finally:
            release.set()
        future.result(timeout=10)
    monkeypatch.setattr(projections, "derive_projection_rows", original)
    with factory() as db:
        before = projections.projection_snapshot(db, tenant, projections.INVENTORY)
        assert [row["sku"] for row in before["items"]] == ["BEFORE"]
        assert before["metadata"]["state"] == "pending"
        projections.rebuild_projections(db, tenant, [projections.INVENTORY])
        db.commit()
        assert (
            len(
                projections.projection_snapshot(db, tenant, projections.INVENTORY)[
                    "items"
                ]
            )
            == 2
        )


def test_rolled_back_event_and_failed_publication_leave_no_progress(
    scheduled_database, monkeypatch
):
    from reality.services.core import emit_business_event

    _engine, factory, tenant, _actor = scheduled_database
    with factory() as db:
        create_item(db, tenant, "RETAINED", "Retained item")
        projections.rebuild_projections(db, tenant, [projections.INVENTORY])
        db.commit()
        before = projections.projection_snapshot(db, tenant, projections.INVENTORY)
        emit_business_event(
            db, tenant, "item.updated", "item", before["items"][0]["item_id"], {}
        )
        db.flush()
        db.rollback()
        assert (
            projections.projection_snapshot(db, tenant, projections.INVENTORY) == before
        )
    with factory() as db, db.begin():
        dispatch(db, tenant)
    with factory() as db, db.begin():
        run = scheduled_jobs.claim_next(db, tenant)
        run_id, token = run.id, run.claim_token
    original = projections._replace_rows

    def fail_after_write(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("injected failure after cache write")

    monkeypatch.setattr(projections, "_replace_rows", fail_after_write)
    with pytest.raises(RuntimeError), factory() as db, db.begin():
        scheduled_jobs.execute_claim(db, tenant, run_id, token)
    with factory() as db:
        assert (
            projections.projection_snapshot(db, tenant, projections.INVENTORY) == before
        )
        assert (
            db.scalar(
                select(ScheduledJobRun.status).where(
                    ScheduledJobRun.tenant_id == tenant, ScheduledJobRun.id == run_id
                )
            )
            == "running"
        )


def test_failed_job_retains_data_and_requires_explicit_recovery(session, business):
    tenant = business.tenant.id
    dispatch(session, tenant)
    complete(session, tenant)
    create_item(session, tenant, "LATER", "Later")
    dispatch(session, tenant)
    run = scheduled_jobs.claim_next(session, tenant)
    scheduled_jobs.record_failure(
        session, tenant, run.id, run.claim_token, "handler_failed", retryable=False
    )
    assert (
        projections.projection_snapshot(session, tenant, projections.INVENTORY)[
            "metadata"
        ]["state"]
        == "failed"
    )
    assert dispatch(session, tenant) is None
    projections.rebuild_projections(
        session, tenant, projections.MATERIALIZED_PROJECTIONS, force=True
    )
    assert (
        projections.projection_snapshot(session, tenant, projections.INVENTORY)[
            "metadata"
        ]["state"]
        == "ready"
    )
    create_item(session, tenant, "RECOVERED", "Recovered")
    assert dispatch(session, tenant) is not None


def test_unknown_events_invalidate_and_known_unrelated_events_do_not(session, business):
    from reality.services.core import emit_business_event

    tenant = business.tenant.id
    projections.rebuild_projections(
        session, tenant, projections.MATERIALIZED_PROJECTIONS
    )
    emit_business_event(
        session, tenant, "price_list.updated", "price_list", "example", {}
    )
    session.flush()
    assert (
        projections.projection_snapshot(session, tenant, projections.INVENTORY)[
            "metadata"
        ]["state"]
        == "ready"
    )
    emit_business_event(session, tenant, "future.unknown", "item", business.item.id, {})
    session.flush()
    assert (
        projections.projection_snapshot(session, tenant, projections.INVENTORY)[
            "metadata"
        ]["state"]
        == "pending"
    )


def test_snapshot_data_and_metadata_are_one_read_statement(session, business):
    from sqlalchemy import event

    from reality.web.read_models import projection_page

    projections.rebuild_projections(
        session, business.tenant.id, [projections.INVENTORY]
    )
    statements = []

    def capture(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement)

    event.listen(session.bind, "before_cursor_execute", capture)
    try:
        result = projection_page(
            session, business.tenant.id, projections.INVENTORY, with_metadata=True
        )
        assert result["metadata"]["state"] == "ready"
        assert len(result["items"]) == result["page"]["total"] == 1
        assert len(statements) == 1
        assert statements[0].lstrip().upper().startswith("WITH")
    finally:
        event.remove(session.bind, "before_cursor_execute", capture)


def test_projection_services_keep_other_tenant_untouched(session, business):
    from reality.jobs.handlers.projections import ProjectionConfig, authorize
    from reality.jobs.registry import JobContext
    from reality.services.core import create_tenant
    from reality.services.projection_jobs import enqueue_due_projections

    local = business.tenant.id
    foreign = create_tenant(session, "Foreign projection scope").id
    create_item(session, foreign, "FOREIGN", "Private foreign item")
    projections.rebuild_projections(session, foreign, [projections.INVENTORY])
    before = projections.projection_snapshot(session, foreign, projections.INVENTORY)
    run = enqueue_due_projections(session, local)
    assert run.tenant_id == local
    complete(session, local)
    assert (
        projections.projection_snapshot(session, foreign, projections.INVENTORY)
        == before
    )
    assert all(
        row["sku"] != "FOREIGN"
        for row in projections.projection_snapshot(
            session, local, projections.INVENTORY
        )["items"]
    )
    with pytest.raises(JobError, match="not_authorized"):
        authorize(
            session,
            JobContext(foreign, None, run.id, None, now() + timedelta(seconds=30)),
            ProjectionConfig(names=["inventory"]),
        )


def test_frequent_schedules_cannot_starve_projection_dispatch(scheduled_database):
    from reality.db.scheduled_jobs import ScheduledJob
    from reality.jobs.runtime import ProcessLoop

    engine, factory, tenant, actor = scheduled_database
    with factory() as db, db.begin():
        schedule = scheduled_jobs.create_schedule(
            db,
            tenant,
            actor,
            "invitations.cleanup",
            {},
            request_id="frequent",
            interval_seconds=5,
        )
        scheduled_jobs.control_schedule(
            db, tenant, actor, schedule.id, "resume", 1, "start"
        )
        schedule.next_run_at = now() - timedelta(seconds=1)
        schedule_id = schedule.id
    scheduler = ProcessLoop("scheduler", tenant_id=tenant)
    scheduler.sweep(engine, max_runs=1, max_seconds=25)
    ProcessLoop("worker", tenant_id=tenant).sweep(engine, max_runs=1, max_seconds=25)
    with factory() as db, db.begin():
        db.scalar(
            select(ScheduledJob).where(
                ScheduledJob.tenant_id == tenant, ScheduledJob.id == schedule_id
            )
        ).next_run_at = now() - timedelta(seconds=1)
    scheduler.sweep(engine, max_runs=1, max_seconds=25)
    with factory() as db:
        assert (
            db.scalar(
                select(ScheduledJobRun.id).where(
                    ScheduledJobRun.tenant_id == tenant,
                    ScheduledJobRun.job_type == "projections.refresh",
                )
            )
            is not None
        )


def test_read_cannot_flush_unrelated_pending_cache_writes(session, business):
    from reality.db.core import uid
    from reality.web.read_models import projection_page

    pending = ProjectionRow(
        id=uid("prj"),
        tenant_id=business.tenant.id,
        projection_name="inventory",
        record_key="pending-only",
        payload='{"item_id":"not-persisted"}',
        projection_version=4,
        source_event_sequence=0,
    )
    session.add(pending)
    assert projections.projection_rows(session, business.tenant.id, "inventory") == []
    assert (
        projections.projection_snapshot(session, business.tenant.id, "inventory")[
            "items"
        ]
        == []
    )
    assert (
        projection_page(session, business.tenant.id, "inventory", with_metadata=True)[
            "items"
        ]
        == []
    )
    assert pending in session.new
    session.expunge(pending)


def test_old_version_and_missing_checkpoint_bootstrap_without_new_event(
    session, business
):
    from sqlalchemy import delete

    tenant = business.tenant.id
    dispatch(session, tenant)
    complete(session, tenant)
    checkpoint = session.scalar(
        select(ProjectionCheckpoint).where(
            ProjectionCheckpoint.tenant_id == tenant,
            ProjectionCheckpoint.projection_name == projections.INVENTORY,
        )
    )
    checkpoint.projection_version -= 1
    session.execute(
        delete(ProjectionCheckpoint).where(
            ProjectionCheckpoint.tenant_id == tenant,
            ProjectionCheckpoint.projection_name == projections.PAYMENTS,
        )
    )
    session.flush()
    run = dispatch(session, tenant)
    assert set(run.configuration["arguments"]["names"]) == {
        projections.INVENTORY,
        projections.PAYMENTS,
    }
    complete(session, tenant)
    for name in (projections.INVENTORY, projections.PAYMENTS):
        assert (
            projections.projection_snapshot(session, tenant, name)["metadata"]["state"]
            == "ready"
        )


def test_retry_keeps_internal_identity_and_publishes_once(session, business):
    tenant = business.tenant.id
    first = dispatch(session, tenant)
    claim = scheduled_jobs.claim_next(session, tenant)
    scheduled_jobs.record_failure(
        session, tenant, claim.id, claim.claim_token, "handler_failed", retryable=True
    )
    assert dispatch(session, tenant) is None
    claim.next_attempt_at = now() - timedelta(seconds=1)
    session.flush()
    completed = complete(session, tenant)
    assert completed.id == first.id and completed.actor_id is None
    assert dispatch(session, tenant) is None


def test_commitment_hold_invalidates_supply_demand(session, business):
    from reality.services.core import create_commitment, hold_commitment

    tenant = business.tenant.id
    commitment = create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "2",
        "2026-09-10",
    )
    projections.rebuild_projections(session, tenant, [projections.ITEM_SUPPLY_DEMAND])
    hold_commitment(session, tenant, commitment.id, "manual_review")
    assert (
        projections.projection_snapshot(
            session, tenant, projections.ITEM_SUPPLY_DEMAND
        )["metadata"]["state"]
        == "pending"
    )
