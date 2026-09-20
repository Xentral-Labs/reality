"""The reporting SQL source reuses exact persisted inventory observations."""

from datetime import datetime
from decimal import Decimal

import pytest
import test_inventory_batch_generations as fixtures
from sqlalchemy import Numeric, delete, func, select

from reality.db.core import Item
from reality.db.cost_generations import CostInventoryPublication
from reality.services import core, costing
from reality.services.analytics import costing_relation

cost_owner = fixtures.cost_owner


def stored(session, business, owner):
    action, _ = fixtures.confirmed(session, business, owner)
    ids = costing.build_inventory_batch_generation(session, business.tenant.id, action)[
        "generation_ids"
    ]
    return action, ids


def test_relation_sql_parity_grain_and_partitions(session, business, cost_owner):
    tenant = business.tenant.id
    action, ids = stored(session, business, cost_owner)
    relation = costing_relation.inventory_selection_relation(tenant, ids).subquery()
    rows = (
        session.execute(select(relation).order_by(relation.c.generation_id))
        .mappings()
        .all()
    )
    observations = costing.inventory_cost_snapshots(session, tenant, ids)["rows"]
    assert len(rows) == len({row["snapshot_id"] for row in rows}) == 2
    for row, observed in zip(rows, observations, strict=True):
        assert row["tenant_id"] == tenant
        assert row["review_action_id"] == action
        for key in ("generation_id",):
            assert row[key] == observed[key]
        for key in (
            "item_id",
            "review_id",
            "policy_revision_id",
            "owner_party_id",
            "currency",
            "base_unit",
            "method",
            "algorithm_version",
        ):
            assert row[key] == observed["context"][key]
        for key in ("effective_at", "knowledge_at", "completed_at"):
            assert row[key] == datetime.fromisoformat(observed["context"][key])
        assert (
            row["processed_event_sequence"]
            == observed["freshness"]["processed_event_sequence"]
        )
        assert row["acquisition_value"] == Decimal(
            observed["result"]["acquisition_value"]
        )
        assert row["remaining_quantity"] == Decimal(
            observed["result"]["remaining_quantity"]
        )
    assert isinstance(relation.c.acquisition_value.type, Numeric)
    assert relation.c.acquisition_value.type.scale == 4
    assert relation.c.remaining_quantity.type.scale == 4
    grouped = session.execute(
        select(
            relation.c.currency,
            relation.c.base_unit,
            func.sum(relation.c.remaining_quantity),
            func.sum(relation.c.acquisition_value),
        )
        .group_by(relation.c.currency, relation.c.base_unit)
        .order_by(relation.c.base_unit)
    ).all()
    assert grouped == [
        ("EUR", "kg", Decimal("40.0000"), Decimal("420.0000")),
        ("EUR", "pcs", Decimal("40.0000"), Decimal("420.0000")),
    ]
    total = session.scalar(select(func.sum(relation.c.acquisition_value)))
    assert total == Decimal(
        costing.inventory_batch_snapshot(session, tenant, action)["result"][
            "acquisition_value"
        ]
    )


def test_relation_foreign_missing_and_partial_membership(session, business, cost_owner):
    tenant = business.tenant.id
    _, ids = stored(session, business, cost_owner)
    foreign = core.create_tenant(session, "Other company")
    for caller_tenant, chosen in ((foreign.id, ids), (tenant, ["absent"])):
        relation = costing_relation.inventory_selection_relation(
            caller_tenant, chosen
        ).subquery()
        assert session.execute(select(relation)).all() == []
        assert session.scalar(select(func.sum(relation.c.acquisition_value))) is None
    # The low-level relation does not certify coverage; the shared reader must refuse.
    assert (
        len(
            session.execute(
                costing_relation.inventory_selection_relation(
                    tenant, [ids[0], "absent"]
                )
            ).all()
        )
        == 1
    )
    with pytest.raises(core.NotFound):
        costing.inventory_cost_snapshots(session, tenant, [ids[0], "absent"])


def test_relation_preserves_retained_units_and_exact_ids(session, business, cost_owner):
    tenant = business.tenant.id
    _, ids = stored(session, business, cost_owner)
    query = costing_relation.inventory_selection_relation(tenant, ids).order_by(
        "generation_id"
    )
    before = session.execute(query).mappings().all()
    item = session.get(Item, business.item.id)
    item.unit = "changed-master-unit"
    session.execute(
        delete(CostInventoryPublication).where(
            CostInventoryPublication.tenant_id == tenant,
            CostInventoryPublication.generation_id.in_(ids),
        )
    )
    session.flush()
    core.record_movement(
        session, tenant, "receipt", item.id, "1", to_location_id=business.location.id
    )
    assert session.execute(query).mappings().all() == before
    assert {row["base_unit"] for row in before} == {"kg", "pcs"}


@pytest.mark.parametrize(
    "ids",
    [
        [],
        (),
        "id",
        {"id"},
        [""],
        [" "],
        [None],
        [True],
        ["same", "same"],
        [str(i) for i in range(101)],
    ],
)
def test_relation_rejects_invalid_selection_before_sql(ids):
    with pytest.raises(core.InvalidOperation, match="selection"):
        costing_relation.inventory_selection_relation("tenant", ids)
