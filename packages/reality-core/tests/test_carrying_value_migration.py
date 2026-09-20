"""T086 carrying assessments retain immutable same-tenant authority."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DBAPIError

TABLES = {
    "cost_valuation_assessment_revision",
    "cost_valuation_assessment_part",
}


def configuration(database):
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database)
    return config


def test_carrying_assessment_migration_matches_model_and_empty_rollback(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = configuration(postgres_database)
    command.upgrade(config, "0086_carrying_value")
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
        header = Base.metadata.tables["cost_valuation_assessment_revision"]
        assert "policy_id" not in header.c
        assert "item_id" not in header.c
        assert "owner_party_id" not in header.c
        assert "assessment_revision_id" in {
            column["name"]
            for column in inspector.get_columns("cost_inventory_generation")
        }
        assert "carrying_value" in {
            column["name"]
            for column in inspector.get_columns("cost_inventory_snapshot")
        }
        command.downgrade(config, "0085_commercial_matching")
        assert not TABLES & set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_carrying_assessment_populated_downgrade_and_mutation_refuse(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = configuration(postgres_database)
    command.upgrade(config, "0086_carrying_value")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE cost_valuation_assessment_revision DISABLE TRIGGER ALL"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO cost_valuation_assessment_revision(id,tenant_id,inventory_review_id,revision,kind,effective_at,target_event_sequence,knowledge_at,introduced_event_id,action_id,reason,input_schema_version,content_hash) VALUES ('r','t','v',1,'write_down',now(),1,now(),'e','a','retained',1,'0123456789012345678901234567890123456789012345678901234567890123')"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE cost_valuation_assessment_revision ENABLE TRIGGER ALL"
                )
            )
        with engine.begin() as connection, pytest.raises(DBAPIError, match="immutable"):
            connection.execute(
                text(
                    "UPDATE cost_valuation_assessment_revision SET reason='changed' WHERE id='r'"
                )
            )
        with pytest.raises(RuntimeError, match="valuation assessment"):
            command.downgrade(config, "0085_commercial_matching")
        assert TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
