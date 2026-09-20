"""Partial commercial matching retains immutable tenant-scoped authority."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DBAPIError

TABLES = {
    "cost_commercial_match_revision",
    "cost_commercial_inventory_part",
    "cost_commercial_direct_part",
}


def configuration(database):
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database)
    return config


def test_commercial_matching_migration_matches_model_and_empty_rollback(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = configuration(postgres_database)
    command.upgrade(config, "0085_commercial_matching")
    engine = create_engine(postgres_database)
    try:
        from reality.db.core import Base

        inspector = inspect(engine)
        assert TABLES <= set(inspector.get_table_names())
        for name in TABLES:
            actual = {
                tuple(row["constrained_columns"])
                for row in inspector.get_foreign_keys(name)
            }
            expected = {
                tuple(row.column_keys)
                for row in Base.metadata.tables[name].foreign_key_constraints
            }
            assert actual == expected, name
        command.downgrade(config, "0084_inventory_ownership_parts")
        assert not TABLES & set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_commercial_matching_populated_downgrade_and_mutation_refuse(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = configuration(postgres_database)
    command.upgrade(config, "0085_commercial_matching")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE cost_commercial_match_revision DISABLE TRIGGER ALL")
            )
            connection.execute(
                text(
                    "INSERT INTO cost_commercial_match_revision(id,tenant_id,document_line_id,revision,stated_net,currency,evidence_hash,goods_cost_disposition,profile,introduced_event_id,action_id,reason,input_schema_version,content_hash) VALUES ('r','t','l',1,10,'EUR','0123456789012345678901234567890123456789012345678901234567890123','not_applicable','commercial_v1','e','a','retained',1,'0123456789012345678901234567890123456789012345678901234567890123')"
                )
            )
            connection.execute(
                text("ALTER TABLE cost_commercial_match_revision ENABLE TRIGGER ALL")
            )
        with engine.begin() as connection, pytest.raises(DBAPIError, match="immutable"):
            connection.execute(
                text(
                    "UPDATE cost_commercial_match_revision SET reason='changed' WHERE id='r'"
                )
            )
        with pytest.raises(RuntimeError, match="commercial matching"):
            command.downgrade(config, "0084_inventory_ownership_parts")
        assert TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
