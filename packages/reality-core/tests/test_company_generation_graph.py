"""Verified company generations use the existing reporting graph without implicit latest."""

from uuid import uuid4

import pytest
import test_company_generation_jobs as jobs
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from reality.db.core import TenantMembership
from reality.domain.traversal import Traversal
from reality.services import costing
from reality.services.analytics.reports import change_graph_report, get_report
from reality.services.analytics.traversal import TraversalRefused, plan, run_traversal
from reality.services.memberships import Principal
from reality.tools.graph import invoke
from reality.web import analytics_api, auth

company_database = jobs.company_database


def question(generation_id: str, *, family: str = "contribution", **changes):
    body = {
        "from": f"{family}_valuation",
        "measures": [
            "inventory_acquisition_value"
            if family == "inventory"
            else "contribution_db1"
        ]
        + (
            []
            if family == "inventory"
            else [
                "contribution_db1_known",
                "contribution_db1_required",
                "contribution_db1_covered",
                "contribution_db1_rate",
                "contribution_db2",
                "contribution_db2_known",
                "contribution_db2_required",
                "contribution_db2_covered",
                "contribution_db2_rate",
            ]
        ),
        "group_by": (
            [
                {"field": "root.currency"},
                {"field": "root.base_unit"},
                {"field": "root.method"},
                {"field": "root.owner_party_id"},
            ]
            if family == "inventory"
            else [
                {"field": "root.currency"},
                {"field": "root.base_unit"},
            ]
        ),
    }
    return body | {
        "company_cost_context": {"generation_id": generation_id},
        **changes,
    }


def test_company_context_is_fixed_exclusive_and_standalone():
    parsed = Traversal.model_validate(question("generation"))
    assert parsed.company_cost_context.generation_id == "generation"
    for changes in (
        {"captured_cost_context": {"generation_id": "captured"}},
        {"contribution_cost_context": {"action_id": "action"}},
        {"inventory_cost_context": {"action_id": "action"}},
        {"from": "order", "measures": ["stated_order_amount"]},
        {"follow": [{"edge": "document_line_document", "as": "document"}]},
    ):
        with pytest.raises(TraversalRefused) as failure:
            plan(Traversal.model_validate(question("generation", **changes)))
        assert failure.value.code == "cost_context_invalid"


def test_company_inventory_refuses_time_bucketing():
    with pytest.raises(TraversalRefused) as failure:
        plan(
            Traversal.model_validate(
                question(
                    "generation",
                    family="inventory",
                    group_by=[
                        {"field": "root.currency"},
                        {"field": "root.base_unit"},
                        {"field": "root.effective_at", "bucket": "month"},
                    ],
                )
            )
        )
    assert failure.value.code == "not_additive"


@pytest.mark.parametrize(
    "family,changes,code",
    [
        ("inventory", {"group_by": []}, "unit_mismatch"),
        ("contribution", {"group_by": []}, "unit_mismatch"),
        (
            "contribution",
            {
                "group_by": [
                    {"field": "root.currency"},
                    {"field": "root.base_unit"},
                    {"field": "root.effective_at", "bucket": "month"},
                ]
            },
            "not_additive",
        ),
    ],
)
def test_company_context_preserves_partition_and_time_rules(family, changes, code):
    with pytest.raises(TraversalRefused) as failure:
        plan(Traversal.model_validate(question("generation", family=family, **changes)))
    assert failure.value.code == code


def test_company_generation_runs_inventory_and_contribution_graphs(company_database):
    factory, tenant, manifest = jobs._manifest(company_database)
    with factory() as session:
        generation = costing.build_company_cost_generation(
            session, tenant, manifest["id"]
        )["generation_id"]
        session.commit()
    with factory() as session:
        inventory = run_traversal(
            session,
            tenant,
            Traversal.model_validate(question(generation, family="inventory")),
        )
        contribution = run_traversal(
            session, tenant, Traversal.model_validate(question(generation))
        )
        dimensional = run_traversal(
            session,
            tenant,
            Traversal.model_validate(
                question(
                    generation,
                    group_by=[
                        {"field": "root.currency"},
                        {"field": "root.base_unit"},
                        {"field": "root.customer_id"},
                        {"field": "root.item_id"},
                        {"field": "root.sales_channel"},
                    ],
                )
            ),
        )

    assert inventory.rows[0]["inventory_acquisition_value"] == "420.0000"
    assert inventory.cost_basis["generation_id"] == generation
    assert inventory.cost_basis["authority_scope"] == "independent_member_reviews"
    assert contribution.rows[0]["contribution_db1_known"] == "570.0000"
    assert contribution.rows[0]["contribution_db1"] == "570.0000"
    assert contribution.rows[0]["contribution_db1_rate"] == "47.5000"
    assert contribution.rows[0]["contribution_db2"] is None
    assert contribution.rows[0]["contribution_db2_known"] == "0"
    assert contribution.rows[0]["contribution_db2_rate"] is None
    assert contribution.cost_basis["generation_id"] == generation
    assert len(dimensional.rows) == 1
    assert dimensional.rows[0]["contribution_db1_known"] == "570.0000"


