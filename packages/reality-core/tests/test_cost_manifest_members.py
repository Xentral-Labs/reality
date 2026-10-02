"""Exact logical memberships retain typed targets and original mutation behavior."""

from types import SimpleNamespace

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import DBAPIError

FAMILIES = {
    "cost_manifest_receipt": (
        "receipt_basis_id",
        "cost_receipt_basis",
        "CostManifestReceipt",
    ),
    "cost_manifest_component": (
        "component_basis_id",
        "cost_component_basis",
        "CostManifestComponent",
    ),
    "cost_manifest_attribution": (
        "attribution_revision_id",
        "cost_attribution_revision",
        "CostManifestAttribution",
    ),
    "cost_manifest_correction": (
        "correction_basis_id",
        "cost_correction_basis",
        "CostManifestCorrection",
    ),
    "cost_manifest_replacement": (
        "replacement_id",
        "cost_component_replacement",
        "CostManifestReplacement",
    ),
}


def seed_members(session):
    from test_costing_services import (
        assignment,
        cost_owner,
        evidence,
        execute,
        receipt,
        review,
    )

    from reality.db import costing as models
    from reality.services import core
    from reality.services.costing import _hash, receipt_cost

    business = SimpleNamespace(tenant=core.create_tenant(session, "Manifest members"))
    tenant = business.tenant.id
    business.supplier = core.create_party(session, tenant, "Supplier", "supplier")
    business.item = core.create_item(session, tenant, "ITEM", "Item")
    business.location = core.create_location(session, tenant, "Warehouse")
    owner = cost_owner.__wrapped__(session, business)
    movement = receipt(session, business)
    first = execute(
        session,
        business,
        owner,
        assignment(session, business, movement, evidence(session, business), "1000"),
    )
    old = review(session, business, owner, movement, {"goods"})
    expected = receipt_cost(
        session, tenant, movement.id, manifest_id=old["manifest_id"]
    )
    execute(
        session,
        business,
        owner,
        assignment(
            session,
            business,
            movement,
            evidence(session, business, "900", "0"),
            "900",
            operation="replace",
            previous_component_basis_id=first["component_basis_id"],
        ),
    )
    core.correct_movement(session, tenant, movement.id, reason="Received correction")
    targets = {
        name: session.scalar(
            select(getattr(models, model).__table__.metadata.tables[target].c.id)
            .where(
                getattr(models, model).__table__.metadata.tables[target].c.tenant_id
                == tenant
            )
            .order_by(getattr(models, model).__table__.metadata.tables[target].c.id)
        )
        for name, (_, target, model) in FAMILIES.items()
    }
    assert all(targets.values())
    values = {
        key: [targets[name]]
        for name, key in (
            ("cost_manifest_receipt", "receipt"),
            ("cost_manifest_component", "component"),
            ("cost_manifest_attribution", "attribution"),
            ("cost_manifest_correction", "correction"),
            ("cost_manifest_replacement", "replacement"),
        )
    }
    manifests = []
    for number in range(2):
        manifest = models.CostInputManifest(
            tenant_id=tenant,
            id=core.uid("manifest"),
            target_event_sequence=expected["event_sequence"],
            effective_at=core.now(),
            knowledge_at=core.now(),
            input_schema_version=1,
            algorithm_version="receipt-v1",
            state="sealed",
            content_hash=_hash(values if number == 0 else {k: [] for k in values}),
            sealed_at=core.now(),
        )
        session.add(manifest)
        session.flush()
        manifests.append(manifest.id)
    for name, (column, _, model) in FAMILIES.items():
        session.add(
            getattr(models, model)(
                tenant_id=tenant,
                id="collision",
                manifest_id=manifests[0],
                **{column: targets[name]},
            )
        )
        session.flush()
    return tenant, targets, manifests, movement.id, old["manifest_id"], expected


