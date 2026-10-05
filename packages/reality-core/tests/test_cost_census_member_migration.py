"""Populated protected census storage has an exact reversible transition."""

import importlib.util

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, insert, inspect, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker
from test_company_generation_manifest import _reviewed
from test_cost_census_members import (
    FAMILIES,
    STORE,
    assert_indexes,
    building,
    rows,
    seed_capture,
)
from test_cost_projection_migration import _schema_snapshot
from test_finance_reference_migration import _all_records

from reality.db.core import Base
from reality.services import core, costing
from reality.services.memberships import Principal


def protections(connection):
    return list(
        connection.execute(
            text(
                "SELECT c.relname,t.tgname,pg_get_triggerdef(t.oid),pg_get_functiondef(t.tgfoid) "
                "FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
                "WHERE NOT t.tgisinternal AND c.relname LIKE 'cost_company_census%' "
                "ORDER BY c.relname,t.tgname"
            )
        ).tuples()
    )


@pytest.fixture
def predecessor(postgres_database, monkeypatch):
    from reality.services import operational_cases

    # Pin the unrelated coordination policy to this historical schema version.
    monkeypatch.setattr(operational_cases, "coordination_enabled", lambda *_: False)
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0120_manifest_members")
    engine = create_engine(postgres_database)
    try:
        first = seed_capture(engine)
        seed_capture(engine)
        factory = sessionmaker(engine, expire_on_commit=False)
        factory, tenant, owner, census = _reviewed((engine, factory, first[1], None))
        with factory() as session:
            costing.admit_company_cost_manifest(
                session, tenant, census, principal=Principal(owner)
            )
            session.commit()
        yield engine, config, first
    finally:
        engine.dispose()


def test_populated_upgrade_rollback_reupgrade_exact_history(predecessor):
    engine, config, first = predecessor
    names = tuple(FAMILIES.values())
    with engine.connect() as connection:
        physical = set(inspect(connection).get_table_names())
        all_names = sorted(physical - {"alembic_version"})
        before = _all_records(connection, all_names)
        schema = _schema_snapshot(
            connection, (*names, "cost_company_contribution_input")
        )
        guards = protections(connection)
        assert before["cost_company_contribution_input"]
    command.upgrade(config, "0121_census_members")
    with engine.connect() as connection:
        assert _all_records(connection, all_names) == before
        assert set(inspect(connection).get_table_names()) == physical - set(names) | {
            STORE
        }
        assert_indexes(connection)
    with Session(engine) as session:
        assert costing.verify_company_cost_census(session, first[1], first[2])[
            "verified"
        ]
    seed_capture(engine)
    with engine.connect() as connection:
        current = _all_records(connection, all_names)
    command.downgrade(config, "0120_manifest_members")
    with engine.connect() as connection:
        assert _all_records(connection, all_names) == current
        assert (
            _schema_snapshot(connection, (*names, "cost_company_contribution_input"))
            == schema
        )
        assert protections(connection) == guards
    command.upgrade(config, "0121_census_members")
    with engine.connect() as connection:
        assert _all_records(connection, all_names) == current
    with engine.begin() as connection, pytest.raises(DBAPIError, match="immutable"):
        connection.execute(
            text(
                "UPDATE cost_company_census SET event_sequence=event_sequence+1 WHERE tenant_id=:t"
            ),
            {"t": first[1]},
        )


def test_parity_abort_restores_all_original_values_and_protection(
    predecessor, monkeypatch
):
    engine, _, _ = predecessor
    spec = importlib.util.spec_from_file_location(
        "census_migration_test", "migrations/versions/0121_census_members.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    with engine.connect() as connection:
        names = sorted(set(inspect(connection).get_table_names()) - {"alembic_version"})
        before = _all_records(connection, names)
        guards = protections(connection)
        connection.rollback()

        def refuse(*args):
            raise RuntimeError("Injected census parity failure")

        monkeypatch.setattr(module, "_verify", refuse)
        with (
            pytest.raises(RuntimeError, match="parity"),
            connection.begin(),
            Operations.context(MigrationContext.configure(connection)),
        ):
            module.upgrade()
        assert _all_records(connection, names) == before
        assert protections(connection) == guards
        assert STORE not in inspect(connection).get_table_names()


def test_protected_purge_refusal_and_rollback_preserved(predecessor):
    engine, config, first = predecessor
    for revision in ("0120_manifest_members", "0121_census_members"):
        command.upgrade(config, revision)
        with engine.connect() as connection:
            names = sorted(
                set(inspect(connection).get_table_names()) - {"alembic_version"}
            )
            before = _all_records(connection, names)
        with Session(engine) as session:
            with pytest.raises(DBAPIError, match="immutable"):
                if revision == "0120_manifest_members":
                    # Historical guard proof uses the original physical interface;
                    # current metadata already declares the future store.
                    session.execute(
                        text("DELETE FROM cost_company_census_line WHERE tenant_id=:t"),
                        {"t": first[1]},
                    )
                else:
                    core._purge_tenant_records(session, first[1])
            session.rollback()
        with engine.connect() as connection:
            assert _all_records(connection, names) == before


def test_company_input_cannot_select_equal_non_line_identity(predecessor):
    engine, config, _ = predecessor
    command.upgrade(config, "0121_census_members")
    with Session(engine) as session:
        original = dict(
            session.execute(
                text("SELECT * FROM cost_company_contribution_input LIMIT 1")
            )
            .mappings()
            .one()
        )
        tenant = original["tenant_id"]
        manifest = dict(
            session.execute(
                text(
                    "SELECT * FROM cost_company_manifest WHERE tenant_id=:t AND id=:i"
                ),
                {"t": tenant, "i": original["manifest_id"]},
            )
            .mappings()
            .one()
        )
        captured = rows(session.connection(), tenant, manifest["census_id"])
        header = building(session, tenant, manifest["census_id"])
        manifest.update(
            id="typed-test-manifest",
            state="building",
            sealed_at=None,
            content_hash="f" * 64,
        )
        session.execute(
            insert(Base.metadata.tables["cost_company_manifest"]).values(**manifest)
        )
        for family in ("movement", "document"):
            member = dict(captured[family][0])
            member.update(id="not-a-line", census_id=header["id"])
            session.execute(
                insert(Base.metadata.tables[FAMILIES[family]]).values(**member)
            )
        session.commit()
    original.update(
        id="typed-test-input", manifest_id=manifest["id"], census_line_id="not-a-line"
    )
    with Session(engine) as session, pytest.raises(DBAPIError, match="foreign key"):
        session.execute(
            insert(Base.metadata.tables["cost_company_contribution_input"]).values(
                **original
            )
        )
