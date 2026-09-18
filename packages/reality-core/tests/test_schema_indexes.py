"""Spec 181: every foreign key's first column carries an index, in the models and in the database."""

import importlib.util
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from reality.db.core import FOREIGN_KEY_INDEXES, Base, index_foreign_keys


def _leading_columns(indexes, constraints):
    leading = {index["column_names"][0] for index in indexes if index["column_names"]}
    for constraint in constraints:
        # Unique constraints report column_names, the primary key constrained_columns.
        columns = constraint.get("column_names") or constraint.get(
            "constrained_columns"
        )
        if columns:
            leading.add(columns[0])
    return leading


def test_every_foreign_key_leads_an_index_in_the_models():
    # The rule ran once at import time; running it again finds nothing left to index,
    # which is the whole invariant: every foreign key's first column leads an index, a
    # primary key or a unique constraint.
    assert index_foreign_keys(Base.metadata) == []
    assert len(FOREIGN_KEY_INDEXES) >= 80


def test_migration_creates_exactly_the_indexes_for_its_schema_generation():
    path = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "versions"
        / "0059_foreign_key_indexes.py"
    )
    spec = importlib.util.spec_from_file_location("fk_indexes_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    migrated = {(name, table, column) for name, table, column in module.INDEXES}
    derived = {
        (index.name, index.table.name, next(iter(index.columns)).name)
        for index in FOREIGN_KEY_INDEXES
    }
    # Revision 0059 owns every derived index for tables that existed at 0058.
    # Tables added by later migrations create their own derived indexes.
    later_tables = {"analytics_report", "analysis_request"}
    assert migrated == {
        entry for entry in derived if entry[1] not in later_tables
    }
    assert {entry[1] for entry in derived - migrated} == later_tables
    assert all(len(name) <= 63 for name, _, _ in migrated)


def test_migrated_database_indexes_every_foreign_key(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        inspector = inspect(engine)
        missing = []
        for table in inspector.get_table_names():
            leading = _leading_columns(
                inspector.get_indexes(table),
                [
                    inspector.get_pk_constraint(table),
                    *inspector.get_unique_constraints(table),
                ],
            )
            for foreign_key in inspector.get_foreign_keys(table):
                column = foreign_key["constrained_columns"][0]
                if column not in leading:
                    missing.append(f"{table}.{column}")
        assert missing == [], missing
        command.downgrade(config, "0058_storyline")
        remaining = {
            index["name"]
            for table in inspect(engine).get_table_names()
            for index in inspect(engine).get_indexes(table)
        }
        assert not ({index.name for index in FOREIGN_KEY_INDEXES} & remaining)
        command.upgrade(config, "head")
    finally:
        engine.dispose()
