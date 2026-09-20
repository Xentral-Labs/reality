"""Captured report discovery exposes fixed metadata, never financial approval."""

import pytest

from reality.services import core
from reality.tools.application import run_read_tool


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


def test_tool_lists_sealed_metadata_without_replay(report_database, monkeypatch):
    import test_cost_captured_basis_storage as storage
    from test_cost_census import read_session

    from reality.services import captured_report, costing

    factory, tenant, _, basis = storage.retained(report_database)
    with read_session(factory) as session:
        generation = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )["generation_id"]
        session.commit()

    def forbidden(*args, **kwargs):
        raise AssertionError("Discovery must not replay captured inputs")

    monkeypatch.setattr(captured_report.cost_captured_basis, "_replay", forbidden)
    with factory() as session:
        result = run_read_tool(
            session,
            tenant,
            "graph.captured_reports.list",
            {"family": "contribution", "limit": 1},
        )
    assert result["next_cursor"] is None
    assert result["items"] == [
        {
            "generation_id": generation,
            "basis_id": basis["basis_id"],
            "kind": "captured_review_selection_v1",
            "algorithm_version": "captured-report-v1",
            "effective_at": basis["context"]["effective_at"],
            "observed_at": basis["context"]["observed_at"],
            "event_sequence": basis["context"]["event_sequence"],
            "completed_at": result["items"][0]["completed_at"],
            "inventory_count": 1,
            "contribution_count": 1,
            "published": False,
            "freshness": "ready",
            "financial_publication_eligible": False,
        }
    ]


def test_family_cursor_tenant_and_http_boundaries(report_database):
    import test_cost_captured_basis_storage as storage
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_cost_census import read_session

    from reality.services import costing
    from reality.services.analytics.captured_options import captured_report_options
    from reality.web import analytics_api, auth

    factory, tenant, _, basis = storage.retained(report_database)
    with read_session(factory) as session:
        generation = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )["generation_id"]
        session.commit()
    with factory() as session:
        foreign = core.create_tenant(session, "Foreign discovery").id
        session.commit()
    with factory() as session:
        assert (
            captured_report_options(session, foreign, family="inventory")["items"] == []
        )
        with pytest.raises(core.NotFound):
            captured_report_options(
                session, foreign, family="inventory", cursor=generation
            )
        for family in ("inventory", "contribution"):
            assert (
                captured_report_options(session, tenant, family=family)["items"][0][
                    "generation_id"
                ]
                == generation
            )
        app = FastAPI()
        app.include_router(analytics_api.router, prefix="/tenants/{tenant_id}")
        app.dependency_overrides[auth.database_session] = lambda: session
        with TestClient(app) as client:
            response = client.get(
                f"/tenants/{tenant}/analytics/graph/captured-reports",
                params={"family": "inventory"},
            )
            hidden = client.get(
                f"/tenants/{foreign}/analytics/graph/captured-reports",
                params={"family": "inventory", "cursor": generation},
            )
        assert response.status_code == 200, response.text
        assert response.json()["items"][0]["generation_id"] == generation
        assert hidden.status_code == 404


@pytest.mark.parametrize("limit", [0, 51, True, "2"])
def test_bounds_refuse_before_sql(session, business, limit):
    from reality.services.analytics.captured_options import captured_report_options

    with pytest.raises(core.InvalidOperation):
        captured_report_options(
            session, business.tenant.id, family="inventory", limit=limit
        )
