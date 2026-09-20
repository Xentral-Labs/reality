"""Historical joint DB observations are disposable, complete and tenant-pinned."""

import json
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from datetime import timedelta
from threading import Barrier, Event
from types import SimpleNamespace

import pytest
import test_contribution_batch_review as fixtures
from sqlalchemy import delete, event, func, select

from reality.db.contribution import CostContributionReview, CostRevenueMatchBasis
from reality.db.core import AppUser, ChangeProposal, Item, Tenant, TenantMembership
from reality.db.cost_generations import (
    CostContributionGeneration,
    CostContributionSnapshot,
)
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.jobs.registry import JobError
from reality.services import core, costing, scheduled_jobs

cost_owner = fixtures.cost_owner


def confirmed(session, business, owner):
    args, _, _ = fixtures.prepared(session, business, owner)
    action, result = fixtures.stock.commit_review(session, business, owner, args)
    return action.id, result


def count(session, model, tenant):
    return session.scalar(
        select(func.count()).select_from(model).where(model.tenant_id == tenant)
    )


def test_cache_parity_no_replay_read_and_retry(
    session, business, cost_owner, monkeypatch
):
    tenant = business.tenant.id
    action, original = confirmed(session, business, cost_owner)
    blank = costing.contribution_snapshot(session, tenant, action)
    assert blank["state"] == "uninitialized" and blank["rows"] == blank["groups"] == []
    before = count(session, CostContributionReview, tenant)
    built = costing.build_contribution_generation(session, tenant, action)
    assert built["created"] and built["contribution_rows"] == 2
    assert count(session, CostContributionReview, tenant) == before

    def forbidden(*args, **kwargs):
        pytest.fail("Historical cache attempted financial replay")

    monkeypatch.setattr(
        "reality.services.contribution_generations.reviewed_contribution", forbidden
    )
    assert (
        costing.build_contribution_generation(session, tenant, action)["created"]
        is False
    )
    pending = Item(
        id=core.uid("item"), tenant_id=tenant, sku="PENDING", name="Pending", unit="pcs"
    )
    session.add(pending)
    statements = []

    def watch(conn, cursor, statement, *rest):
        statements.append(statement.lower())

    event.listen(session.bind, "before_cursor_execute", watch)
    try:
        cached = costing.contribution_snapshot(session, tenant, action)
    finally:
        event.remove(session.bind, "before_cursor_execute", watch)
    assert pending in session.new
    session.expunge(pending)
    assert len(statements) <= 10
    assert all(s.lstrip().startswith("select") for s in statements)
    assert not any("max(business_event.sequence)" in s for s in statements)
    assert cached["generation_id"] == built["generation_id"]
    assert cached["coverage"] == {"expected_positions": 2, "available_positions": 2}
    expected = {r["review_id"]: r for r in original["reviews"]}
    assert len(cached["rows"]) == len(cached["groups"]) == 2
    for row in cached["rows"]:
        reviewed = expected[row["review_id"]]
        assert row["db1_total"] == reviewed["db1"]
        assert row["db2_total"] == reviewed["db2"]
        assert row["db1_rate"] == reviewed["db1_rate"]
        assert row["db2_covered"] == int(reviewed["db2"] is not None)
        assert row["known_direct_selling_cost"] == reviewed["known_direct_selling_cost"]
    assert {g["base_unit"] for g in cached["groups"]} == {"pcs", "kg"}
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    assert costing.contribution_snapshot(session, tenant, action) == cached


def test_foreign_action_membership_and_corrupt_cache_refuse(
    session, business, cost_owner
):
    tenant = business.tenant.id
    action, original = confirmed(session, business, cost_owner)
    with pytest.raises(core.NotFound):
        costing.contribution_snapshot(session, tenant, original["inventory_action_id"])
    other = core.create_tenant(session, "Other")
    for fn in (costing.contribution_snapshot, costing.build_contribution_generation):
        for scope in (action, "absent"):
            with pytest.raises(core.NotFound):
                fn(session, other.id, scope)
    costing.build_contribution_generation(session, tenant, action)
    stored = session.scalar(
        select(CostContributionSnapshot).where(
            CostContributionSnapshot.tenant_id == tenant
        )
    )
    basis = session.scalar(
        select(CostRevenueMatchBasis).where(CostRevenueMatchBasis.tenant_id == tenant)
    )
    basis.stated_net += 1
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        costing.contribution_snapshot(session, tenant, action)
    basis.stated_net -= 1
    session.flush()
    stored.goods_cost += 1
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        costing.contribution_snapshot(session, tenant, action)
    stored.goods_cost -= 1
    session.flush()
    session.delete(stored)
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        costing.contribution_snapshot(session, tenant, action)
    parent = session.get(ChangeProposal, action)
    payload = json.loads(parent.output)
    payload["reviews"].pop()
    parent.output = json.dumps(payload)
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        costing.build_contribution_generation(session, tenant, action)


