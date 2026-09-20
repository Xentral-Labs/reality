"""Deterministic company generation, jobs and scope-keyed publication."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier

import pytest
import test_company_generation_manifest as manifests
from sqlalchemy import func, select, update

from reality.db.company_generations import (
    CostCompanyGeneration,
    CostCompanyInventoryResult,
)
from reality.db.cost_generations import CostInventorySnapshot
from reality.jobs.registry import JobContext, JobError, get_definition
from reality.services import core, costing
from reality.services.memberships import Principal

company_database = manifests.company_database


def _context(tenant, actor, run="run"):
    return JobContext(
        tenant_id=tenant,
        actor_id=actor,
        run_id=run,
        scheduled_for=None,
        deadline=datetime.now(UTC) + timedelta(minutes=1),
    )


def _manifest(database, *, reviewed=True):
    if reviewed:
        factory, tenant, owner, census = manifests._reviewed(database)
    else:
        import test_cost_census_storage as census_storage
        import test_costing_services as costs
        from test_cost_census import seed

        from reality.db.core import Tenant

        data = seed(database)
        factory, tenant, *_ = data
        with factory() as session:
            actor = costs.cost_owner.__wrapped__(
                session, type("Business", (), {"tenant": session.get(Tenant, tenant)})()
            )
            session.commit()
            owner = actor.id
        census = census_storage.retain(data)["id"]
    with factory() as session:
        held = costing.admit_company_cost_manifest(
            session, tenant, census, principal=Principal(owner)
        )
        session.commit()
    return factory, tenant, held


def test_deterministic_chunks_unknown_completion_and_lost_response_retry(
    company_database,
):
    factory, tenant, manifest = _manifest(company_database, reviewed=False)
    with factory() as session:
        first = costing.build_company_cost_generation(
            session, tenant, manifest["id"], start=0, limit=1
        )
        session.commit()
    assert first["state"] == "building" and first["completed_work_count"] == 1
    with factory() as session:
        retry = costing.build_company_cost_generation(
            session, tenant, manifest["id"], start=0, limit=1
        )
        final = costing.build_company_cost_generation(
            session, tenant, manifest["id"], start=1, limit=1
        )
        session.commit()
    assert retry["generation_id"] == first["generation_id"]
    assert retry["completed_work_count"] == 1
    assert final["state"] == "sealed" and final["completed_work_count"] == 2


def test_checksum_corruption_refuses_and_rolls_back(company_database):
    factory, tenant, manifest = _manifest(company_database)
    with factory() as session:
        built = costing.build_company_cost_generation(session, tenant, manifest["id"])
        session.commit()
    with factory() as session:
        row = session.scalar(
            select(CostCompanyInventoryResult).where(
                CostCompanyInventoryResult.generation_id == built["generation_id"]
            )
        )
        session.execute(
            update(CostInventorySnapshot)
            .where(CostInventorySnapshot.generation_id == row.inventory_generation_id)
            .values(acquisition_value=999)
        )
        session.commit()
    with factory() as session, pytest.raises(core.InvalidOperation, match="integrity"):
        costing.build_company_cost_generation(session, tenant, manifest["id"])


def test_publication_cas_retry_conflict_and_pending_preservation(company_database):
    factory, tenant, manifest = _manifest(company_database)
    with factory() as session:
        built = costing.build_company_cost_generation(session, tenant, manifest["id"])
        session.commit()
    with factory() as session:
        published = costing.publish_company_cost_generation(
            session, tenant, built["generation_id"], previous_generation_id=None
        )
        session.commit()
    with factory() as session:
        assert not costing.publish_company_cost_generation(
            session, tenant, built["generation_id"], previous_generation_id=None
        )["changed"]
        session.commit()
    from datetime import datetime

    from test_cost_census import read_session

    from reality.db.core import TenantMembership

    with read_session(factory) as session:
        census = costing.retain_company_cost_census(
            session,
            tenant,
            datetime.fromisoformat(manifest["effective_at"]),
            request_id="competing-census",
        )["id"]
        session.commit()
    with factory() as session:
        owner = session.scalar(
            select(TenantMembership.user_id).where(
                TenantMembership.tenant_id == tenant,
                TenantMembership.role == "owner",
            )
        )
        competing_manifest = costing.admit_company_cost_manifest(
            session, tenant, census, principal=Principal(owner)
        )
        competing = costing.build_company_cost_generation(
            session, tenant, competing_manifest["id"]
        )
        with pytest.raises(core.Conflict):
            costing.publish_company_cost_generation(
                session,
                tenant,
                competing["generation_id"],
                previous_generation_id="lost",
            )
        session.rollback()
    with factory() as session:
        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()
    with factory() as session:
        report = costing.company_cost_generation_report(
            session, tenant, built["generation_id"]
        )
        assert report["freshness"] == "pending"
        assert (
            session.scalar(select(func.count()).select_from(CostCompanyGeneration)) == 1
        )
    assert published["changed"]


def test_owner_jobs_admit_build_publish_and_retry_with_bounded_results(
    company_database,
):
    factory, tenant, owner, census = manifests._reviewed(company_database)
    admit = get_definition("costing.company_manifest.admit")
    build = get_definition("costing.company_generation.build")
    publish = get_definition("costing.company_generation.publish")
    with factory() as session:
        admitted = admit.handler(
            session,
            _context(tenant, owner),
            admit.validate({"census_id": census, "max_subjects": 10}),
        )
        session.commit()
    manifest_id = admitted.references[0].id
    with factory() as session:
        built = build.handler(
            session,
            _context(tenant, owner),
            build.validate({"manifest_id": manifest_id, "start": 0, "limit": 10}),
        )
        session.commit()
    generation_id = built.references[0].id
    config = publish.validate(
        {"generation_id": generation_id, "expected_previous_id": None}
    )
    with factory() as session:
        first = publish.handler(session, _context(tenant, owner), config)
        session.commit()
    with factory() as session:
        retry = publish.handler(session, _context(tenant, owner, "retry"), config)
        session.commit()
    assert admitted.counts == {"manifests": 1, "inputs": 2}
    assert built.counts == {"completed_work": 2, "expected_work": 2}
    assert first.counts == {"publication_changed": 1}
    assert retry.counts == {"publication_changed": 0}
    assert all(
        len(result.model_dump_json()) < 3500 for result in (admitted, built, first)
    )


def test_company_jobs_revalidate_owner_scope_and_strict_configuration(company_database):
    factory, _, owner, census = manifests._reviewed(company_database)
    admit = get_definition("costing.company_manifest.admit")
    config = admit.validate({"census_id": census})
    with factory() as session:
        foreign = core.create_tenant(session, "Foreign job tenant").id
        session.commit()
    with factory() as session, pytest.raises(JobError, match="not_authorized"):
        admit.authorize(session, _context(foreign, owner), config)
    with pytest.raises(JobError, match="invalid_configuration"):
        admit.validate({"census_id": census, "publish": True})


def test_competing_company_publications_have_one_cas_winner(company_database):
    from test_cost_census import read_session

    factory, tenant, owner, census = manifests._reviewed(company_database)
    with factory() as session:
        first_manifest = costing.admit_company_cost_manifest(
            session, tenant, census, principal=Principal(owner)
        )
        first = costing.build_company_cost_generation(
            session, tenant, first_manifest["id"]
        )["generation_id"]
        session.commit()
    with read_session(factory) as session:
        second_census = costing.retain_company_cost_census(
            session,
            tenant,
            datetime.fromisoformat(first_manifest["effective_at"]),
            request_id="concurrent-census",
        )["id"]
        session.commit()
    with factory() as session:
        second_manifest = costing.admit_company_cost_manifest(
            session, tenant, second_census, principal=Principal(owner)
        )
        second = costing.build_company_cost_generation(
            session, tenant, second_manifest["id"]
        )["generation_id"]
        session.commit()

    barrier = Barrier(2)

    def publish(identity):
        with factory() as session:
            barrier.wait()
            try:
                result = costing.publish_company_cost_generation(
                    session, tenant, identity, previous_generation_id=None
                )
                session.commit()
                return result["changed"]
            except core.Conflict:
                session.rollback()
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(publish, (first, second)))
    assert sorted(outcomes, key=str) == [True, "conflict"]