def test_five_exact_interfaces_share_one_physical_store(session):
    from reality.db.core import Base
    from reality.db.schema_views import include_schema_object

    assert include_schema_object(None, "cost_manifest_member", "table", False, None)
    inspector = inspect(session.connection())
    assert "cost_manifest_member" in inspector.get_table_names()
    assert_database_fk_indexes(session.connection())
    assert not set(FAMILIES) & set(inspector.get_table_names())
    assert set(FAMILIES) <= set(inspector.get_view_names())
    for name in FAMILIES:
        assert not include_schema_object(None, name, "table", False, None)
        assert [c["name"] for c in inspector.get_columns(name)] == list(
            Base.metadata.tables[name].c.keys()
        )


def test_orm_and_sql_crud_preserve_family_and_tenant_namespaces(session):
    from reality.db import costing as models
    from reality.services.costing import receipt_cost

    tenant, targets, manifests, movement, old, expected = seed_members(session)
    other, *_ = seed_members(session)
    assert receipt_cost(session, tenant, movement, manifest_id=old) == expected
    for name, (column, _, model) in FAMILIES.items():
        cls = getattr(models, model)
        temporary = cls(
            tenant_id=tenant,
            id="orm-insert",
            manifest_id=manifests[1],
            **{column: targets[name]},
        )
        session.add(temporary)
        session.flush()
        session.delete(temporary)
        session.flush()
        row = session.get(cls, (tenant, "collision"))
        row.manifest_id = manifests[1]
        session.flush()
        session.expire(row)
        assert row.manifest_id == manifests[1]
        assert (
            session.execute(
                text(
                    f"UPDATE {name} SET manifest_id=:m WHERE tenant_id=:t AND id='collision' RETURNING {column}"
                ),
                {"m": manifests[0], "t": tenant},
            ).scalar_one()
            == targets[name]
        )
        assert (
            session.execute(
                text(
                    f"DELETE FROM {name} WHERE tenant_id=:t AND id='collision' RETURNING id"
                ),
                {"t": tenant},
            ).scalar_one()
            == "collision"
        )
        assert session.execute(
            text(
                f"INSERT INTO {name} (tenant_id,id,manifest_id,{column}) VALUES (:t,'collision',:m,:v) RETURNING id,{column}"
            ),
            {"t": tenant, "m": manifests[0], "v": targets[name]},
        ).one() == ("collision", targets[name])
        session.expire_all()
        assert session.get(cls, (other, "collision")) is not None
    assert (
        session.scalar(
            text("SELECT count(*) FROM cost_manifest_member WHERE id='collision'")
        )
        == 10
    )


def test_members_reject_wrong_links_duplicates_and_shapes(session):
    tenant, targets, manifests, *_ = seed_members(session)
    other, other_targets, other_manifests, *_ = seed_members(session)
    for name, (column, _, _) in FAMILIES.items():
        for manifest, target in (
            (manifests[0], targets[name]),
            (other_manifests[0], targets[name]),
            (manifests[0], other_targets[name]),
            (manifests[0], "missing"),
        ):
            with pytest.raises(DBAPIError), session.begin_nested():
                session.execute(
                    text(
                        f"INSERT INTO {name} (tenant_id,id,manifest_id,{column}) VALUES (:t,'invalid',:m,:v)"
                    ),
                    {"t": tenant, "m": manifest, "v": target},
                )
        with session.begin_nested():
            session.execute(
                text(
                    f"INSERT INTO {name} (tenant_id,id,manifest_id,{column}) VALUES (:t,'second-manifest',:m,:v)"
                ),
                {"t": tenant, "m": manifests[1], "v": targets[name]},
            )
        with pytest.raises(DBAPIError), session.begin_nested():
            session.execute(
                text(
                    f"UPDATE {name} SET {column}=NULL WHERE tenant_id=:t AND id='collision'"
                ),
                {"t": tenant},
            )
    for family, receipt_target, component_target in (
        ("unknown", targets["cost_manifest_receipt"], None),
        ("cost_manifest_receipt", None, None),
        (
            "cost_manifest_receipt",
            targets["cost_manifest_receipt"],
            targets["cost_manifest_component"],
        ),
    ):
        with pytest.raises(DBAPIError), session.begin_nested():
            session.execute(
                text(
                    "INSERT INTO cost_manifest_member (tenant_id,member_family,id,manifest_id,receipt_basis_id,component_basis_id) VALUES (:t,:f,'shape',:m,:r,:c)"
                ),
                {
                    "t": tenant,
                    "f": family,
                    "m": manifests[0],
                    "r": receipt_target,
                    "c": component_target,
                },
            )
    assert other != tenant


