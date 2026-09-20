"""Shared worker builds one bounded captured report without publishing it."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from reality.jobs.registry import JobContext, JobError, get_definition
from reality.services import core


@pytest.fixture
def report_database(postgres_database, monkeypatch):
    import test_cost_captured_basis_storage as storage
    from alembic import command
    from alembic.config import Config

    fixture = storage.scheduled_database.__wrapped__(postgres_database, monkeypatch)
    database = next(fixture)
    try:
        command.upgrade(Config("alembic.ini"), "0079_captured_report")
        yield database
    finally:
        fixture.close()


def context(tenant, actor, run="run"):
    return JobContext(
        tenant_id=tenant,
        actor_id=actor,
        run_id=run,
        scheduled_for=None,
        deadline=datetime.now(UTC) + timedelta(minutes=1),
    )


def test_owner_job_builds_and_retry_reuses_generation(report_database):
    import test_cost_captured_basis_storage as storage
    from test_cost_census import read_session

    from reality.db.captured_report import CostPublication
    from reality.db.core import TenantMembership
    from reality.services import costing

    factory, tenant, _, basis = storage.retained(report_database)
    with factory() as session:
        actor = session.scalar(
            select(TenantMembership.user_id).where(
                TenantMembership.tenant_id == tenant,
                TenantMembership.role == "owner",
            )
        )
    definition = get_definition("costing.captured_report.refresh")
    config = definition.validate({"basis_id": basis["basis_id"]})
    with read_session(factory) as session:
        first = definition.handler(session, context(tenant, actor), config)
        session.commit()
    with read_session(factory) as session:
        second = definition.handler(session, context(tenant, actor, "retry"), config)
        session.commit()
    assert first == second
    assert first.counts == {"generations": 1}
    assert first.references[0].record_type == "cost_generation"
    with factory() as session:
        assert session.scalar(select(CostPublication.id)) is None
        assert (
            costing.captured_cost_report(session, tenant, first.references[0].id)[
                "financial_publication_eligible"
            ]
            is False
        )


def test_job_refuses_foreign_actor_basis_and_extra_configuration(report_database):
    import test_cost_captured_basis_storage as storage

    from reality.db.core import TenantMembership

    factory, tenant, _, basis = storage.retained(report_database)
    definition = get_definition("costing.captured_report.refresh")
    config = definition.validate({"basis_id": basis["basis_id"]})
    with factory() as session:
        actor = session.scalar(
            select(TenantMembership.user_id).where(TenantMembership.tenant_id == tenant)
        )
        foreign = core.create_tenant(session, "Foreign worker").id
        session.commit()
    with factory() as session, pytest.raises(JobError):
        definition.authorize(session, context(foreign, actor), config)
    with pytest.raises(JobError):
        definition.validate({"basis_id": basis["basis_id"], "publish": True})


def test_publication_job_changes_pointer_once_and_retry_is_safe(report_database):
    import test_cost_captured_basis_storage as storage
    from test_cost_census import read_session

    from reality.db.captured_report import CostPublication
    from reality.db.core import TenantMembership
    from reality.services import costing

    factory, tenant, _, basis = storage.retained(report_database)
    with read_session(factory) as session:
        generation = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )["generation_id"]
        session.commit()
    with factory() as session:
        actor = session.scalar(
            select(TenantMembership.user_id).where(
                TenantMembership.tenant_id == tenant,
                TenantMembership.role == "owner",
            )
        )
    definition = get_definition("costing.captured_report.publish")
    config = definition.validate(
        {"generation_id": generation, "expected_previous_id": None}
    )
    conflict = definition.validate(
        {"generation_id": generation, "expected_previous_id": "wrong"}
    )
    with (
        factory() as session,
        pytest.raises(JobError, match="cost_publication_conflict"),
    ):
        definition.handler(session, context(tenant, actor, "stale"), conflict)
    with factory() as session:
        first = definition.handler(session, context(tenant, actor), config)
        session.commit()
    with factory() as session:
        second = definition.handler(session, context(tenant, actor, "retry"), config)
        session.commit()
        assert session.scalar(select(CostPublication.generation_id)) == generation
    assert first.counts == {"publication_changed": 1}
    assert second.counts == {"publication_changed": 0}
    assert first.references == second.references


def test_publication_job_refuses_foreign_generation_and_extra_input(report_database):
    import test_cost_captured_basis_storage as storage
    from test_cost_census import read_session

    from reality.db.core import TenantMembership
    from reality.services import costing

    factory, tenant, _, basis = storage.retained(report_database)
    with read_session(factory) as session:
        generation = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )["generation_id"]
        session.commit()
    with factory() as session:
        actor = session.scalar(
            select(TenantMembership.user_id).where(TenantMembership.tenant_id == tenant)
        )
        foreign = core.create_tenant(session, "Foreign publisher").id
        session.commit()
    definition = get_definition("costing.captured_report.publish")
    config = definition.validate({"generation_id": generation})
    with factory() as session, pytest.raises(JobError):
        definition.authorize(session, context(foreign, actor), config)
    with pytest.raises(JobError):
        definition.validate({"generation_id": generation, "amount": "1"})
