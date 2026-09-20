"""Contribution authority migration preserves tenant FKs and retained history."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

TABLES = {"cost_revenue_match_basis", "cost_contribution_review"}


def test_contribution_migration_and_empty_rollback(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0073_contribution_reviews")
    engine = create_engine(postgres_database)
    try:
        from reality.db.core import Base

        inspector = inspect(engine)
        for name in TABLES:
            actual = {
                tuple(f["constrained_columns"])
                for f in inspector.get_foreign_keys(name)
            }
            assert actual == {
                tuple(f.column_keys)
                for f in Base.metadata.tables[name].foreign_key_constraints
            }
        command.downgrade(config, "0072_inventory_costing")
        assert not TABLES & set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_contribution_populated_downgrade_refuses(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0073_contribution_reviews")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE cost_contribution_review DISABLE TRIGGER ALL")
            )
            conn.execute(
                text(
                    "INSERT INTO cost_contribution_review(id,tenant_id,revenue_basis_id,inventory_member_id,revision,profile,economic_at,knowledge_at,introduced_event_id,event_sequence,action_id,reason,content_hash) VALUES ('r','t','b','m',1,'commercial_v1',now(),now(),'e',1,'a','retained','hash')"
                )
            )
            conn.execute(
                text("ALTER TABLE cost_contribution_review ENABLE TRIGGER ALL")
            )
        with pytest.raises(RuntimeError, match="retained"):
            command.downgrade(config, "0072_inventory_costing")
        assert TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
