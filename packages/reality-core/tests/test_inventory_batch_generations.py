"""Joint inventory values require every member of the real confirmed action."""

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from types import SimpleNamespace

import pytest
import test_inventory_batch_review as fixtures
from conftest import record_by_id
from sqlalchemy import delete, event, select

from reality.db.core import AppUser, ChangeProposal, Item, Tenant
from reality.db.cost_generations import (
    CostInventoryGeneration,
    CostInventoryPublication,
    CostInventorySnapshot,
)
from reality.jobs.registry import get_definition
from reality.services import core, costing, scheduled_jobs

cost_owner = fixtures.cost_owner


def confirmed(session, business, owner):
    args = fixtures.prepared(session, business, owner)
    action, result = fixtures.fixtures.commit_review(session, business, owner, args)
    return action.id, [r["review_id"] for r in result["reviews"]]


def test_joint_partial_complete_retry_and_freshness(session, business, cost_owner):
    tenant = business.tenant.id
    action, reviews = confirmed(session, business, cost_owner)
    blank = costing.inventory_batch_snapshot(session, tenant, action)
    assert blank["freshness"]["state"] == "uninitialized"
    assert blank["result"] is None and blank["rows"] == []
    assert blank["coverage"] == {"expected_items": 2, "available_items": 0}
    costing.build_inventory_generation(session, tenant, reviews[0])
    partial = costing.inventory_batch_snapshot(session, tenant, action)
    assert partial["result"] is None and partial["coverage"]["available_items"] == 1
    built = costing.build_inventory_batch_generation(session, tenant, action)
    assert built["created"] == 1
    historical = costing.inventory_batch_snapshot(session, tenant, action)
    assert historical["result"] == {
        "acquisition_value": "840.0000",
        "currency": "EUR",
        "quantities": [
            {"base_unit": "kg", "remaining_quantity": "40.0000"},
            {"base_unit": "pcs", "remaining_quantity": "40.0000"},
        ],
        "carrying_value": None,
        "carrying_value_state": "assessment_not_supported",
    }
    assert historical["freshness"]["state"] == "historical"
    assert len(historical["generation_ids"]) == len(historical["rows"]) == 2
    assert (
        costing.build_inventory_batch_generation(session, tenant, action)["created"]
        == 0
    )
    assert (
        costing.inventory_batch_snapshot(session, tenant, action, mode="current")[
            "freshness"
        ]["state"]
        == "ready"
    )
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    current = costing.inventory_batch_snapshot(session, tenant, action, mode="current")
    assert current["freshness"]["state"] == "pending"
    assert current["result"] is None and current["rows"] == []
    assert current["basis_result"] == historical["result"]
    assert (
        costing.inventory_batch_snapshot(
            session, tenant, action, mode="current", allow_previous=True
        )["result"]
        == historical["result"]
    )
    assert costing.inventory_batch_snapshot(session, tenant, action) == historical


def test_joint_foreign_and_unconfirmed_actions_refuse(session, business, cost_owner):
    tenant = business.tenant.id
    action, _ = confirmed(session, business, cost_owner)
    foreign = core.create_tenant(session, "Foreign")
    for caller_tenant, identity in ((foreign.id, action), (tenant, "absent")):
        for fn in (
            costing.inventory_batch_snapshot,
            costing.build_inventory_batch_generation,
        ):
            with pytest.raises(core.NotFound):
                fn(session, caller_tenant, identity)
    args = json.loads(record_by_id(session, ChangeProposal, action).input)
    args["expected_event_sequence"] = costing._sequence(session, tenant)
    proposal = fixtures.propose(session, tenant, cost_owner, args)
    with pytest.raises(core.NotFound):
        costing.inventory_batch_snapshot(session, tenant, proposal.id)