def test_failed_second_calculation_and_deadline_publish_nothing(
    session, business, cost_owner, monkeypatch
):
    from reality.services import contribution_generations

    tenant = business.tenant.id
    action, _ = confirmed(session, business, cost_owner)
    with pytest.raises(JobError, match="handler_timeout"):
        costing.build_contribution_generation(
            session, tenant, action, deadline=core.now() - timedelta(seconds=1)
        )
    original = contribution_generations.reviewed_contribution
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("second calculation failed")
        return original(*args, **kwargs)

    monkeypatch.setattr(contribution_generations, "reviewed_contribution", fail)
    with pytest.raises(RuntimeError, match="second calculation"):
        costing.build_contribution_generation(session, tenant, action)
    assert count(session, CostContributionGeneration, tenant) == 0
    assert count(session, CostContributionSnapshot, tenant) == 0
    monkeypatch.setattr(contribution_generations, "reviewed_contribution", original)
    original_flush = session.flush

    def fail_publication(*args, **kwargs):
        if any(isinstance(row, CostContributionSnapshot) for row in session.new):
            raise RuntimeError("cache publication failed")
        return original_flush(*args, **kwargs)

    monkeypatch.setattr(session, "flush", fail_publication)
    with pytest.raises(RuntimeError, match="cache publication"):
        costing.build_contribution_generation(session, tenant, action)
    monkeypatch.setattr(session, "flush", original_flush)
    assert count(session, CostContributionGeneration, tenant) == 0
    assert count(session, CostContributionSnapshot, tenant) == 0


def committed(factory, tenant, actor):
    with factory() as session:
        business = SimpleNamespace(
            tenant=session.get(Tenant, tenant),
            company=core.create_party(session, tenant, "Company", "company"),
            customer=core.create_party(session, tenant, "Customer", "company"),
            supplier=core.create_party(session, tenant, "Supplier", "company"),
            item=core.create_item(session, tenant, "FIRST", "First"),
            location=core.create_location(session, tenant, "Warehouse"),
        )
        action, _ = confirmed(session, business, session.get(AppUser, actor))
        session.commit()
        return action, business.item.id, business.location.id


def test_concurrent_builds_reuse_one_generation(scheduled_database):
    _, factory, tenant, actor = scheduled_database
    action, _, _ = committed(factory, tenant, actor)
    barrier = Barrier(2)

    def build(_):
        with factory.begin() as session:
            barrier.wait(timeout=10)
            return costing.build_contribution_generation(session, tenant, action)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(build, range(2)))
    assert sum(r["created"] for r in results) == 1
    assert results[0]["generation_id"] == results[1]["generation_id"]


def test_shared_worker_and_revoked_owner(scheduled_database):
    from reality.jobs.runtime import ProcessLoop

    engine, factory, tenant, actor = scheduled_database
    action, _, _ = committed(factory, tenant, actor)
    with factory.begin() as session:
        scheduled_jobs.create_manual_run(
            session,
            tenant,
            actor,
            "costing.contribution.refresh",
            {"action_id": action},
            request_id="contribution-worker",
        )
    assert (
        ProcessLoop("worker", tenant_id=tenant).sweep(
            engine, max_runs=1, max_seconds=25
        )["succeeded"]
        == 1
    )
    with factory.begin() as session:
        assert (
            costing.contribution_snapshot(session, tenant, action)["state"]
            == "historical"
        )
        scheduled_jobs.create_manual_run(
            session,
            tenant,
            actor,
            "costing.contribution.refresh",
            {"action_id": action},
            request_id="contribution-revoked",
        )
        membership = session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant, TenantMembership.user_id == actor
            )
        )
        membership.role = "member"
    assert (
        ProcessLoop("worker", tenant_id=tenant).sweep(
            engine, max_runs=1, max_seconds=25
        )["succeeded"]
        == 0
    )
    with factory() as session:
        revoked = session.scalar(
            select(ScheduledJobRun).where(
                ScheduledJobRun.tenant_id == tenant,
                ScheduledJobRun.request_id == "contribution-revoked",
            )
        )
        assert revoked.status == "failed"
        assert revoked.last_error_code == "not_authorized"


def test_cached_same_unit_total_preserves_partial_db2(session, business, cost_owner):
    args, _, _ = fixtures.prepared(session, business, cost_owner, second_unit="pcs")
    action, _ = fixtures.stock.commit_review(session, business, cost_owner, args)
    costing.build_contribution_generation(session, business.tenant.id, action.id)
    result = costing.contribution_snapshot(session, business.tenant.id, action.id)
    assert len(result["groups"]) == 1
    group = result["groups"][0]
    assert group["revenue_total"] == "2400.0000"
    assert group["db1_total"] == "1140.0000"
    assert group["db1_rate"] == "47.5000"
    assert group["db2_total"] is group["db2_rate"] is None
    assert group["db2_known"] == "570.0000"
    assert (group["db2_required"], group["db2_covered"]) == (2, 1)


