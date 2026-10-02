"""Populated shared-output migration preserves all four families losslessly."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError


@pytest.fixture
def legacy_database(postgres_database, monkeypatch):
    import test_cost_census_storage as storage
    from legacy_finance import bootstrap_legacy_accounts

    from reality.services.finance import accounts

    # Cost migration specimens stay at the original pinned schema. Construct
    # unrelated legacy account defaults without running today's bootstrap DDL.
    monkeypatch.setattr(accounts, "_bootstrap_accounts", bootstrap_legacy_accounts)
    original = command.upgrade

    def legacy_upgrade(config, revision, **kwargs):
        return original(
            config, "0116_company_currency" if revision == "head" else revision, **kwargs
        )

    fixture = storage.scheduled_database.__wrapped__(postgres_database, monkeypatch)
    with monkeypatch.context() as patch:
        patch.setattr(command, "upgrade", legacy_upgrade)
        database = next(fixture)
    try:
        yield database
    finally:
        fixture.close()


def _snapshot(connection, names, columns):
    return {
        name: list(
            connection.execute(
                text(
                    "SELECT "
                    + ", ".join(columns[name])
                    + f" FROM {name} ORDER BY tenant_id,id"
                )
            ).tuples()
        )
        for name in names
    }


def _schema_snapshot(connection, names):
    inspector = inspect(connection)
    return {
        name: {
            "columns": [
                (c["name"], str(c["type"]), c["nullable"], c["default"])
                for c in inspector.get_columns(name)
            ],
            "primary": inspector.get_pk_constraint(name),
            "checks": sorted(
                inspector.get_check_constraints(name), key=lambda c: c["name"]
            ),
            "unique": sorted(
                inspector.get_unique_constraints(name), key=lambda c: c["name"]
            ),
            "foreign": sorted(
                inspector.get_foreign_keys(name), key=lambda c: c["name"]
            ),
            "indexes": sorted(inspector.get_indexes(name), key=lambda c: c["name"]),
        }
        for name in names
    }


def test_populated_four_family_upgrade_and_lossless_downgrade(legacy_database):
    import test_company_generation_jobs as company
    import test_cost_captured_basis_storage as captured
    from test_cost_census import read_session

    from reality.db.core import Base
    from reality.db.cost_projections import FAMILIES, STORAGE, VIEW_COLUMNS
    from reality.services import costing

    engine, _, _, _ = legacy_database
    factory, tenant, manifest = company._manifest(legacy_database)
    with factory() as session:
        built = costing.build_company_cost_generation(session, tenant, manifest["id"])
        costing.publish_company_cost_generation(
            session, tenant, built["generation_id"], previous_generation_id=None
        )
        session.commit()
    factory, captured_tenant, _, basis = captured.retained(legacy_database)
    with read_session(factory) as session:
        report = costing.build_captured_cost_generation(
            session, captured_tenant, basis["basis_id"]
        )
        session.commit()
    with factory() as session:
        costing.publish_captured_cost_generation(
            session,
            captured_tenant,
            report["generation_id"],
            expected_previous_id=None,
        )
        session.commit()
    # Distinct former namespaces may contain the same opaque ID in one tenant.
    with engine.begin() as connection:
        connection.execute(
            text("""INSERT INTO cost_company_generation (
            tenant_id,id,manifest_id,algorithm_bundle,scope_key,state,
            expected_work_count,completed_work_count,inventory_count,contribution_count,
            inventory_content_hash,contribution_content_hash,started_at)
            SELECT c.tenant_id,i.id,c.manifest_id,'collision',c.scope_key,'building',
                c.expected_work_count,0,c.inventory_count,c.contribution_count,
                c.inventory_content_hash,c.contribution_content_hash,c.started_at
            FROM cost_company_generation c JOIN cost_inventory_generation i
                ON c.tenant_id=i.tenant_id LIMIT 1""")
        )
    # This specimen is pinned to 0108; later physical stores do not exist yet.
    legacy_tables = set(inspect(engine).get_table_names())
    authorities = {
        name: tuple(table.c.keys())
        for name, table in Base.metadata.tables.items()
        if name in legacy_tables
        and (
            (name.startswith("cost_") and name not in FAMILIES and name not in STORAGE)
            or name
            in {
                "source_record",
                "document",
                "document_line",
                "commitment",
                "movement",
                "ledger_entry",
                "fact",
                "action",
                "business_event",
                "analytics_report",
            }
        )
    }
    with engine.connect() as connection:
        original_schema = _schema_snapshot(connection, FAMILIES)
        authority_before = _snapshot(connection, authorities, authorities)
        before = _snapshot(connection, FAMILIES, VIEW_COLUMNS)
        physical_before = set(inspect(connection).get_table_names())
    # Company construction produces inventory/contribution child generations.
    assert all(
        before[name]
        for name in (
            "cost_inventory_generation",
            "cost_contribution_generation",
            "cost_generation",
            "cost_company_generation",
        )
    )
    config = Config("alembic.ini")
    command.upgrade(config, "0117_cost_projections")
    with engine.connect() as connection:
        assert _snapshot(connection, FAMILIES, VIEW_COLUMNS) == before
        assert _snapshot(connection, authorities, authorities) == authority_before
        physical = set(inspect(connection).get_table_names())
        assert len(physical_before) - len(physical) == 9
        assert not set(FAMILIES) & physical
        assert set(STORAGE) <= physical
        assert set(FAMILIES) <= set(inspect(connection).get_view_names())
    # Guards must act on direct shared writes, not just logical services/views.
    with engine.connect() as connection, pytest.raises(DBAPIError), connection.begin():
        connection.execute(
            text("""UPDATE cost_projection_generation SET output_hash=repeat('0',64)
            WHERE projection_family='cost_generation' AND tenant_id=:tenant AND id=:id"""),
            {"tenant": captured_tenant, "id": report["generation_id"]},
        )
    command.downgrade(config, "0116_company_currency")
    with engine.connect() as connection:
        assert _snapshot(connection, FAMILIES, VIEW_COLUMNS) == before
        assert _snapshot(connection, authorities, authorities) == authority_before
        restored_schema = _schema_snapshot(connection, FAMILIES)
        for name in FAMILIES:
            for section in original_schema[name]:
                assert (
                    restored_schema[name][section] == original_schema[name][section]
                ), (name, section)
        assert set(inspect(connection).get_table_names()) == physical_before
        assert not set(STORAGE) & set(inspect(connection).get_table_names())
    command.upgrade(config, "0117_cost_projections")
    with engine.connect() as connection:
        assert _snapshot(connection, FAMILIES, VIEW_COLUMNS) == before
        assert _snapshot(connection, authorities, authorities) == authority_before
