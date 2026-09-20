"""Retained census schema has tenant links and refuses destructive rollback."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from test_cost_captured_basis_storage import scheduled_database  # noqa: F401

TABLES = {
    "cost_captured_basis",
    "cost_captured_inventory_basis",
    "cost_captured_contribution_basis",
}


def test_migration_parity_and_empty_upgrade_downgrade(postgres_database, monkeypatch):
    from reality.db.core import Base

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0078_captured_cost_basis")
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
            from sqlalchemy import CheckConstraint, UniqueConstraint

            model = Base.metadata.tables[table]
            assert {
                tuple(row["column_names"])
                for row in inspector.get_unique_constraints(table)
            } == {
                tuple(constraint.columns.keys())
                for constraint in model.constraints
                if isinstance(constraint, UniqueConstraint)
            }
            assert {row["name"] for row in inspector.get_check_constraints(table)} == {
                constraint.name
                for constraint in model.constraints
                if isinstance(constraint, CheckConstraint)
            }
            assert {
                row["name"]: row["nullable"] for row in inspector.get_columns(table)
            } == {column.name: column.nullable for column in model.columns}

            assert {
                index["name"]
                for index in inspector.get_indexes(table)
                if not index.get("duplicates_constraint")
            } == {index.name for index in Base.metadata.tables[table].indexes}
        command.downgrade(config, "0077_company_cost_census")
        assert not TABLES & set(inspect(engine).get_table_names())
        command.upgrade(config, "0078_captured_cost_basis")
        assert TABLES <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_populated_downgrade_refuses(scheduled_database, monkeypatch):  # noqa: F811
    from test_cost_captured_basis_storage import retained

    engine, *_ = scheduled_database
    monkeypatch.setenv(
        "REALITY_DATABASE_URL", engine.url.render_as_string(hide_password=False)
    )
    config = Config("alembic.ini")
    retained(scheduled_database)
    with pytest.raises(RuntimeError, match="retained captured basis history"):
        command.downgrade(config, "0077_company_cost_census")
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT count(*) FROM cost_captured_basis")) == 1
