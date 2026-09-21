"""Exact owner-authorized financial company manifest admission."""

import pytest
import test_cost_census_resolution as resolution
import test_cost_census_storage as census_storage
import test_costing_services as costs
from alembic import command
from alembic.config import Config
from conftest import record_by_id
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from test_cost_census import seed

from reality.db.company_generations import (
    CostCompanyContributionInput,
    CostCompanyInventoryInput,
    CostCompanyManifest,
)
from reality.db.core import Tenant
from reality.services import core, costing
from reality.services.memberships import Principal


@pytest.fixture
def company_database(postgres_database, monkeypatch):
    fixture = census_storage.scheduled_database.__wrapped__(
        postgres_database, monkeypatch
    )
    database = next(fixture)
    try:
        command.upgrade(Config("alembic.ini"), "0084_inventory_ownership_parts")
        yield database
    finally:
        fixture.close()


def _reviewed(database):
    factory, business, owner, cutoff, _ = resolution.setup_review(
        database, contribution=True
    )
    census = resolution.capture(factory, business.tenant.id, cutoff)
    return factory, business.tenant.id, owner.id, census


def test_committed_cursor_exact_population_fingerprints_and_retry(company_database):
    factory, tenant, owner, census = _reviewed(company_database)
    with factory() as session:
        first = costing.admit_company_cost_manifest(
            session, tenant, census, principal=Principal(owner)
        )
        session.commit()
    with factory() as session:
        second = costing.admit_company_cost_manifest(
            session, tenant, census, principal=Principal(owner)
        )
        manifest = record_by_id(session, CostCompanyManifest, first["id"])
        inventory = list(
            session.scalars(
                select(CostCompanyInventoryInput).where(
                    CostCompanyInventoryInput.manifest_id == first["id"]
                )
            )
        )
        contribution = list(
            session.scalars(
                select(CostCompanyContributionInput).where(
                    CostCompanyContributionInput.manifest_id == first["id"]
                )
            )
        )
    assert second == first
    assert manifest.knowledge_at >= manifest.effective_at
    assert manifest.target_event_sequence == first["target_event_sequence"]
    assert len(inventory) == first["counts"]["inventory"] == 1
    assert len(contribution) == first["counts"]["contribution"] == 1
    assert inventory[0].support_state == contribution[0].db1_state == "known"
    assert all(len(row.input_fingerprint) == 64 for row in inventory + contribution)


def test_unknowns_and_exact_unresolved_gap_binding(company_database):
    data = seed(company_database)
    factory, tenant, *_ = data
    with factory() as session:
        owner = costs.cost_owner.__wrapped__(
            session,
            type("Business", (), {"tenant": session.get(Tenant, tenant)})(),
        )
        session.commit()
        owner_id = owner.id
    census = census_storage.retain(data)["id"]
    with factory() as session:
        value = costing.admit_company_cost_manifest(
            session, tenant, census, principal=Principal(owner_id)
        )
        inventory = session.scalar(
            select(CostCompanyInventoryInput).where(
                CostCompanyInventoryInput.manifest_id == value["id"]
            )
        )
        contribution = session.scalar(
            select(CostCompanyContributionInput).where(
                CostCompanyContributionInput.manifest_id == value["id"]
            )
        )
    assert inventory.support_state == "unknown" and inventory.review_id is None
    assert contribution.db1_state == contribution.db2_state == "unknown"
    assert contribution.review_id is None
    assert value["counts"]["header_gaps"] == 1
    assert value["counts"]["source_gaps"] == 1
    assert len(value["gap_digest"]) == 64


def test_foreign_stale_and_non_owner_admission_refuse(company_database):
    factory, tenant, owner, census = _reviewed(company_database)
    with factory() as session:
        other = core.create_tenant(session, "Other")
        outsider = costs.cost_owner.__wrapped__(
            session, type("Business", (), {"tenant": other})()
        )
        session.commit()
    with factory() as session:
        with pytest.raises(core.NotFound):
            costing.admit_company_cost_manifest(
                session, other.id, census, principal=Principal(outsider.id)
            )
        with pytest.raises(core.NotFound):
            costing.admit_company_cost_manifest(
                session, tenant, census, principal=Principal(outsider.id)
            )
        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()
    with factory() as session, pytest.raises(core.InvalidOperation, match="stale"):
        costing.admit_company_cost_manifest(
            session, tenant, census, principal=Principal(owner)
        )


def test_caught_failure_and_rollback_leave_no_partial_manifest(
    company_database, monkeypatch
):
    factory, tenant, owner, census = _reviewed(company_database)
    from reality.services import company_generations

    monkeypatch.setattr(company_generations, "digest", lambda value: "broken")
    with factory() as session:
        with pytest.raises(DBAPIError):
            costing.admit_company_cost_manifest(
                session, tenant, census, principal=Principal(owner)
            )
        session.commit()
    with factory() as session:
        assert (
            session.scalar(
                select(CostCompanyManifest).where(
                    CostCompanyManifest.tenant_id == tenant
                )
            )
            is None
        )
