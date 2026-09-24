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


def _module(name: str):
    path = Path(__file__).resolve().parents[1] / "migrations" / "versions" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_migrations_together_create_exactly_the_derived_indexes():
    """Two revisions own these now, and between them they own all of them.

    0059 gave every foreign key's first column an index. Since spec 181 FR-005 a
    reference between two company-scoped tables begins with the company, so the
    rule indexes the whole key instead and 0088 replaced the narrower indexes
    with composite ones. Neither revision owns the set by itself; what has to
    hold is that following both of them leaves exactly what the rule derives.
    """
    first = _module("0059_foreign_key_indexes.py")
    second = _module("0088_tenant_scoped_keys.py")
    after_first = {(name, table, (column,)) for name, table, column in first.INDEXES}
    after_second = after_first - {
        (name, table, columns) for name, table, columns, _ in second.INDEX_DROPS
    } | {(name, table, columns) for name, table, columns, _ in second.INDEX_CREATES}
    # References added to existing tables later name their index in their revision.
    after_second |= set(_module("0093_decision_trail.py").INDEXES)
    derived = {
        (index.name, index.table.name, tuple(c.name for c in index.columns))
        for index in FOREIGN_KEY_INDEXES
    }
    # Tables added by later migrations bring their own derived indexes with them.
    later_tables = {
        "analytics_report",
        "analysis_request",
        "dunning_notice",
        "dunning_notice_invoice",
        "supply_assignment",
    }
    assert {entry for entry in after_second if entry[1] not in later_tables} == {
        entry for entry in derived if entry[1] not in later_tables
    }
    assert {entry[1] for entry in derived - after_second} <= later_tables
    assert all(len(name) <= 63 for name, _, _ in derived)


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
        # What a revision creates, its downgrade takes away. Asking instead that
        # no *derived* index name survives stopped being true under spec 181
        # FR-005: thirty-six indexes kept their name and changed their columns,
        # because the rule now derives what the model used to declare on the
        # column. Those names were already there at 0058, for a reason no
        # revision here is answerable for, and 0088 hands them back on the way
        # down — so they are excluded rather than demanded.
        keys = _module("0088_tenant_scoped_keys.py")
        created = {
            name for name, _, _ in _module("0059_foreign_key_indexes.py").INDEXES
        }
        created |= {name for name, _, _, _ in keys.INDEX_CREATES}
        created -= {name for name, _, _, _ in keys.INDEX_DROPS}
        assert not (created & remaining)
        command.upgrade(config, "head")
    finally:
        engine.dispose()
