"""Approved nullable actor is confined to internal projection jobs."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError

from reality.db.core import uid
from reality.db.scheduled_jobs import ScheduledJobRun


def test_projection_job_schema_roundtrip(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        columns = {
            c["name"]: c for c in inspect(engine).get_columns("scheduled_job_run")
        }
        assert columns["actor_id"]["nullable"]
        assert "uq_projection_run_unfinished" in {
            i["name"] for i in inspect(engine).get_indexes("scheduled_job_run")
        }
        command.downgrade(config, "0056_physical_shipments")
        assert not next(
            c
            for c in inspect(engine).get_columns("scheduled_job_run")
            if c["name"] == "actor_id"
        )["nullable"]
        command.upgrade(config, "head")
    finally:
        engine.dispose()


def test_actor_constraint_and_internal_deduplication(
    session, business, scheduled_owner
):
    def insert(kind, actor):
        row = ScheduledJobRun(
            id=uid("run"),
            tenant_id=business.tenant.id,
            actor_id=actor,
            job_type=kind,
            configuration={"version": 1, "arguments": {"names": ["inventory"]}},
            request_id=uid("request"),
            request_fingerprint="a" * 64,
        )
        session.add(row)
        session.flush()

    for kind, actor in [
        ("invitations.cleanup", None),
        ("projections.refresh", scheduled_owner.id),
    ]:
        with pytest.raises(IntegrityError), session.begin_nested():
            insert(kind, actor)
    insert("projections.refresh", None)
    with pytest.raises(IntegrityError), session.begin_nested():
        insert("projections.refresh", None)


def test_downgrade_preserves_internal_job_history(postgres_database, monkeypatch):
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from reality.services.core import create_tenant
    from reality.services.projection_jobs import enqueue_due_projections

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as db:
            tenant = create_tenant(db, "Projection migration history")
            runs = enqueue_due_projections(db, tenant.id)
            assert len(runs) > 1, "one run per projection behind (spec 181 FR-004)"
            tenant_id, run_id = tenant.id, runs[0].id
            db.commit()
        # The queue is refused before the history is: restoring the per-company
        # index cannot be done while a company holds several unfinished runs.
        with pytest.raises(RuntimeError, match="more than one unfinished refresh run"):
            command.downgrade(config, "0056_physical_shipments")
        with Session(engine) as db:
            db.execute(
                ScheduledJobRun.__table__.update()
                .where(ScheduledJobRun.tenant_id == tenant_id)
                .values(status="succeeded")
            )
            db.commit()
        with pytest.raises(RuntimeError, match="Internal job history exists"):
            command.downgrade(config, "0056_physical_shipments")
        with Session(engine) as db:
            retained = db.scalar(
                select(ScheduledJobRun).where(
                    ScheduledJobRun.tenant_id == tenant_id,
                    ScheduledJobRun.id == run_id,
                )
            )
            assert retained is not None and retained.actor_id is None
        assert next(
            c
            for c in inspect(engine).get_columns("scheduled_job_run")
            if c["name"] == "actor_id"
        )["nullable"]
    finally:
        engine.dispose()
