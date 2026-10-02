"""Populated manifest storage roundtrip preserves values, authorities and old DDL."""

import importlib.util

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from test_cost_manifest_members import (
    FAMILIES,
    assert_database_fk_indexes,
    seed_members,
)
from test_cost_projection_migration import _schema_snapshot
from test_finance_reference_migration import _all_records


@pytest.fixture
def legacy_members(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0119_finance_references")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as session:
            first = seed_members(session)
            seed_members(session)
            session.commit()
        yield engine, config, first
    finally:
        engine.dispose()


def test_populated_members_roundtrip_exact_authorities_and_schema(legacy_members):
    from reality.services.costing import receipt_cost

    engine, config, data = legacy_members
    tenant, targets, manifests, movement, old, expected = data
    with engine.connect() as connection:
        physical = set(inspect(connection).get_table_names())
        names = sorted(physical - {"alembic_version"})
        before = _all_records(connection, names)
        schema = _schema_snapshot(connection, FAMILIES)
    command.upgrade(config, "0120_manifest_members")
    with engine.connect() as connection:
        assert _all_records(connection, names) == before
        assert set(inspect(connection).get_table_names()) == physical - set(
            FAMILIES
        ) | {"cost_manifest_member"}
        assert len(inspect(connection).get_foreign_keys("cost_manifest_member")) == 7
        assert_database_fk_indexes(connection)
    with Session(engine) as session:
        assert receipt_cost(session, tenant, movement, manifest_id=old) == expected
    with engine.begin() as connection:
        for name, (column, _, _) in FAMILIES.items():
            assert (
                connection.execute(
                    text(
                        f"UPDATE {name} SET manifest_id=:m WHERE tenant_id=:t AND id='collision' RETURNING id"
                    ),
                    {"m": manifests[1], "t": tenant},
                ).scalar_one()
                == "collision"
            )
            assert (
                connection.execute(
                    text(
                        f"DELETE FROM {name} WHERE tenant_id=:t AND id='collision' RETURNING id"
                    ),
                    {"t": tenant},
                ).scalar_one()
                == "collision"
            )
            assert (
                connection.execute(
                    text(
                        f"INSERT INTO {name} (tenant_id,id,manifest_id,{column}) VALUES (:t,'collision',:m,:v) RETURNING id"
                    ),
                    {"t": tenant, "m": manifests[1], "v": targets[name]},
                ).scalar_one()
                == "collision"
            )
    with engine.connect() as connection:
        changed = _all_records(connection, names)
        assert {n: v for n, v in changed.items() if n not in FAMILIES} == {
            n: v for n, v in before.items() if n not in FAMILIES
        }
    command.downgrade(config, "0119_finance_references")
    with engine.connect() as connection:
        assert _all_records(connection, names) == changed
        assert _schema_snapshot(connection, FAMILIES) == schema
        assert set(inspect(connection).get_table_names()) == physical
    command.upgrade(config, "0120_manifest_members")
    with engine.connect() as connection:
        assert _all_records(connection, names) == changed


def test_failed_parity_leaves_original_schema_and_rows(legacy_members, monkeypatch):
    engine, _config, _ = legacy_members
    path = "migrations/versions/0120_manifest_members.py"
    module_spec = importlib.util.spec_from_file_location(
        "manifest_migration_test", path
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    with engine.connect() as connection:
        before = _all_records(connection, FAMILIES)
        tables = set(inspect(connection).get_table_names())
        connection.rollback()

        def refuse(*args):
            raise RuntimeError("Injected parity failure")

        monkeypatch.setattr(module, "_verify", refuse)
        with (
            pytest.raises(RuntimeError, match="parity"),
            connection.begin(),
            Operations.context(MigrationContext.configure(connection)),
        ):
            module.upgrade()
        assert _all_records(connection, FAMILIES) == before
        assert set(inspect(connection).get_table_names()) == tables