def test_unknown_company_members_preserve_coverage_without_inventing_zero(
    company_database,
):
    factory, tenant, manifest = jobs._manifest(company_database, reviewed=False)
    with factory() as session:
        generation = costing.build_company_cost_generation(
            session, tenant, manifest["id"]
        )["generation_id"]
        session.commit()
    with factory() as session:
        result = run_traversal(
            session, tenant, Traversal.model_validate(question(generation))
        )

    row = result.rows[0]
    assert row["contribution_db1"] is None
    assert row["contribution_db1_known"] == "0"
    assert row["contribution_db1_required"] == 1
    assert row["contribution_db1_covered"] == 0
    assert row["contribution_db2"] is None
    assert row["contribution_db2_known"] == "0"


def test_graph_tool_and_saved_report_retain_exact_company_generation(company_database):
    factory, tenant, manifest = jobs._manifest(company_database)
    with factory() as session:
        generation = costing.build_company_cost_generation(
            session, tenant, manifest["id"]
        )["generation_id"]
        session.commit()
    with factory() as session:
        response = invoke(
            session, tenant, "graph.ask", {"question": question(generation)}
        )
        assert response["cost_basis"]["generation_id"] == generation
        user_id = session.scalar(
            select(TenantMembership.user_id).where(
                TenantMembership.tenant_id == tenant,
                TenantMembership.status == "active",
            )
        )
        saved = change_graph_report(
            session,
            tenant,
            Principal(user_id),
            {
                "operation": "create",
                "request_id": str(uuid4()),
                "name": "Company contribution",
                "question": question(generation),
            },
        )
        reopened = get_report(
            session, tenant, Principal(user_id), saved["id"], report_kind="graph"
        )
        assert reopened["definition"]["company_cost_context"] == {
            "generation_id": generation
        }
        rerun = run_traversal(
            session, tenant, Traversal.model_validate(reopened["definition"])
        )
        assert rerun.cost_basis["generation_id"] == generation

        app = FastAPI()
        app.include_router(analytics_api.router, prefix="/tenants/{tenant_id}")
        app.dependency_overrides[auth.database_session] = lambda: session
        with TestClient(app) as client:
            http = client.post(
                f"/tenants/{tenant}/analytics/graph/ask",
                json={"question": reopened["definition"]},
            )
        assert http.status_code == 200, http.text
        assert http.json()["cost_basis"]["generation_id"] == generation


def test_fixed_company_graph_reports_pending_without_changing_values(company_database):
    factory, tenant, manifest = jobs._manifest(company_database)
    with factory() as session:
        generation = costing.build_company_cost_generation(
            session, tenant, manifest["id"]
        )["generation_id"]
        before = run_traversal(
            session, tenant, Traversal.model_validate(question(generation))
        )
        from reality.services import core

        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()
    with factory() as session:
        after = run_traversal(
            session, tenant, Traversal.model_validate(question(generation))
        )

    assert after.rows == before.rows
    assert before.cost_basis["freshness_context"]["state"] == "ready"
    assert after.cost_basis["freshness_context"]["state"] == "pending"


def test_published_company_generation_discovery_is_metadata_only(company_database):
    factory, tenant, manifest = jobs._manifest(company_database)
    with factory() as session:
        generation = costing.build_company_cost_generation(
            session, tenant, manifest["id"]
        )["generation_id"]
        costing.publish_company_cost_generation(
            session, tenant, generation, previous_generation_id=None
        )
        session.commit()
    with factory() as session:
        option = invoke(
            session,
            tenant,
            "graph.company_generation.current",
            {"family": "contribution"},
        )["item"]

    assert option["generation_id"] == generation
    assert option["subject_count"] == 1
    assert option["state"] == "ready"
    assert option["authority_scope"] == "independent_member_reviews"
    assert "rows" not in option and "totals" not in option


def test_company_graph_and_discovery_do_not_disclose_or_write(
    company_database, monkeypatch
):
    from reality.services import core

    factory, tenant, manifest = jobs._manifest(company_database)
    with factory() as session:
        generation = costing.build_company_cost_generation(
            session, tenant, manifest["id"]
        )["generation_id"]
        costing.publish_company_cost_generation(
            session, tenant, generation, previous_generation_id=None
        )
        foreign = core.create_tenant(session, "Foreign company graph").id
        session.commit()
    with factory() as session:
        monkeypatch.setattr(
            session,
            "flush",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("company graph read flushed")
            ),
        )
        assert (
            invoke(
                session,
                tenant,
                "graph.company_generation.current",
                {"family": "inventory"},
            )["item"]["generation_id"]
            == generation
        )
        run_traversal(
            session,
            tenant,
            Traversal.model_validate(question(generation, family="inventory")),
        )
        with pytest.raises(core.NotFound):
            run_traversal(
                session,
                foreign,
                Traversal.model_validate(question(generation, family="inventory")),
            )
        assert invoke(
            session,
            foreign,
            "graph.company_generation.current",
            {"family": "inventory"},
        ) == {"item": None}
