"""Confirmed contribution graph totals retain coverage after filtering."""

import pytest
import test_contribution_generations as fixtures
from sqlalchemy import update

from reality.db.cost_generations import CostContributionSnapshot
from reality.domain.traversal import Traversal
from reality.services import core, costing
from reality.services.analytics.traversal import TraversalRefused, plan, run_traversal
from reality.tools.graph import invoke

cost_owner = fixtures.cost_owner


def question(action, **changes):
    return {
        "from": "contribution_valuation",
        "contribution_cost_context": {"action_id": action, "mode": "historical"},
        "measures": [
            "contribution_db1",
            "contribution_db2",
            "contribution_db2_known",
            "contribution_db2_covered",
            "contribution_db2_required",
            "contribution_db1_rate",
        ],
        "group_by": [{"field": "root.currency"}, {"field": "root.base_unit"}],
        "order_by": [{"by": "root.base_unit"}],
        **changes,
    }


def test_exact_graph_coverage_filter_and_no_replay(
    session, business, cost_owner, monkeypatch
):
    tenant = business.tenant.id
    action, _ = fixtures.confirmed(session, business, cost_owner)
    built = costing.build_contribution_generation(session, tenant, action)

    def forbidden(*args, **kwargs):
        raise AssertionError("Graph must not flush or replay FIFO")

    monkeypatch.setattr(session, "flush", forbidden)
    monkeypatch.setattr(costing, "reviewed_contribution", forbidden)
    catalog = invoke(
        session, tenant, "graph.catalog", {"node": "contribution_valuation"}
    )
    properties = {entry["key"]: entry for entry in catalog["nodes"][0]["properties"]}
    assert properties["effective_at"]["kind"] == "time"
    assert properties["economic_at"]["temporal"] == "date"
    response = invoke(session, tenant, "graph.ask", {"question": question(action)})
    assert response["cost_basis"]["generation_ids"] == [built["generation_id"]]
    assert response["cost_basis"]["coverage"] == {
        "expected_positions": 2,
        "available_positions": 2,
    }
    assert response["editor"]["path"] is None
    assert "context" in response["editor"]["reason"].lower()
    rows = response["rows"]
    assert len(rows) == 2
    assert all(row["contribution_db1"] == "570.0000" for row in rows)
    assert all(row["contribution_db1_rate"] == "47.5000" for row in rows)
    assert {row["contribution_db2"] for row in rows} == {None, "570.0000"}
    assert {row["contribution_db2_covered"] for row in rows} == {0, 1}
    complete = next(row for row in rows if row["contribution_db2"] is not None)
    filtered = invoke(
        session,
        tenant,
        "graph.ask",
        {
            "question": question(
                action,
                filter=[
                    {
                        "field": "root.base_unit",
                        "op": "eq",
                        "value": complete["root.base_unit"],
                    }
                ],
            )
        },
    )
    assert filtered["rows"] == [complete]
    empty = invoke(
        session,
        tenant,
        "graph.ask",
        {
            "question": question(
                action,
                filter=[{"field": "root.item_id", "op": "eq", "value": "absent"}],
            )
        },
    )
    assert empty["rows"] == []
    assert "jsonb_to_recordset" not in response["sql"]


