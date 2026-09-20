"""Fixed captured generations are queryable without becoming company valuations."""

from uuid import uuid4

import pytest

from reality.domain.traversal import Traversal
from reality.services import core
from reality.services.analytics.reports import change_graph_report, get_report
from reality.services.analytics.traversal import TraversalRefused, plan, run_traversal
from reality.services.memberships import Principal
from reality.tools.graph import invoke


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


def question(generation_id, *, family="contribution", **changes):
    if family == "inventory":
        body = {
            "from": "inventory_valuation",
            "measures": ["inventory_acquisition_value"],
            "group_by": [
                {"field": "root.currency"},
                {"field": "root.base_unit"},
                {"field": "root.method"},
                {"field": "root.owner_party_id"},
            ],
        }
    else:
        body = {
            "from": "contribution_valuation",
            "measures": [
                "contribution_db1",
                "contribution_db1_known",
                "contribution_db1_required",
                "contribution_db1_covered",
                "contribution_db2",
                "contribution_db2_known",
                "contribution_db2_required",
                "contribution_db2_covered",
            ],
            "group_by": [
                {"field": "root.currency"},
                {"field": "root.base_unit"},
            ],
        }
    return body | {
        "captured_cost_context": {"generation_id": generation_id},
        **changes,
    }


def test_context_is_fixed_exclusive_and_standalone():
    assert (
        Traversal.model_validate(question("g")).captured_cost_context.generation_id
        == "g"
    )
    for changes in (
        {"contribution_cost_context": {"action_id": "a"}},
        {"inventory_cost_context": {"action_id": "a"}},
        {"from": "order", "measures": ["stated_order_amount"], "group_by": []},
        {"follow": [{"edge": "document_line_document", "as": "document"}]},
    ):
        with pytest.raises(TraversalRefused) as failure:
            plan(Traversal.model_validate(question("g", **changes)))
        assert failure.value.code == "cost_context_invalid"


def test_graph_tool_saved_report_and_http_use_one_captured_generation(
    report_database, monkeypatch
):
    import test_cost_captured_basis_storage as storage
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import select
    from test_cost_census import read_session

    from reality.db.core import TenantMembership
    from reality.services import captured_report, costing
    from reality.web import analytics_api, auth

    factory, tenant, _, basis = storage.retained(report_database)
    with read_session(factory) as session:
        generation = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )["generation_id"]
        session.commit()

    def forbidden(*args, **kwargs):
        raise AssertionError("Captured graph reads must not replay financial history")

    monkeypatch.setattr(captured_report.cost_captured_basis, "_replay", forbidden)
    with factory() as session:
        contribution = invoke(
            session, tenant, "graph.ask", {"question": question(generation)}
        )
        assert contribution["rows"] == [
            {
                "root.currency": "EUR",
                "root.base_unit": "pcs",
                "contribution_db1": None,
                "contribution_db1_known": "570.0000",
                "contribution_db1_required": 1,
                "contribution_db1_covered": 1,
                "contribution_db2": None,
                "contribution_db2_known": "0",
                "contribution_db2_required": 1,
                "contribution_db2_covered": 0,
            }
        ]
        assert contribution["cost_basis"]["generation_id"] == generation
        assert contribution["cost_basis"]["financial_publication_eligible"] is False
        inventory = invoke(
            session,
            tenant,
            "graph.ask",
            {"question": question(generation, family="inventory")},
        )
        assert inventory["rows"][0]["inventory_acquisition_value"] == "420.0000"

        principal = Principal(
            session.scalar(
                select(TenantMembership.user_id).where(
                    TenantMembership.tenant_id == tenant,
                    TenantMembership.status == "active",
                )
            )
        )
        saved = change_graph_report(
            session,
            tenant,
            principal,
            {
                "operation": "create",
                "request_id": str(uuid4()),
                "name": "Captured contribution",
                "question": question(generation),
            },
        )
        reopened = get_report(
            session, tenant, principal, saved["id"], report_kind="graph"
        )
        assert reopened["definition"]["captured_cost_context"] == {
            "generation_id": generation
        }
        assert (
            run_traversal(
                session, tenant, Traversal.model_validate(reopened["definition"])
            ).cost_basis["generation_id"]
            == generation
        )

        app = FastAPI()
        app.include_router(analytics_api.router, prefix="/tenants/{tenant_id}")
        app.dependency_overrides[auth.database_session] = lambda: session
        with TestClient(app) as client:
            response = client.post(
                f"/tenants/{tenant}/analytics/graph/ask",
                json={"question": reopened["definition"]},
            )
        assert response.status_code == 200, response.text
        assert response.json()["cost_basis"]["generation_id"] == generation


def test_unknown_and_foreign_captured_generation_remain_explicit(report_database):
    import test_cost_captured_basis_storage as storage
    from test_cost_census import read_session

    from reality.services import costing

    factory, tenant, _, basis = storage.retained(report_database, reviewed=False)
    with read_session(factory) as session:
        generation = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )["generation_id"]
        session.commit()
    with factory() as session:
        result = run_traversal(
            session, tenant, Traversal.model_validate(question(generation))
        )
        assert result.rows == (
            {
                "root.currency": None,
                "root.base_unit": None,
                "contribution_db1": None,
                "contribution_db1_known": "0",
                "contribution_db1_required": 1,
                "contribution_db1_covered": 0,
                "contribution_db2": None,
                "contribution_db2_known": "0",
                "contribution_db2_required": 1,
                "contribution_db2_covered": 0,
            },
        )
        assert result.cost_basis["coverage"] == {
            "inventory_required": 1,
            "contribution_required": 1,
        }
        foreign = core.create_tenant(session, "Foreign captured graph").id
        session.commit()
    with factory() as session, pytest.raises(core.NotFound):
        run_traversal(session, foreign, Traversal.model_validate(question(generation)))
