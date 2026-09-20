"""A bounded selection preserves each independently reviewed inventory basis."""

from types import SimpleNamespace

import pytest
import test_inventory_generations as fixtures
from sqlalchemy import event, select

from reality.db.core import Item
from reality.db.cost_generations import CostInventoryPublication, CostInventorySnapshot
from reality.services import core, costing

cost_owner = fixtures.cost_owner


def build(session, business, owner):
    review = fixtures.reviewed(session, business, owner)
    return costing.build_inventory_generation(session, business.tenant.id, review)[
        "generation_id"
    ]


def test_selection_retains_distinct_item_bases(
    session, business, cost_owner, monkeypatch
):
    tenant = business.tenant.id
    first = build(session, business, cost_owner)
    other = SimpleNamespace(**vars(business))
    other.item = core.create_item(session, tenant, "SECOND", "Second item")
    second = build(session, other, cost_owner)
    expected = sorted(
        [
            costing.inventory_cost_snapshot(
                session, tenant, business.item.id, generation_id=first
            ),
            costing.inventory_cost_snapshot(
                session, tenant, other.item.id, generation_id=second
            ),
        ],
        key=lambda row: row["generation_id"],
    )
    assert (
        expected[0]["context"]["knowledge_at"] != expected[1]["context"]["knowledge_at"]
    )

    def forbidden(*args, **kwargs):
        pytest.fail("Historical selection attempted replay or live cursor lookup")

    monkeypatch.setattr(
        "reality.services.inventory_generations.inventory_cost", forbidden
    )
    monkeypatch.setattr("reality.services.inventory_generations._sequence", forbidden)
    result = costing.inventory_cost_snapshots(session, tenant, [second, first])
    assert result == {
        "mode": "historical_selection",
        "count": 2,
        "rows": expected,
        "persistence": {"business_writes": False, "projection_writes": False},
    }
    assert costing.inventory_cost_snapshots(session, tenant, (first, second)) == result
    # Exact immutable generation selection never follows a publication pointer.
    pointer = session.scalar(
        select(CostInventoryPublication).where(
            CostInventoryPublication.tenant_id == tenant,
            CostInventoryPublication.generation_id == first,
        )
    )
    session.delete(pointer)
    session.flush()
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    assert costing.inventory_cost_snapshots(session, tenant, [first, second]) == result


def test_selection_foreign_missing_members_refuse_equally(
    session, business, cost_owner
):
    tenant = business.tenant.id
    generation = build(session, business, cost_owner)
    foreign = core.create_tenant(session, "Foreign selection")
    errors = []
    for selected_tenant, ids in (
        (foreign.id, [generation]),
        (foreign.id, ["absent"]),
        (tenant, [generation, "absent"]),
    ):
        with pytest.raises(core.NotFound) as error:
            costing.inventory_cost_snapshots(session, selected_tenant, ids)
        errors.append(str(error.value))
    assert len(set(errors)) == 1
    assert generation not in errors[0]


def test_selection_two_queries_without_flush_or_replay(session, business, cost_owner):
    tenant = business.tenant.id
    first = build(session, business, cost_owner)
    other = SimpleNamespace(**vars(business))
    other.item = core.create_item(session, tenant, "SECOND", "Second item")
    second = build(session, other, cost_owner)
    pending = Item(
        id=core.uid("itm"), tenant_id=tenant, sku="PENDING", name="Pending", unit="pcs"
    )
    session.add(pending)
    statements = []

    def watch(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    event.listen(session.bind, "before_cursor_execute", watch)
    try:
        for ids in ([first], [first, second]):
            statements.clear()
            costing.inventory_cost_snapshots(session, tenant, ids)
            assert len(statements) <= 2
            assert all(s.lstrip().startswith("select") for s in statements)
            assert not any(
                "cost_inventory_member" in s
                or "business_event" in s
                or "cost_inventory_publication" in s
                for s in statements
            )
            assert pending in session.new
    finally:
        event.remove(session.bind, "before_cursor_execute", watch)


def test_selection_corrupt_member_refuses_whole_result(session, business, cost_owner):
    tenant = business.tenant.id
    generation = build(session, business, cost_owner)
    row = session.scalar(
        select(CostInventorySnapshot).where(
            CostInventorySnapshot.tenant_id == tenant,
            CostInventorySnapshot.generation_id == generation,
        )
    )
    row.acquisition_value += 1
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity mismatch"):
        costing.inventory_cost_snapshots(session, tenant, [generation])


@pytest.mark.parametrize(
    "ids",
    [
        [],
        (),
        "abc",
        {"abc"},
        [""],
        [" "],
        [1],
        [True],
        [None],
        ["one", "one"],
        [str(i) for i in range(101)],
    ],
)
def test_selection_invalid_shape_refuses_before_database(ids):
    class NoDatabase:
        def __getattr__(self, name):
            pytest.fail("Invalid selection accessed the database")

    with pytest.raises(core.InvalidOperation, match="selection"):
        costing.inventory_cost_snapshots(NoDatabase(), "tenant", ids)


def test_selection_accepts_upper_bound_without_silent_truncation(session, business):
    # All 100 IDs are admissible input, but missing members must refuse, not truncate.
    with pytest.raises(core.NotFound, match="selection not found"):
        costing.inventory_cost_snapshots(
            session, business.tenant.id, [f"absent-{index}" for index in range(100)]
        )
