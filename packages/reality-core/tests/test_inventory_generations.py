"""Stored inventory observations use retained authority and the shared worker."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from types import SimpleNamespace

import pytest
import test_carrying_value_services as carrying
import test_inventory_costing_services as fixtures
from sqlalchemy import event, func, select

from reality.db.core import AppUser, Item, Tenant, TenantMembership
from reality.db.cost_generations import (
    CostInventoryGeneration,
    CostInventoryPublication,
    CostInventorySnapshot,
)
from reality.db.inventory_costing import CostInventoryReview
from reality.jobs.registry import JobError, get_definition
from reality.services import core, scheduled_jobs
from reality.services.costing import build_inventory_generation, inventory_cost_snapshot

cost_owner = fixtures.cost_owner


def reviewed(session, business, owner):
    args, _, _ = fixtures.prepared(session, business, owner)
    return fixtures.commit_review(session, business, owner, args)[1]["review_id"]


def count(session, model, tenant):
    return session.scalar(
        select(func.count()).select_from(model).where(model.tenant_id == tenant)
    )


def test_stored_a_no_replay_and_late_input(session, business, cost_owner, monkeypatch):
    tenant, item = business.tenant.id, business.item.id
    review = reviewed(session, business, cost_owner)
    assert (
        inventory_cost_snapshot(session, tenant, item)["freshness"]["state"]
        == "uninitialized"
    )
    before = count(session, CostInventoryReview, tenant)
    built = build_inventory_generation(session, tenant, review)
    assert built["created"] is True
    assert count(session, CostInventoryReview, tenant) == before
    assert count(session, CostInventorySnapshot, tenant) == 1
    current = inventory_cost_snapshot(session, tenant, item)
    assert current["generation_id"] == built["generation_id"]
    assert current["result"] == {
        "remaining_quantity": "40.0000",
        "acquisition_value": "420.0000",
        "carrying_value": None,
        "carrying_value_state": "assessment_missing",
    }
    assert current["freshness"]["state"] == "ready"
    historical = inventory_cost_snapshot(
        session, tenant, item, generation_id=built["generation_id"]
    )

    def forbidden(*args, **kwargs):
        pytest.fail("Cache read or retry replayed inventory")

    monkeypatch.setattr(
        "reality.services.inventory_generations.inventory_cost", forbidden
    )
    assert build_inventory_generation(session, tenant, review)["created"] is False
    core.record_movement(
        session, tenant, "receipt", item, "1", to_location_id=business.location.id
    )
    pending = inventory_cost_snapshot(session, tenant, item)
    assert pending["freshness"]["state"] == "pending" and pending["result"] is None
    assert pending["basis_result"]["acquisition_value"] == "420.0000"
    assert (
        inventory_cost_snapshot(session, tenant, item, allow_previous=True)["result"]
        == current["result"]
    )
    assert (
        inventory_cost_snapshot(
            session, tenant, item, generation_id=built["generation_id"]
        )
        == historical
    )
    assert (
        inventory_cost_snapshot(session, tenant, item, review_id=review)["freshness"][
            "state"
        ]
        == "historical"
    )


def test_generation_binds_assessment_and_serves_carrying_without_replay(
    session, business, cost_owner, monkeypatch
):
    args, inventory = carrying.prepared_assessment(session, business, cost_owner)
    assessment = carrying.commit_assessment(session, business, cost_owner, args)
    built = build_inventory_generation(
        session, business.tenant.id, inventory["review_id"]
    )
    result = inventory_cost_snapshot(
        session,
        business.tenant.id,
        business.item.id,
        generation_id=built["generation_id"],
    )
    assert (
        result["context"]["assessment_revision_id"]
        == assessment["assessment_revision_id"]
    )
    assert result["result"]["acquisition_value"] == "420.0000"
    assert result["result"]["carrying_value"] == "300.0000"
    assert result["result"]["carrying_value_state"] == "reviewed_assessment"

    monkeypatch.setattr(
        "reality.services.inventory_generations.inventory_cost",
        lambda *args, **kwargs: pytest.fail("Generation read replayed inventory"),
    )
    replay = inventory_cost_snapshot(
        session,
        business.tenant.id,
        business.item.id,
        generation_id=built["generation_id"],
    )
    assert replay == result


def test_foreign_build_read_and_relation_refuse(session, business, cost_owner):
    from reality.services.analytics.costing_relation import inventory_relation

    review = reviewed(session, business, cost_owner)
    built = build_inventory_generation(session, business.tenant.id, review)
    other = core.create_tenant(session, "Other")
    # A real disposable cache identity must not masquerade as confirmed evidence.
    from reality.services.costing import cost_record

    with pytest.raises(core.NotFound):
        cost_record(
            session,
            business.tenant.id,
            "cost_inventory_generation",
            built["generation_id"],
        )
    for call in (
        lambda: build_inventory_generation(session, other.id, review),
        lambda: inventory_cost_snapshot(
            session, other.id, business.item.id, generation_id=built["generation_id"]
        ),
        lambda: inventory_cost_snapshot(
            session, business.tenant.id, business.item.id, generation_id="missing"
        ),
    ):
        with pytest.raises(core.NotFound):
            call()
    assert (
        session.execute(inventory_relation(other.id, built["generation_id"])).all()
        == []
    )
    second = core.create_item(session, business.tenant.id, "SECOND", "Second item")
    with pytest.raises(core.NotFound):
        inventory_cost_snapshot(
            session, business.tenant.id, second.id, generation_id=built["generation_id"]
        )


def test_read_is_bounded_no_autoflush_or_writes(session, business, cost_owner):
    tenant = business.tenant.id
    review = reviewed(session, business, cost_owner)
    built = build_inventory_generation(session, tenant, review)
    pending = Item(
        id=core.uid("itm"), tenant_id=tenant, sku="PENDING", name="Pending", unit="pcs"
    )
    session.add(pending)
    statements = []

    def watch(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    event.listen(session.bind, "before_cursor_execute", watch)
    try:
        inventory_cost_snapshot(
            session, tenant, business.item.id, generation_id=built["generation_id"]
        )
    finally:
        event.remove(session.bind, "before_cursor_execute", watch)
    assert pending in session.new
    assert len(statements) <= 8
    assert not any(
        s.lstrip().startswith(("insert", "update", "delete")) for s in statements
    )
    assert not any(
        "cost_inventory_member" in s or "max(business_event.sequence)" in s
        for s in statements
    )


def test_failed_publication_rolls_back_its_cache_only(
    session, business, cost_owner, monkeypatch
):
    from reality.domain.cost_generation import PublicationRefusal

    tenant = business.tenant.id
    review = reviewed(session, business, cost_owner)

    def fail(**kwargs):
        raise PublicationRefusal("injected_publication_failure")

    monkeypatch.setattr(
        "reality.services.inventory_generations.publication_decision", fail
    )
    with pytest.raises(PublicationRefusal, match="injected"):
        build_inventory_generation(session, tenant, review)
    for model in (
        CostInventoryGeneration,
        CostInventorySnapshot,
        CostInventoryPublication,
    ):
        assert count(session, model, tenant) == 0
    assert count(session, CostInventoryReview, tenant) == 1


def test_corrupt_retained_input_cannot_publish(session, business, cost_owner):
    tenant = business.tenant.id
    review = reviewed(session, business, cost_owner)
    row = session.scalar(
        select(CostInventoryReview).where(
            CostInventoryReview.tenant_id == tenant, CostInventoryReview.id == review
        )
    )
    row.content_hash = "0" * 64
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        build_inventory_generation(session, tenant, review)
    assert count(session, CostInventoryGeneration, tenant) == 0


def test_corrupt_cached_amount_is_never_served_or_republished(
    session, business, cost_owner
):
    from decimal import Decimal

    tenant = business.tenant.id
    review = reviewed(session, business, cost_owner)
    built = build_inventory_generation(session, tenant, review)
    row = session.scalar(
        select(CostInventorySnapshot).where(CostInventorySnapshot.tenant_id == tenant)
    )
    row.acquisition_value = Decimal(999)
    session.flush()
    for call in (
        lambda: build_inventory_generation(session, tenant, review),
        lambda: inventory_cost_snapshot(
            session, tenant, business.item.id, generation_id=built["generation_id"]
        ),
    ):
        with pytest.raises(core.InvalidOperation, match="integrity"):
            call()


def test_registry_real_claim_and_idempotent_retry(session, business, cost_owner):
    tenant = business.tenant.id
    review = reviewed(session, business, cost_owner)
    definition = get_definition("costing.inventory.refresh")
    with pytest.raises(JobError, match="invalid_configuration"):
        definition.validate({"review_id": review, "amount": "420"})
    first = scheduled_jobs.create_manual_run(
        session,
        tenant,
        cost_owner.id,
        definition.name,
        {"review_id": review},
        request_id="cost-build",
    )
    assert (
        scheduled_jobs.create_manual_run(
            session,
            tenant,
            cost_owner.id,
            definition.name,
            {"review_id": review},
            request_id="cost-build",
        ).id
        == first.id
    )
    run = scheduled_jobs.claim_next(session, tenant)
    assert run.id == first.id
    token = run.claim_token
    with pytest.raises(JobError, match="stale_claim"):
        scheduled_jobs.execute_claim(session, tenant, run.id, "wrong")
    assert count(session, CostInventoryGeneration, tenant) == 0
    assert scheduled_jobs.execute_claim(session, tenant, run.id, token) == "succeeded"
    assert scheduled_jobs.execute_claim(session, tenant, run.id, token) == "succeeded"
    assert run.result["counts"] == {"generations": 1, "inventory_rows": 1}
    assert count(session, CostInventoryGeneration, tenant) == 1


def test_worker_rechecks_owner_and_foreign_review(session, business, cost_owner):
    tenant = business.tenant.id
    review = reviewed(session, business, cost_owner)
    with pytest.raises(JobError, match="cost_basis_unavailable"):
        scheduled_jobs.create_manual_run(
            session,
            tenant,
            cost_owner.id,
            "costing.inventory.refresh",
            {"review_id": "foreign-or-missing"},
            request_id="bad-review",
        )
    scheduled_jobs.create_manual_run(
        session,
        tenant,
        cost_owner.id,
        "costing.inventory.refresh",
        {"review_id": review},
        request_id="revoke",
    )
    run = scheduled_jobs.claim_next(session, tenant)
    member = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant,
            TenantMembership.user_id == cost_owner.id,
        )
    )
    member.role = "member"
    session.flush()
    with pytest.raises(JobError, match="not_authorized"):
        scheduled_jobs.execute_claim(session, tenant, run.id, run.claim_token)
    assert count(session, CostInventoryGeneration, tenant) == 0


def test_deadline_rolls_back_before_publication(session, business, cost_owner):
    tenant = business.tenant.id
    review = reviewed(session, business, cost_owner)
    with pytest.raises(JobError, match="handler_timeout"):
        build_inventory_generation(
            session, tenant, review, deadline=core.now() - timedelta(seconds=1)
        )
    assert count(session, CostInventoryGeneration, tenant) == 0


def prepare_committed(factory, tenant, actor):
    with factory() as session:
        business = SimpleNamespace(
            tenant=session.get(Tenant, tenant),
            company=core.create_party(session, tenant, "Company", "company"),
            supplier=core.create_party(session, tenant, "Supplier", "supplier"),
            item=core.create_item(session, tenant, "CACHE", "Cache item"),
            location=core.create_location(session, tenant, "Warehouse"),
        )
        owner = session.get(AppUser, actor)
        review = reviewed(session, business, owner)
        session.commit()
        return review, business.item.id


def test_concurrent_builds_publish_one_generation(scheduled_database):
    _, factory, tenant, actor = scheduled_database
    review, item = prepare_committed(factory, tenant, actor)
    barrier = Barrier(2)

    def build(_):
        with factory.begin() as session:
            barrier.wait(timeout=10)
            return build_inventory_generation(session, tenant, review)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(build, range(2)))
    assert len({r["generation_id"] for r in results}) == 1
    assert sum(r["created"] for r in results) == 1
    with factory() as session:
        assert count(session, CostInventoryGeneration, tenant) == 1
        assert count(session, CostInventoryPublication, tenant) == 1
        assert (
            inventory_cost_snapshot(session, tenant, item)["result"][
                "acquisition_value"
            ]
            == "420.0000"
        )


def test_real_worker_child_publishes_and_only_reports_reference(scheduled_database):
    from reality.jobs.runtime import ProcessLoop

    engine, factory, tenant, actor = scheduled_database
    review, item = prepare_committed(factory, tenant, actor)
    with factory.begin() as session:
        scheduled_jobs.create_manual_run(
            session,
            tenant,
            actor,
            "costing.inventory.refresh",
            {"review_id": review},
            request_id="real-child",
        )
    result = ProcessLoop("worker", tenant_id=tenant).sweep(
        engine, max_runs=1, max_seconds=25
    )
    assert result["succeeded"] == 1
    with factory() as session:
        assert (
            inventory_cost_snapshot(session, tenant, item)["result"][
                "acquisition_value"
            ]
            == "420.0000"
        )


def test_late_commit_during_build_and_atomic_visibility(
    scheduled_database, monkeypatch
):
    from threading import Event

    from reality.services import inventory_generations

    _, factory, tenant, actor = scheduled_database
    review, item = prepare_committed(factory, tenant, actor)
    reached, release = Event(), Event()
    original = inventory_generations.inventory_cost

    def paused(*args, **kwargs):
        result = original(*args, **kwargs)
        reached.set()
        assert release.wait(timeout=10)
        return result

    monkeypatch.setattr(inventory_generations, "inventory_cost", paused)

    def build():
        with factory.begin() as session:
            return build_inventory_generation(session, tenant, review)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(build)
        try:
            assert reached.wait(timeout=10)
            with factory() as session:
                assert (
                    inventory_cost_snapshot(session, tenant, item)["freshness"]["state"]
                    == "uninitialized"
                )
                location = core.create_location(session, tenant, "Late arrival")
                core.record_movement(
                    session, tenant, "receipt", item, "1", to_location_id=location.id
                )
                session.commit()
        finally:
            release.set()
        result = future.result(timeout=10)
    assert result["freshness"] == "pending"
    with factory() as session:
        current = inventory_cost_snapshot(session, tenant, item)
        assert current["result"] is None
        assert current["basis_result"]["remaining_quantity"] == "40.0000"
        assert current["freshness"]["state"] == "pending"


def test_cache_deletion_reconstructs_from_retained_inputs(
    session, business, cost_owner
):
    from sqlalchemy import delete

    tenant = business.tenant.id
    review = reviewed(session, business, cost_owner)
    first = build_inventory_generation(session, tenant, review)
    before = inventory_cost_snapshot(
        session, tenant, business.item.id, review_id=review
    )
    for model in (
        CostInventoryPublication,
        CostInventorySnapshot,
        CostInventoryGeneration,
    ):
        session.execute(delete(model).where(model.tenant_id == tenant))
    assert count(session, CostInventoryReview, tenant) == 1
    second = build_inventory_generation(session, tenant, review)
    assert second["generation_id"] != first["generation_id"]
    after = inventory_cost_snapshot(session, tenant, business.item.id, review_id=review)
    assert before["result"] == after["result"]
    assert before["context"]["event_sequence"] == after["context"]["event_sequence"]


def test_current_snapshot_refuses_repeatable_read_but_exact_history_works(
    session, business, cost_owner, monkeypatch
):
    tenant = business.tenant.id
    review = reviewed(session, business, cost_owner)
    build_inventory_generation(session, tenant, review)
    monkeypatch.setattr(
        session.connection(), "get_isolation_level", lambda: "REPEATABLE READ"
    )
    with pytest.raises(core.InvalidOperation, match="READ COMMITTED"):
        inventory_cost_snapshot(session, tenant, business.item.id)
    with pytest.raises(core.InvalidOperation, match="READ COMMITTED"):
        build_inventory_generation(session, tenant, review)
    assert (
        inventory_cost_snapshot(session, tenant, business.item.id, review_id=review)[
            "result"
        ]["acquisition_value"]
        == "420.0000"
    )


def test_zero_inventory_is_a_valid_published_result(session, business, cost_owner):
    from reality.services.costing import receipt_cost

    tenant = business.tenant.id
    args, receipt, issue = fixtures.prepared(session, business, cost_owner)
    last = core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "40",
        from_location_id=business.location.id,
    )
    args.update(
        economic_issue_ids=[issue.id, last.id],
        effective_at=core.now().isoformat(),
        expected_event_sequence=receipt_cost(session, tenant, receipt.id)[
            "event_sequence"
        ],
    )
    review = fixtures.commit_review(session, business, cost_owner, args)[1]["review_id"]
    build_inventory_generation(session, tenant, review)
    result = inventory_cost_snapshot(session, tenant, business.item.id)
    assert result["freshness"]["state"] == "ready"
    assert result["result"]["remaining_quantity"] == "0.0000"
    assert result["result"]["acquisition_value"] == "0.0000"
    assert result["result"]["carrying_value"] is None


def test_new_review_does_not_fall_back_to_previous_cached_review(
    session, business, cost_owner
):
    from reality.services.costing import receipt_cost

    tenant = business.tenant.id
    args, receipt, _ = fixtures.prepared(session, business, cost_owner)
    old = fixtures.commit_review(session, business, cost_owner, args)[1]["review_id"]
    build_inventory_generation(session, tenant, old)
    args["expected_event_sequence"] = receipt_cost(session, tenant, receipt.id)[
        "event_sequence"
    ]
    args["reason"] = "Renewed review of the same retained scope"
    latest = fixtures.commit_review(session, business, cost_owner, args)[1]["review_id"]
    assert latest != old
    current = inventory_cost_snapshot(session, tenant, business.item.id)
    assert (
        current["freshness"]["state"] == "uninitialized" and current["result"] is None
    )
    assert (
        inventory_cost_snapshot(session, tenant, business.item.id, review_id=old)[
            "result"
        ]["acquisition_value"]
        == "420.0000"
    )
    build_inventory_generation(session, tenant, latest)
    assert (
        inventory_cost_snapshot(session, tenant, business.item.id)["context"][
            "review_id"
        ]
        == latest
    )
