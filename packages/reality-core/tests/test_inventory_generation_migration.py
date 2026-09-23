"""Disposable inventory cache migration preserves all retained financial inputs."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

TABLES = {
    "cost_inventory_generation",
    "cost_inventory_snapshot",
    "cost_inventory_publication",
}


def test_cache_migration_foreign_keys_and_rollback(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0075_inventory_generations")
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
                if "assessment_revision_id" not in f.column_keys
            }
        with engine.begin() as conn:
            # Isolate disposable storage downgrade without manufacturing business authority.
            conn.execute(
                text("ALTER TABLE cost_inventory_generation DISABLE TRIGGER ALL")
            )
            conn.execute(
                text(
                    "INSERT INTO cost_inventory_generation (id,tenant_id,review_id,algorithm_version,completed_at,output_hash) VALUES ('g','t','r','inventory-v1',now(),:digest)"
                ),
                {"digest": "0" * 64},
            )
            conn.execute(
                text("ALTER TABLE cost_inventory_generation ENABLE TRIGGER ALL")
            )
        with engine.begin() as conn, pytest.raises(IntegrityError), conn.begin_nested():
            conn.execute(
                text(
                    "INSERT INTO cost_inventory_snapshot (id,tenant_id,generation_id,remaining_quantity,acquisition_value) VALUES ('s','other','g',1,1)"
                )
            )
        command.downgrade(config, "0074_selling_costs")
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
    from reality.services import core

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0075_inventory_generations")
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
            tenant_id, actor_id = tenant.id, actor.id
            session.commit()
        with engine.begin() as conn:
            # Written as SQL, not through the ORM: this test pins an older schema on
            # purpose, and a column the model gains later must not break its subject.
            conn.execute(
                text(
                    "INSERT INTO scheduled_job_run"
                    " (id, tenant_id, actor_id, job_type, configuration, request_id,"
                    "  request_fingerprint, status, attempt_count, next_attempt_at, created_at)"
                    " VALUES (:id, :tenant, :actor, :job_type, cast(:configuration as jsonb),"
                    "  :request_id, :fingerprint, 'pending', 0, now(), now())"
                ),
                {
                    "id": "cache-run",
                    "tenant": tenant_id,
                    "actor": actor_id,
                    "job_type": "costing.inventory.refresh",
                    "configuration": '{"version": 1, "arguments": {"review_id": "retained-review"}}',
                    "request_id": "cache-migration-request",
                    "fingerprint": "0" * 64,
                },
            )
        with pytest.raises(RuntimeError, match="unfinished costing jobs"):
            command.downgrade(config, "0074_selling_costs")
        assert TABLES <= set(inspect(engine).get_table_names())
        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE scheduled_job_run SET status='cancelled' WHERE id='cache-run'"
                )
            )
        command.downgrade(config, "0074_selling_costs")
    finally:
        engine.dispose()