@pytest.mark.parametrize(
    "change,code",
    [
        ({"contribution_cost_context": None}, "cost_context_required"),
        ({"group_by": []}, "unit_mismatch"),
        ({"inventory_cost_context": {"action_id": "other"}}, "cost_context_invalid"),
        (
            {"from": "order", "measures": ["stated_order_amount"]},
            "cost_context_invalid",
        ),
        (
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
def test_context_and_grain_refusal(change, code):
    with pytest.raises(TraversalRefused) as failure:
        plan(Traversal.model_validate(question("action", **change)))
    assert failure.value.code == code


def test_missing_foreign_and_corrupt_generation(session, business, cost_owner):
    tenant = business.tenant.id
    action, _ = fixtures.confirmed(session, business, cost_owner)
    with pytest.raises(TraversalRefused) as failure:
        run_traversal(session, tenant, Traversal.model_validate(question(action)))
    assert failure.value.code == "cost_basis_unavailable"
    costing.build_contribution_generation(session, tenant, action)
    foreign = core.create_tenant(session, "Foreign")
    with pytest.raises(core.NotFound):
        run_traversal(session, foreign.id, Traversal.model_validate(question(action)))
    session.execute(
        update(CostContributionSnapshot)
        .where(CostContributionSnapshot.tenant_id == tenant)
        .values(goods_cost=1)
    )
    with pytest.raises(core.InvalidOperation, match="integrity"):
        run_traversal(session, tenant, Traversal.model_validate(question(action)))


def test_same_unit_partial_group_and_saved_http_question(session, business, cost_owner):
    from uuid import uuid4

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from reality.services.analytics.reports import change_graph_report, get_report
    from reality.services.memberships import Principal
    from reality.web import analytics_api, auth

    tenant = business.tenant.id
    args, _, _ = fixtures.fixtures.prepared(
        session, business, cost_owner, second_unit="pcs"
    )
    action, _ = fixtures.fixtures.stock.commit_review(
        session, business, cost_owner, args
    )
    costing.build_contribution_generation(session, tenant, action.id)
    principal = Principal(cost_owner.id)
    saved = change_graph_report(
        session,
        tenant,
        principal,
        {
            "operation": "create",
            "request_id": str(uuid4()),
            "name": "Contribution",
            "question": question(action.id),
        },
    )
    reopened = get_report(session, tenant, principal, saved["id"], report_kind="graph")
    assert reopened["definition"]["contribution_cost_context"]["action_id"] == action.id
    app = FastAPI()
    app.include_router(analytics_api.router, prefix="/tenants/{tenant_id}")
    app.dependency_overrides[auth.database_session] = lambda: session
    with TestClient(app) as client:
        response = client.post(
            f"/tenants/{tenant}/analytics/graph/ask",
            json={"question": reopened["definition"]},
        )
    assert response.status_code == 200, response.text
    assert response.json()["rows"] == [
        {
            "root.currency": "EUR",
            "root.base_unit": "pcs",
            "contribution_db1": "1140.0000",
            "contribution_db2": None,
            "contribution_db2_known": "570.0000",
            "contribution_db2_covered": 1,
            "contribution_db2_required": 2,
            "contribution_db1_rate": "47.5000",
        }
    ]
    bucketed = run_traversal(
        session,
        tenant,
        Traversal.model_validate(
            question(
                action.id,
                group_by=[
                    {"field": "root.currency"},
                    {"field": "root.base_unit"},
                    {"field": "root.economic_at", "bucket": "month"},
                ],
            )
        ),
    )
    assert len(bucketed.rows) == 1
    assert bucketed.rows[0]["contribution_db2"] is None


@pytest.mark.parametrize("mutation", ["delete", "update"])
def test_graph_protects_cache_through_final_sql(
    scheduled_database, monkeypatch, mutation
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from sqlalchemy import delete, text
    from sqlalchemy.exc import OperationalError

    from reality.services.analytics import contribution_relation

    _, factory, tenant, actor = scheduled_database
    action, item, location = fixtures.committed(factory, tenant, actor)
    with factory.begin() as session:
        costing.build_contribution_generation(session, tenant, action)
    checked, resume = Event(), Event()
    original = contribution_relation.report_relation

    def pause(*args, **kwargs):
        result = original(*args, **kwargs)
        checked.set()
        assert resume.wait(15)
        return result

    monkeypatch.setattr(contribution_relation, "report_relation", pause)

    def read():
        with factory.begin() as session:
            return run_traversal(
                session, tenant, Traversal.model_validate(question(action))
            )

    statement = (
        delete(CostContributionSnapshot)
        if mutation == "delete"
        else update(CostContributionSnapshot).values(goods_cost=1)
    ).where(CostContributionSnapshot.tenant_id == tenant)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(read)
        try:
            assert checked.wait(15)
            with factory() as session:
                session.execute(text("SET LOCAL lock_timeout = '200ms'"))
                with pytest.raises(OperationalError, match="lock timeout"):
                    session.execute(statement)
                session.rollback()
            with factory.begin() as session:
                core.record_movement(
                    session, tenant, "receipt", item, "1", to_location_id=location
                )
        finally:
            resume.set()
        assert future.result(timeout=15).rows[0]["contribution_db1"] == "570.0000"
    with factory.begin() as session:
        assert session.execute(statement).rowcount == 2