def test_calculation_allows_intake_and_publication_is_atomic(
    scheduled_database, monkeypatch
):
    from reality.services import contribution_generations

    _, factory, tenant, actor = scheduled_database
    action, item, location = committed(factory, tenant, actor)
    computed, resume, published, commit = (Event() for _ in range(4))
    original_read, original_load = (
        contribution_generations.reviewed_contribution,
        contribution_generations._load,
    )
    calls = []

    def calculate(*args, **kwargs):
        result = original_read(*args, **kwargs)
        calls.append(1)
        if len(calls) == 2:
            computed.set()
            assert resume.wait(timeout=15)
        return result

    def load(*args, **kwargs):
        result = original_load(*args, **kwargs)
        if result is not None and not published.is_set():
            published.set()
            assert commit.wait(timeout=15)
        return result

    monkeypatch.setattr(contribution_generations, "reviewed_contribution", calculate)
    monkeypatch.setattr(contribution_generations, "_load", load)

    def build():
        with factory.begin() as session:
            return costing.build_contribution_generation(session, tenant, action)

    def intake():
        with factory.begin() as session:
            core.record_movement(
                session, tenant, "receipt", item, "1", to_location_id=location
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        task = pool.submit(build)
        try:
            assert computed.wait(timeout=15)
            pool.submit(intake).result(timeout=10)
            resume.set()
            assert published.wait(timeout=15)
            with factory() as session:
                assert (
                    costing.contribution_snapshot(session, tenant, action)["state"]
                    == "uninitialized"
                )
        finally:
            resume.set()
            commit.set()
        assert task.result(timeout=15)["created"]
    with factory() as session:
        assert len(costing.contribution_snapshot(session, tenant, action)["rows"]) == 2


def test_pinned_reader_protects_cache_while_intake_proceeds(scheduled_database):
    _, factory, tenant, actor = scheduled_database
    action, item, location = committed(factory, tenant, actor)
    with factory.begin() as session:
        costing.build_contribution_generation(session, tenant, action)
    started = Event()

    def evict():
        with factory.begin() as session:
            started.set()
            generation = session.scalar(
                select(CostContributionGeneration)
                .where(
                    CostContributionGeneration.tenant_id == tenant,
                    CostContributionGeneration.action_id == action,
                )
                .with_for_update()
            )
            session.execute(
                delete(CostContributionSnapshot).where(
                    CostContributionSnapshot.tenant_id == tenant,
                    CostContributionSnapshot.generation_id == generation.id,
                )
            )
            session.delete(generation)

    def intake():
        with factory.begin() as session:
            core.record_movement(
                session, tenant, "receipt", item, "1", to_location_id=location
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        with factory.begin() as reader:
            result = costing.contribution_snapshot(reader, tenant, action)
            task = pool.submit(evict)
            assert started.wait(timeout=10)
            with pytest.raises(FutureTimeout):
                task.result(timeout=0.2)
            pool.submit(intake).result(timeout=10)
            assert len(result["rows"]) == 2
        task.result(timeout=10)
    with factory() as session:
        assert (
            costing.contribution_snapshot(session, tenant, action)["state"]
            == "uninitialized"
        )


def test_cached_fixture_a_preserves_direct_and_allocated_selling(
    session, business, cost_owner
):
    import test_selling_costs as selling

    tenant = business.tenant.id
    args, data, inventory_action = fixtures.prepared(
        session, business, cost_owner, second_unit="pcs"
    )
    document = selling.costs.evidence(session, business, "114", "0")
    assignment = selling.selling(session, business, data[0][0], document)
    assignment["parts"] = [
        assignment["parts"][0] | {"source_share": "100"},
        assignment["parts"][0]
        | {
            "source_share": "14",
            "category": "payment_fee",
            "assignment_kind": "allocated",
        },
    ]
    fixtures.stock.commit_review(session, business, cost_owner, assignment)
    inventory_args = json.loads(session.get(ChangeProposal, inventory_action).input)
    cutoff = core.now().isoformat()
    for scope in inventory_args["scopes"]:
        scope["effective_at"] = cutoff
    inventory_args["expected_event_sequence"] = costing._sequence(session, tenant)
    fixtures.stock.commit_review(session, business, cost_owner, inventory_args)
    for position in args["positions"]:
        candidate = costing.contribution_preview(
            session, tenant, position["document_line_id"]
        )
        position["expected_candidate_hash"] = candidate["candidate_hash"]
        if position["document_line_id"] == data[0][0].id:
            position["selling_categories"] = selling.categories(
                "outbound_freight", "payment_fee"
            )
    args["expected_event_sequence"] = costing._sequence(session, tenant)
    action, _ = fixtures.stock.commit_review(session, business, cost_owner, args)
    costing.build_contribution_generation(session, tenant, action.id)
    result = costing.contribution_snapshot(session, tenant, action.id)
    row = next(
        row for row in result["rows"] if row["document_line_id"] == data[0][0].id
    )
    assert (
        row["known_direct_selling_cost"]
        == row["direct_selling_cost_total"]
        == "100.0000"
    )
    assert (
        row["known_allocated_selling_cost"]
        == row["allocated_selling_cost_total"]
        == "14.0000"
    )
    assert row["db1_total"] == "570.0000"
    assert row["db2_total"] == "456.0000"
    assert row["db2_rate"] == "38.0000"
    assert result["groups"][0]["db2_total"] is None
    assert result["groups"][0]["db2_known"] == "456.0000"
