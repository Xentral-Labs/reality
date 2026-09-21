"""Retained census schema has tenant links and refuses destructive rollback."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from test_cost_census_storage import scheduled_database  # noqa: F401

TABLES = {
    "cost_company_census",
    *(
        f"cost_company_census_{family}"
        for family in ("movement", "document", "line", "source")
    ),
}


def test_migration_parity_and_empty_upgrade_downgrade(postgres_database, monkeypatch):
    from reality.db.core import Base

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    # To the head rather than to the revision that first created these tables:
    # the models describe the latest schema, and since spec 181 FR-005 these are
    # keyed by their company. Comparing today's models against yesterday's
    # database would fail for a reason that is not a defect.
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        inspector = inspect(engine)
        for table in TABLES:
            assert {
                tuple(f["constrained_columns"])
                for f in inspector.get_foreign_keys(table)
            } == {
                tuple(f.column_keys)
                for f in Base.metadata.tables[table].foreign_key_constraints
            }
            assert {col["name"] for col in inspector.get_columns(table)} == set(
                Base.metadata.tables[table].c.keys()
            )
            assert {
                index["name"]
                for index in inspector.get_indexes(table)
                if not index.get("duplicates_constraint")
            } == {index.name for index in Base.metadata.tables[table].indexes}
        command.downgrade(config, "0076_contribution_generations")
        assert not TABLES & set(inspect(engine).get_table_names())
        command.upgrade(config, "0077_company_cost_census")
        assert TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_populated_downgrade_refuses(scheduled_database, monkeypatch):  # noqa: F811
    from test_cost_census import seed
    from test_cost_census_storage import retain

    engine, *_ = scheduled_database
    monkeypatch.setenv(
        "REALITY_DATABASE_URL", engine.url.render_as_string(hide_password=False)
    )
    config = Config("alembic.ini")
    retain(seed(scheduled_database))
    with pytest.raises(RuntimeError, match="retained company census history"):
        command.downgrade(config, "0076_contribution_generations")
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT count(*) FROM cost_company_census")) == 1
