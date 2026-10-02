"""Shared cost storage preserves logical grains, identities and authority."""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from reality.db.core import Base


def test_output_storage_is_four_tables_and_thirteen_views(session):
    from reality.db.cost_projections import FAMILIES, STORAGE

    inspector = inspect(session.connection())
    physical = set(inspector.get_table_names())
    assert set(STORAGE) <= physical
    assert not set(FAMILIES) & physical
    assert set(FAMILIES) <= set(inspector.get_view_names())
    assert len(FAMILIES) - len(STORAGE) == 9
    assert all(Base.metadata.tables[name].info["projection_view"] for name in FAMILIES)


def test_compatibility_view_keeps_mapped_fields():
    from sqlalchemy import inspect as mapped

    from reality.db.cost_generations import CostInventorySnapshot

    assert set(mapped(CostInventorySnapshot).columns.keys()) == {
        "tenant_id",
        "id",
        "generation_id",
        "remaining_quantity",
        "acquisition_value",
        "carrying_value",
    }


def test_shared_storage_rejects_wrong_family_and_missing_shape(session, business):
    from reality.db.cost_projections import STORAGE

    assert "cost_projection_generation" in STORAGE
    for family in ("not_a_family", "cost_inventory_generation"):
        with pytest.raises(DBAPIError), session.begin_nested():
            session.execute(
                text("""INSERT INTO cost_projection_generation
                (tenant_id, projection_family, id) VALUES (:tenant,:family,'bad')"""),
                {"tenant": business.tenant.id, "family": family},
            )


def test_schema_creation_is_idempotent(session):
    Base.metadata.create_all(session.connection())
    Base.metadata.create_all(session.connection())


def test_partial_schema_creation_does_not_install_incomplete_guards(postgres_database):
    from sqlalchemy import create_engine

    from reality.db.core import Tenant

    engine = create_engine(postgres_database)
    try:
        Base.metadata.create_all(engine, tables=[Tenant.__table__])
        assert inspect(engine).get_table_names() == ["tenant"]
    finally:
        engine.dispose()


def test_projection_schema_matches_frozen_migration_without_index_drift():
    """A second interpreter must produce the same shared indexes as frozen DDL."""
    import importlib.util
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    from sqlalchemy.dialects.postgresql import dialect
    from sqlalchemy.schema import CreateIndex

    from reality.db.cost_projections import STORAGE

    migration = Path("migrations/versions/0117_cost_projections.py")
    spec = importlib.util.spec_from_file_location("frozen_projections", migration)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected = sorted(
        sql.strip()
        for sql in module.SHARED_DDL
        if sql.startswith(("CREATE INDEX", "CREATE UNIQUE INDEX"))
    )
    actual = sorted(
        str(CreateIndex(index).compile(dialect=dialect())).strip()
        for name in STORAGE
        for index in Base.metadata.tables[name].indexes
    )
    assert actual == expected
    code = """import json
from sqlalchemy.schema import CreateIndex
from sqlalchemy.dialects.postgresql import dialect
from reality.db.core import Base
from reality.db.cost_projections import STORAGE
print(json.dumps(sorted(str(CreateIndex(i).compile(dialect=dialect())).strip()
    for n in STORAGE for i in Base.metadata.tables[n].indexes)))"""
    environment = os.environ | {"PYTHONHASHSEED": "316", "PYTHONPATH": "src"}
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == expected


@pytest.fixture
def cost_owner(session, business):
    import test_inventory_costing_services as fixtures

    return fixtures.cost_owner.__wrapped__(session, business)


def test_real_inventory_view_writes_null_uniqueness_and_typed_links(
    session, business, cost_owner
):
    from test_inventory_generations import reviewed

    from reality.services import core, costing

    tenant = business.tenant.id
    review = reviewed(session, business, cost_owner)
    built = costing.build_inventory_generation(session, tenant, review)
    result = costing.inventory_cost_snapshot(session, tenant, business.item.id)
    assert result["generation_id"] == built["generation_id"]
    assert result["result"]["acquisition_value"] == "420.0000"
    other = core.create_tenant(session, "Other projection tenant").id
    queries = [
        (
            """INSERT INTO cost_inventory_generation
            (tenant_id,id,review_id,assessment_revision_id,algorithm_version,completed_at,output_hash)
            SELECT tenant_id,'duplicate',review_id,assessment_revision_id,algorithm_version,completed_at,output_hash
            FROM cost_inventory_generation WHERE tenant_id=:tenant AND id=:id""",
            {"tenant": tenant, "id": built["generation_id"]},
        ),
        (
            """INSERT INTO cost_inventory_snapshot
            (tenant_id,id,generation_id,remaining_quantity,acquisition_value)
            VALUES (:other,'foreign',:id,1,1)""",
            {"other": other, "id": built["generation_id"]},
        ),
        (
            """UPDATE cost_projection_inventory SET generation_id_family='cost_contribution_generation'
            WHERE tenant_id=:tenant AND generation_id=:id""",
            {"tenant": tenant, "id": built["generation_id"]},
        ),
        (
            """UPDATE cost_projection_generation SET projection_family='cost_contribution_generation'
            WHERE tenant_id=:tenant AND id=:id""",
            {"tenant": tenant, "id": built["generation_id"]},
        ),
    ]
    for sql, params in queries:
        with pytest.raises(DBAPIError), session.begin_nested():
            session.execute(text(sql), params)


def test_schema_creation_repairs_a_missing_storage_guard(session):
    session.execute(
        text("DROP TRIGGER guard_cost_generation_update ON cost_projection_generation")
    )
    Base.metadata.create_all(session.connection())
    assert session.scalar(
        text("""SELECT EXISTS (SELECT 1 FROM pg_trigger
        WHERE tgrelid='cost_projection_generation'::regclass
        AND tgname='guard_cost_generation_update')""")
    )