def test_joint_second_build_failure_rolls_back(
    session, business, cost_owner, monkeypatch
):
    from reality.services import inventory_generations

    tenant = business.tenant.id
    action, _ = confirmed(session, business, cost_owner)
    original = inventory_generations._build
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise core.InvalidOperation("Injected joint build failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(inventory_generations, "_build", fail)
    with pytest.raises(core.InvalidOperation, match="Injected"):
        costing.build_inventory_batch_generation(session, tenant, action)
    assert (
        costing.inventory_batch_snapshot(session, tenant, action)["coverage"][
            "available_items"
        ]
        == 0
    )


def test_joint_bounded_read_no_flush_or_replay(
    session, business, cost_owner, monkeypatch
):
    tenant = business.tenant.id
    action, _ = confirmed(session, business, cost_owner)
    costing.build_inventory_batch_generation(session, tenant, action)
    pending = Item(
        id=core.uid("itm"), tenant_id=tenant, sku="PENDING", name="Pending", unit="pcs"
    )
    session.add(pending)
    statements = []

    def watch(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    def forbidden(*args, **kwargs):
        pytest.fail("A joint read attempted inventory replay")

    monkeypatch.setattr(
        "reality.services.inventory_generations.inventory_cost", forbidden
    )
    event.listen(session.bind, "before_cursor_execute", watch)
    try:
        result = costing.inventory_batch_snapshot(session, tenant, action)
        assert result["result"] is not None
    finally:
        event.remove(session.bind, "before_cursor_execute", watch)
    assert pending in session.new
    assert len(statements) <= 8
    assert all(s.lstrip().startswith("select") for s in statements)
    assert not any(
        "cost_inventory_member" in s or "max(business_event.sequence)" in s
        for s in statements
    )


def test_joint_corrupt_cache_refuses(session, business, cost_owner):
    tenant = business.tenant.id
    action, _ = confirmed(session, business, cost_owner)
    costing.build_inventory_batch_generation(session, tenant, action)
    row = session.scalar(
        select(CostInventorySnapshot).where(CostInventorySnapshot.tenant_id == tenant)
    )
    row.acquisition_value += 1
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        costing.inventory_batch_snapshot(session, tenant, action)


def prepare_committed(factory, tenant, actor):
    with factory() as session:
        business = SimpleNamespace(
            tenant=session.get(Tenant, tenant),
            company=core.create_party(session, tenant, "Company", "company"),
            supplier=core.create_party(session, tenant, "Supplier", "supplier"),
            item=core.create_item(session, tenant, "FIRST", "First"),
            location=core.create_location(session, tenant, "Warehouse"),
        )
        action, _ = confirmed(session, business, session.get(AppUser, actor))
        session.commit()
        return action, business.item.id, business.location.id


def test_joint_concurrent_builds_converge(scheduled_database):
    _, factory, tenant, actor = scheduled_database
    action, _, _ = prepare_committed(factory, tenant, actor)
    barrier = Barrier(2)

    def build(_):
        with factory.begin() as session:
            barrier.wait(timeout=10)
            return costing.build_inventory_batch_generation(session, tenant, action)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(build, range(2)))
    assert sum(r["created"] for r in results) == 2
    assert results[0]["generation_ids"] == results[1]["generation_ids"]


def test_joint_atomic_visibility_and_late_intake(scheduled_database, monkeypatch):
    from reality.services import inventory_generations

    _, factory, tenant, actor = scheduled_database
    action, item, location = prepare_committed(factory, tenant, actor)
    computed, resume_compute, published, resume_publish = (Event() for _ in range(4))
    original_cost = inventory_generations.inventory_cost
    original_build = inventory_generations._build
    computations, publications = [], []

    def cost(*args, **kwargs):
        result = original_cost(*args, **kwargs)
        computations.append(1)
        if len(computations) == 2:
            computed.set()
            assert resume_compute.wait(timeout=10)
        return result

    def publish(*args, **kwargs):
        assert len(computations) == 2, (
            "Cache publication started before all replay finished"
        )
        result = original_build(*args, **kwargs)
        publications.append(1)
        if len(publications) == 1:
            published.set()
            assert resume_publish.wait(timeout=10)
        return result

    monkeypatch.setattr(inventory_generations, "inventory_cost", cost)
    monkeypatch.setattr(inventory_generations, "_build", publish)

    def build():
        with factory.begin() as session:
            return costing.build_inventory_batch_generation(session, tenant, action)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(build)
        try:
            assert computed.wait(timeout=10)
            with factory.begin() as session:
                core.record_movement(
                    session, tenant, "receipt", item, "1", to_location_id=location
                )
            resume_compute.set()
            assert published.wait(timeout=10)
            with factory() as session:
                result = costing.inventory_batch_snapshot(session, tenant, action)
                assert result["result"] is None
                assert result["coverage"]["available_items"] == 0
        finally:
            resume_compute.set()
            resume_publish.set()
        future.result(timeout=15)
    with factory() as session:
        assert (
            costing.inventory_batch_snapshot(session, tenant, action, mode="current")[
                "freshness"
            ]["state"]
            == "pending"
        )
        assert (
            costing.inventory_batch_snapshot(session, tenant, action)["result"][
                "acquisition_value"
            ]
            == "840.0000"
        )


def test_joint_real_worker_and_legacy_config(scheduled_database):
    from reality.jobs.runtime import ProcessLoop

    definition = get_definition("costing.inventory.refresh")
    assert definition.config_model.model_validate({"review_id": "old"}).model_dump(
        mode="json"
    ) == {"review_id": "old"}
    engine, factory, tenant, actor = scheduled_database
    action, _, _ = prepare_committed(factory, tenant, actor)
    with factory.begin() as session:
        scheduled_jobs.create_manual_run(
            session,
            tenant,
            actor,
            "costing.inventory.refresh",
            {"action_id": action},
            request_id="joint-worker",
        )
    assert (
        ProcessLoop("worker", tenant_id=tenant).sweep(
            engine, max_runs=1, max_seconds=25
        )["succeeded"]
        == 1
    )
    with factory() as session:
        assert (
            costing.inventory_batch_snapshot(session, tenant, action)["result"][
                "acquisition_value"
            ]
            == "840.0000"
        )


def test_joint_zero_inventory_is_complete_not_missing(session, business, cost_owner):
    tenant = business.tenant.id
    args = fixtures.prepared(session, business, cost_owner)
    for scope in args["scopes"]:
        issue = core.record_movement(
            session,
            tenant,
            "shipment",
            scope["item_id"],
            "40",
            from_location_id=business.location.id,
        )
        scope["economic_issue_ids"].append(issue.id)
    cutoff = core.now().isoformat()
    for scope in args["scopes"]:
        scope["effective_at"] = cutoff
    args["expected_event_sequence"] = costing._sequence(session, tenant)
    action, _ = fixtures.fixtures.commit_review(session, business, cost_owner, args)
    costing.build_inventory_batch_generation(session, tenant, action.id)
    result = costing.inventory_batch_snapshot(session, tenant, action.id)
    assert result["coverage"] == {"expected_items": 2, "available_items": 2}
    assert result["result"]["acquisition_value"] == "0.0000"
    assert all(
        row["remaining_quantity"] == "0.0000" for row in result["result"]["quantities"]
    )


def test_joint_single_review_cannot_be_relabelled(session, business, cost_owner):
    args, _, _ = fixtures.fixtures.prepared(session, business, cost_owner)
    action, _ = fixtures.fixtures.commit_review(session, business, cost_owner, args)
    for fn in (
        costing.inventory_batch_snapshot,
        costing.build_inventory_batch_generation,
    ):
        with pytest.raises(core.NotFound):
            fn(session, business.tenant.id, action.id)


def test_joint_corrupt_membership_refuses(session, business, cost_owner):
    tenant = business.tenant.id
    action, _ = confirmed(session, business, cost_owner)
    costing.build_inventory_batch_generation(session, tenant, action)
    row = record_by_id(session, ChangeProposal, action)
    payload = json.loads(row.output)
    payload["reviews"].pop()
    row.output = json.dumps(payload)
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        costing.inventory_batch_snapshot(session, tenant, action)


def test_joint_deadline_and_config_guards(session, business, cost_owner):
    from datetime import timedelta

    from pydantic import ValidationError

    from reality.jobs.registry import JobError

    tenant = business.tenant.id
    action, _ = confirmed(session, business, cost_owner)
    with pytest.raises(JobError, match="handler_timeout"):
        costing.build_inventory_batch_generation(
            session, tenant, action, deadline=core.now() - timedelta(seconds=1)
        )
    assert (
        costing.inventory_batch_snapshot(session, tenant, action)["coverage"][
            "available_items"
        ]
        == 0
    )
    model = get_definition("costing.inventory.refresh").config_model
    for config in ({}, {"review_id": "review", "action_id": action}, {"action_id": ""}):
        with pytest.raises(ValidationError):
            model.model_validate(config)
    for options in ({"mode": "latest"}, {"allow_previous": 1}):
        with pytest.raises(core.InvalidOperation):
            costing.inventory_batch_snapshot(session, tenant, action, **options)


def test_joint_disappearing_cache_never_replays_during_publication(
    session, business, cost_owner, monkeypatch
):
    from reality.services import inventory_generations

    tenant = business.tenant.id
    action, reviews = confirmed(session, business, cost_owner)
    existing = costing.build_inventory_generation(session, tenant, reviews[0])[
        "generation_id"
    ]
    original = inventory_generations._build

    def remove_cache(session, tenant, review_id, **kwargs):
        if review_id == reviews[0]:
            for model in (CostInventoryPublication, CostInventorySnapshot):
                session.execute(
                    delete(model).where(
                        model.tenant_id == tenant, model.generation_id == existing
                    )
                )
            session.execute(
                delete(CostInventoryGeneration).where(
                    CostInventoryGeneration.tenant_id == tenant,
                    CostInventoryGeneration.id == existing,
                )
            )
        return original(session, tenant, review_id, **kwargs)

    monkeypatch.setattr(inventory_generations, "_build", remove_cache)
    with pytest.raises(core.Conflict, match="cache changed"):
        costing.build_inventory_batch_generation(session, tenant, action)
    # The injected mutation and any earlier member publication share the savepoint.
    assert (
        costing.inventory_batch_snapshot(session, tenant, action)["coverage"][
            "available_items"
        ]
        == 1
    )