def test_partial_metadata_lifecycle_and_exact_columns(postgres_database):
    from sqlalchemy import create_engine

    from reality.db.core import Base

    engine = create_engine(postgres_database)
    store = Base.metadata.tables["cost_manifest_member"]
    # Every true FK target is needed; recursively include parents without unrelated views.
    selected = set()

    def add(table):
        if table in selected:
            return
        selected.add(table)
        for fk in table.foreign_key_constraints:
            add(fk.referred_table)

    add(store)
    selected.update(Base.metadata.tables[n] for n in FAMILIES)
    try:
        Base.metadata.create_all(engine, tables=list(selected))
        Base.metadata.create_all(engine, tables=list(selected))
        assert set(FAMILIES) <= set(inspect(engine).get_view_names())
        Base.metadata.drop_all(engine, tables=list(selected))
        with engine.connect() as connection:
            assert (
                connection.scalar(
                    text(
                        "SELECT count(*) FROM pg_proc WHERE proname LIKE 'insert_cost_manifest_%'"
                    )
                )
                == 0
            )
        Base.metadata.create_all(engine, tables=list(selected))
        Base.metadata.drop_all(engine, tables=list(selected))
    finally:
        engine.dispose()


def test_count_and_purge_visit_physical_members_once(session):
    from reality.db import costing as models
    from reality.services.account_deletion import _tenant_record_count
    from reality.services.core import _purge_tenant_records

    tenant, targets, manifests, *_ = seed_members(session)
    other, *_ = seed_members(session)
    before = _tenant_record_count(session, tenant)
    for name, (column, _, model) in FAMILIES.items():
        session.add(
            getattr(models, model)(
                tenant_id=tenant,
                id="additional",
                manifest_id=manifests[1],
                **{column: targets[name]},
            )
        )
        session.flush()
    assert _tenant_record_count(session, tenant) == before + 5
    other_count = _tenant_record_count(session, other)
    _purge_tenant_records(session, tenant)
    assert (
        session.scalar(
            text("SELECT count(*) FROM cost_manifest_member WHERE tenant_id=:t"),
            {"t": tenant},
        )
        == 0
    )
    assert _tenant_record_count(session, other) == other_count


def test_physical_foreign_keys_have_unconditional_full_key_indexes():
    from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint

    from reality.db.core import Base

    storage = Base.metadata.tables["cost_manifest_member"]
    covered = {
        tuple(c.name for c in index.columns)
        for index in storage.indexes
        if index.dialect_options["postgresql"].get("where") is None
    }
    covered |= {
        tuple(c.name for c in constraint.columns)
        for constraint in storage.constraints
        if isinstance(constraint, (PrimaryKeyConstraint, UniqueConstraint))
    }
    for foreign_key in storage.foreign_key_constraints:
        columns = tuple(c.name for c in foreign_key.columns)
        assert any(existing[: len(columns)] == columns for existing in covered), columns


def assert_database_fk_indexes(connection):
    inspector = inspect(connection)
    name = "cost_manifest_member"
    covered = {
        tuple(index["column_names"])
        for index in inspector.get_indexes(name)
        if not index.get("dialect_options", {}).get("postgresql_where")
    }
    covered.add(tuple(inspector.get_pk_constraint(name)["constrained_columns"]))
    covered |= {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints(name)
    }
    for fk in inspector.get_foreign_keys(name):
        columns = tuple(fk["constrained_columns"])
        assert any(index[: len(columns)] == columns for index in covered), columns
