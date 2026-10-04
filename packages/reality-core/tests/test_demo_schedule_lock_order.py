"""Spec 146 / 361 FR-006: demo run locking cannot invert shared schedule locks."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from uuid import UUID

from conftest import seed_company
from sqlalchemy import event, select

from reality.db.core import now
from reality.db.scheduled_jobs import ScheduledJob, ScheduledJobRun
from reality.services import company_setup, demo_data
from reality.services import scheduled_jobs as jobs


def test_settlement_run_waits_for_shared_schedule_before_holding_its_own(
    scheduled_database, monkeypatch
):
    _, factory, _, actor = scheduled_database
    with factory() as db:
        tenant = company_setup.create_company(
            db,
            actor,
            "lock-order-company",
            "Lock Order",
            "sandbox",
            "empty",
            confirmed=True,
        )["tenant_id"]
        seed_company(db, tenant)
        schedule_ids = iter(UUID(int=value) for value in range(1, 100))
        monkeypatch.setattr(jobs, "uuid4", lambda: next(schedule_ids))
        preview = demo_data.preview(db, tenant, actor)
        connection = demo_data.connect(
            db,
            tenant,
            actor,
            "connect-lock-order",
            preview["fingerprint"],
            confirmed=True,
        )
        running = demo_data.control(
            db,
            tenant,
            actor,
            "start",
            connection["revision"],
            "start-lock-order",
            confirmed=True,
        )
        production_id = running["schedule_id"]
        settlement_id = demo_data._connection(db, tenant).settlement_schedule_id
        settlement = db.scalar(
            select(ScheduledJob).where(
                ScheduledJob.tenant_id == tenant, ScheduledJob.id == settlement_id
            )
        )
        settlement.next_run_at = now() - timedelta(seconds=1)
        db.commit()
        jobs.materialize_due(db, tenant)
        db.commit()
        run_id = db.scalar(
            select(ScheduledJobRun.id).where(
                ScheduledJobRun.tenant_id == tenant,
                ScheduledJobRun.schedule_id == settlement_id,
                ScheduledJobRun.status == "pending",
            )
        )
        assert run_id

    waiting_for_production = Event()

    def worker():
        with factory() as db:

            def observe(conn, cursor, statement, parameters, context, executemany):
                if (
                    "FOR UPDATE" in statement
                    and "scheduled_job." in statement
                    and production_id in str(parameters)
                ):
                    waiting_for_production.set()

            event.listen(db.connection(), "before_cursor_execute", observe)
            try:
                jobs._locked_claim(db, tenant, run_id)
                demo_data._locked(db, tenant)
            finally:
                db.rollback()

    with ThreadPoolExecutor(max_workers=1) as executor:
        with factory() as control:
            control.scalar(
                select(ScheduledJob)
                .where(
                    ScheduledJob.tenant_id == tenant, ScheduledJob.id == production_id
                )
                .with_for_update()
            )
            task = executor.submit(worker)
            try:
                assert waiting_for_production.wait(10), (
                    "Worker must reach the production schedule lock"
                )
                # A waiter must not hold settlement first: Pause must be able to
                # lock it while owning production without closing a lock cycle.
                control.scalar(
                    select(ScheduledJob)
                    .where(
                        ScheduledJob.tenant_id == tenant,
                        ScheduledJob.id == settlement_id,
                    )
                    .with_for_update(nowait=True)
                )
            finally:
                control.rollback()
        task.result(timeout=15)
