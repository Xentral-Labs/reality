"""T087 conversion authority is immutable and tenant-scoped."""

import pathlib

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DBAPIError

TABLE = "cost_conversion_basis_revision"


def configuration(database):
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database)
    return config


def test_conversion_migration_declares_shortest_composite_links():
    source = pathlib.Path("migrations/versions/0087_cost_conversion.py").read_text()
    assert 'link("evidence_source_record_id", "source_record")' in source
    assert 'link("introduced_event_id", "business_event")' in source
    assert 'link("action_id", "action")' in source
    assert '"fk_cost_attribution_part_conversion"' in source
    assert '"fk_cost_selling_part_conversion"' in source
    assert source.count('["tenant_id", "conversion_basis_revision_id"]') == 2
    assert "Numeric(28, 12)" in source


def test_conversion_migration_matches_model_and_empty_rollback(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = configuration(postgres_database)
    command.upgrade(config, "0087_cost_conversion")
    engine = create_engine(postgres_database)
    try:
        from reality.db.core import Base

        inspector = inspect(engine)
        assert TABLE in inspector.get_table_names()
        actual = {
            tuple(row["constrained_columns"])
            for row in inspector.get_foreign_keys(TABLE)
        }
        expected = {
            tuple(row.column_keys)
            for row in Base.metadata.tables[TABLE].foreign_key_constraints
        }
        assert actual == expected
        for part in ("cost_attribution_part", "cost_selling_attribution_part"):
            columns = {column["name"] for column in inspector.get_columns(part)}
            assert "conversion_basis_revision_id" in columns
            assert ("tenant_id", "conversion_basis_revision_id") in {
                tuple(row["constrained_columns"])
                for row in inspector.get_foreign_keys(part)
            }
        command.downgrade(config, "0086_carrying_value")
        assert TABLE not in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_conversion_history_is_immutable_and_blocks_downgrade(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = configuration(postgres_database)
    command.upgrade(config, "0087_cost_conversion")
    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {TABLE} DISABLE TRIGGER ALL"))
            connection.execute(
                text(
                    f"INSERT INTO {TABLE}(id,tenant_id,evidence_source_record_id,kind,from_code,to_code,numerator,denominator,effective_at,revision,supersedes_id,introduced_event_id,action_id,reason,input_schema_version,content_hash) VALUES ('r','t','s','currency','EUR','USD',1,2,now(),1,NULL,'e','a','retained',1,'0123456789012345678901234567890123456789012345678901234567890123')"
                )
            )
            connection.execute(text(f"ALTER TABLE {TABLE} ENABLE TRIGGER ALL"))
        with engine.begin() as connection, pytest.raises(DBAPIError, match="immutable"):
            connection.execute(
                text(f"UPDATE {TABLE} SET reason='changed' WHERE id='r'")
            )
        with pytest.raises(RuntimeError, match="conversion"):
            command.downgrade(config, "0086_carrying_value")
    finally:
        engine.dispose()
