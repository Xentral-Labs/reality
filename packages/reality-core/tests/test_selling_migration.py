"""Selling authority migration preserves tenant FKs and retained history."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

TABLES = {
    "cost_selling_attribution_part",
    "cost_selling_review_member",
    "cost_selling_review_category",
}


def test_selling_migration_and_empty_rollback(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0074_selling_costs")
    engine = create_engine(postgres_database)
    try:
        from reality.db.core import Base

        inspector = inspect(engine)
        for name in TABLES:
            actual = {
                tuple(f["constrained_columns"])
                for f in inspector.get_foreign_keys(name)
            }
            # The conversion-basis link is introduced by migration 0081 and is
            # therefore intentionally absent at this historical 0067 boundary.
            assert actual == {
                tuple(f.column_keys)
                for f in Base.metadata.tables[name].foreign_key_constraints
                if "conversion_basis_revision_id" not in f.column_keys
            }
        command.downgrade(config, "0073_contribution_reviews")
        assert not TABLES & set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_selling_populated_downgrade_refuses(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "0074_selling_costs")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE cost_selling_review_category DISABLE TRIGGER ALL")
            )
            conn.execute(
                text(
                    "INSERT INTO cost_selling_review_category(id,tenant_id,review_id,category,disposition,reason) VALUES ('r','t','review','payment_fee','confirmed_zero','retained')"
                )
            )
            conn.execute(
                text("ALTER TABLE cost_selling_review_category ENABLE TRIGGER ALL")
            )
        with pytest.raises(RuntimeError, match="retained"):
            command.downgrade(config, "0073_contribution_reviews")
        assert TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
