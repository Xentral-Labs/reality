from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_scheduler_migration_roundtrip(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0044_playground_returns_merge")
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        assert {"scheduled_job", "scheduled_job_run"} <= set(
            inspect(engine).get_table_names()
        )
        command.downgrade(config, "0044_playground_returns_merge")
        assert "scheduled_job" not in inspect(engine).get_table_names()
        command.upgrade(config, "head")
        assert "scheduled_job_run" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_occurrence_manual_and_unfinished_constraints(
    session, business, scheduled_owner
):
    from datetime import timedelta
    from uuid import uuid4

    import pytest
    from sqlalchemy.exc import IntegrityError

    from reality.db.core import now
    from reality.db.scheduled_jobs import ScheduledJobRun
    from reality.services import scheduled_jobs as jobs

    tenant, actor = business.tenant.id, scheduled_owner.id
    schedule = jobs.create_schedule(
        session,
        tenant,
        actor,
        "invitations.cleanup",
        {},
        request_id="constraints",
        interval_seconds=5,
    )
    jobs.control_schedule(session, tenant, actor, schedule.id, "resume", 1, "resume")
    schedule.next_run_at = now() - timedelta(seconds=1)
    jobs.materialize_due(session, tenant)
    run = session.query(ScheduledJobRun).filter_by(tenant_id=tenant).one()

    def duplicate(original, **overrides):
        values = {
            column.name: getattr(original, column.name)
            for column in original.__table__.columns
        }
        values.update(id=uuid4().hex, **overrides)
        with pytest.raises(IntegrityError), session.begin_nested():
            session.add(ScheduledJobRun(**values))
            session.flush()

    duplicate(run)  # Same occurrence is forbidden.
    duplicate(run, scheduled_for=now() + timedelta(seconds=5))  # One unfinished run.
    duplicate(
        run, tenant_id="missing-tenant"
    )  # Tenant FK and composite schedule scope.
    # Existing foreign tenant proves the composite FK independently of tenant existence.
    from reality.db.core import Tenant

    foreign = Tenant(id="foreign-schedule-owner", name="Foreign")
    session.add(foreign)
    session.flush()
    duplicate(run, tenant_id=foreign.id)
    manual = jobs.create_manual_run(
        session,
        tenant,
        actor,
        "invitations.cleanup",
        {},
        request_id="manual-constraint",
    )
    duplicate(manual)
