"""Disposable contribution cache migration preserves all retained financial inputs."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

TABLES = {
    "cost_contribution_generation",
    "cost_contribution_snapshot",
}


def test_cache_migration_foreign_keys_and_rollback(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0076_contribution_generations")
    engine = create_engine(postgres_database)
    try:
        from reality.db.core import Base

        inspector = inspect(engine)
        for name in TABLES:
            assert {
                tuple(f["constrained_columns"])
                for f in inspector.get_foreign_keys(name)
            } == {
                tuple(f.column_keys)
                for f in Base.metadata.tables[name].foreign_key_constraints
            }
        with engine.begin() as conn:
            # Isolate disposable storage downgrade without manufacturing business authority.
            conn.execute(
                text("ALTER TABLE cost_contribution_generation DISABLE TRIGGER ALL")
            )
            conn.execute(
                text(
                    "INSERT INTO cost_contribution_generation (id,tenant_id,action_id,algorithm_version,completed_at,output_hash) VALUES ('g','t','r','commercial-v1',now(),:digest)"
                ),
                {"digest": "0" * 64},
            )
            conn.execute(
                text("ALTER TABLE cost_contribution_generation ENABLE TRIGGER ALL")
            )
        with engine.begin() as conn, pytest.raises(IntegrityError), conn.begin_nested():
            conn.execute(
                text(
                    "INSERT INTO cost_contribution_snapshot (id,tenant_id,generation_id,review_id,goods_cost,known_direct_selling_cost,known_allocated_selling_cost,selling_complete) VALUES ('s','other','g','r',1,0,0,true)"
                )
            )
        command.downgrade(config, "0075_inventory_generations")
        tables = set(inspect(engine).get_table_names())
        assert not TABLES & tables
        assert {
            "cost_inventory_review",
            "cost_input_manifest",
            "cost_contribution_review",
        } <= tables
    finally:
        engine.dispose()


def test_cache_downgrade_refuses_unfinished_worker_run(postgres_database, monkeypatch):
    from sqlalchemy.orm import Session

    from reality.db.core import AppUser
    from reality.db.scheduled_jobs import ScheduledJobRun
    from reality.services import core

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0076_contribution_generations")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as session:
            tenant = core.create_tenant(session, "Migration job")
            actor = AppUser(
                id="cache-worker-owner",
                email="cache-worker@example.test",
                password_hash="unused",
                status="active",
                email_verified_at=core.now(),
            )
            session.add(actor)
            session.flush()
            run = ScheduledJobRun(
                id="cache-run",
                request_id="cache-migration-request",
                request_fingerprint="0" * 64,
                tenant_id=tenant.id,
                actor_id=actor.id,
                job_type="costing.contribution.refresh",
                configuration={
                    "version": 1,
                    "arguments": {"action_id": "retained-action"},
                },
            )
            session.add(run)
            session.commit()
        with pytest.raises(RuntimeError, match="unfinished costing jobs"):
            command.downgrade(config, "0075_inventory_generations")
        assert TABLES <= set(inspect(engine).get_table_names())
        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE scheduled_job_run SET status='cancelled' WHERE id='cache-run'"
                )
            )
        command.downgrade(config, "0075_inventory_generations")
    finally:
        engine.dispose()
