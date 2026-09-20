"""Historical graph sums keep the confirmed inventory basis through execution."""

from decimal import Decimal
from uuid import uuid4

import pytest
import test_inventory_costing_relation as fixtures
from sqlalchemy import update

from reality.db.cost_generations import CostInventorySnapshot
from reality.domain.traversal import Traversal
from reality.services import core, costing
from reality.services.analytics.reports import change_graph_report, get_report
from reality.services.analytics.traversal import TraversalRefused, plan, run_traversal
from reality.services.memberships import Principal
from reality.tools.graph import invoke

cost_owner = fixtures.cost_owner


def question(action, **changes):
    return {
        "from": "inventory_valuation",
        "inventory_cost_context": {"action_id": action, "mode": "historical"},
        "measures": ["inventory_acquisition_value"],
        "group_by": [{"field": "root.currency"}],
        **changes,
    }


def test_graph_tool_uses_exact_complete_basis(session, business, cost_owner):
    tenant = business.tenant.id
    action, ids = fixtures.stored(session, business, cost_owner)
    catalog = invoke(session, tenant, "graph.catalog", {"node": "inventory_valuation"})
    quantity = next(
        m
        for m in catalog["nodes"][0]["measures"]
        if m["key"] == "inventory_remaining_quantity"
    )
    assert "base_unit" in quantity["never_across"]
    response = invoke(session, tenant, "graph.ask", {"question": question(action)})
    assert response["rows"] == [
        {"root.currency": "EUR", "inventory_acquisition_value": "840.0000"}
    ]
    assert response["cost_basis"]["action_id"] == action
    assert response["cost_basis"]["generation_ids"] == ids
    assert response["cost_basis"]["freshness"]["state"] == "historical"
    assert response["cost_basis"]["coverage"] == {
        "expected_items": 2,
        "available_items": 2,
    }
    assert response["question"]["inventory_cost_context"]["action_id"] == action
    assert response["editor"]["path"] is None
    assert "context" in response["editor"]["reason"].lower()
    assert response["statements"] <= 10
    assert "jsonb_to_recordset" not in response["sql"]
    assert "cost_inventory_publication" not in response["sql"]
    quantities = run_traversal(
        session,
        tenant,
        Traversal.model_validate(
            question(
                action,
                measures=["inventory_remaining_quantity"],
                group_by=[{"field": "root.base_unit"}],
                order_by=[{"by": "root.base_unit"}],
            )
        ),
    )
    assert quantities.rows == (
        {"root.base_unit": "kg", "inventory_remaining_quantity": "40.0000"},
        {"root.base_unit": "pcs", "inventory_remaining_quantity": "40.0000"},
    )


@pytest.mark.parametrize(
    "change,code",
    [
        ({"inventory_cost_context": None}, "cost_context_required"),
        ({"group_by": []}, "unit_mismatch"),
        (
            {
                "group_by": [
                    {"field": "root.currency"},
                    {"field": "root.effective_at", "bucket": "month"},
                ]
            },
            "not_additive",
        ),
    ],
)
def test_invalid_context_or_aggregation_refuses_before_sql(change, code):
    with pytest.raises(TraversalRefused) as failure:
        plan(Traversal.model_validate(question("action", **change)))
    assert failure.value.code == code


def test_context_cannot_be_silently_ignored():
    with pytest.raises(TraversalRefused, match="context"):
        plan(
            Traversal.model_validate(
                question(
                    "action",
                    **{
                        "from": "order",
                        "measures": ["stated_order_amount"],
                    },
                )
            )
        )


def test_missing_partial_foreign_and_corrupt_basis_refuse(
    session, business, cost_owner
):
    tenant = business.tenant.id
    action, reviews = fixtures.fixtures.confirmed(session, business, cost_owner)
    for _ in range(2):
        with pytest.raises(TraversalRefused) as failure:
            run_traversal(session, tenant, Traversal.model_validate(question(action)))
        assert failure.value.code == "cost_basis_unavailable"
        costing.build_inventory_generation(session, tenant, reviews[0])
    built = costing.build_inventory_batch_generation(session, tenant, action)
    foreign = core.create_tenant(session, "Other company")
    for selected_tenant, selected_action in [(foreign.id, action), (tenant, "absent")]:
        with pytest.raises(core.NotFound):
            run_traversal(
                session,
                selected_tenant,
                Traversal.model_validate(question(selected_action)),
            )
    session.execute(
        update(CostInventorySnapshot)
        .where(
            CostInventorySnapshot.tenant_id == tenant,
            CostInventorySnapshot.generation_id == built["generation_ids"][0],
        )
        .values(acquisition_value=Decimal(1))
    )
    with pytest.raises(core.InvalidOperation, match="integrity"):
        run_traversal(session, tenant, Traversal.model_validate(question(action)))


def test_saved_context_history_empty_filter_and_no_replay(
    session, business, cost_owner, monkeypatch
):
    tenant = business.tenant.id
    action, _ = fixtures.stored(session, business, cost_owner)
    principal = Principal(cost_owner.id)
    saved = change_graph_report(
        session,
        tenant,
        principal,
        {
            "operation": "create",
            "request_id": str(uuid4()),
            "name": "Inventory value",
            "question": question(action),
        },
    )
    reopened = get_report(session, tenant, principal, saved["id"], report_kind="graph")
    assert reopened["definition"]["inventory_cost_context"]["action_id"] == action
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Report must not flush or replay movements")

    monkeypatch.setattr(session, "flush", forbidden)
    monkeypatch.setattr(costing, "inventory_cost", forbidden)
    assert (
        invoke(session, tenant, "graph.ask", {"question": question(action)})["rows"][0][
            "inventory_acquisition_value"
        ]
        == "840.0000"
    )
    result = run_traversal(
        session, tenant, Traversal.model_validate(reopened["definition"])
    )
    assert result.rows[0]["inventory_acquisition_value"] == "840.0000"
    empty = run_traversal(
        session,
        tenant,
        Traversal.model_validate(
            question(
                action,
                filter=[{"field": "root.item_id", "op": "eq", "value": "absent"}],
            )
        ),
    )
    assert empty.rows == ()
    assert empty.cost_basis["generation_ids"] == result.cost_basis["generation_ids"]


@pytest.mark.parametrize("mutation", ["delete", "update"])
def test_cache_is_protected_through_final_aggregate(
    scheduled_database, monkeypatch, mutation
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from sqlalchemy import delete, text
    from sqlalchemy.exc import OperationalError

    from reality.services.analytics import costing_relation

    _, factory, tenant, actor = scheduled_database
    action, item, location = fixtures.fixtures.prepare_committed(factory, tenant, actor)
    with factory.begin() as session:
        costing.build_inventory_batch_generation(session, tenant, action)
    checked, resume = Event(), Event()
    original = costing_relation.report_relation

    def pause(*args, **kwargs):
        value = original(*args, **kwargs)
        checked.set()
        assert resume.wait(15)
        return value

    monkeypatch.setattr(costing_relation, "report_relation", pause)

    def read():
        with factory.begin() as session:
            return run_traversal(
                session, tenant, Traversal.model_validate(question(action))
            )

    statement = (
        delete(CostInventorySnapshot)
        if mutation == "delete"
        else update(CostInventorySnapshot).values(acquisition_value=1)
    ).where(CostInventorySnapshot.tenant_id == tenant)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(read)
        try:
            assert checked.wait(15)
            with factory() as session:
                session.execute(text("SET LOCAL lock_timeout = '200ms'"))
                with pytest.raises(OperationalError, match="lock timeout"):
                    session.execute(statement)
                session.rollback()
            # The report's cache locks must not block normal business intake.
            with factory.begin() as session:
                core.record_movement(
                    session, tenant, "receipt", item, "1", to_location_id=location
                )
        finally:
            resume.set()
        assert (
            future.result(timeout=15).rows[0]["inventory_acquisition_value"]
            == "840.0000"
        )
    with factory.begin() as session:
        assert session.execute(statement).rowcount == 2


def test_http_transport_preserves_basis_and_refusal(session, business, cost_owner):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from reality.web import analytics_api, auth

    action, ids = fixtures.stored(session, business, cost_owner)
    app = FastAPI()
    app.include_router(analytics_api.router, prefix="/tenants/{tenant_id}")
    app.dependency_overrides[auth.database_session] = lambda: session
    with TestClient(app) as client:
        url = f"/tenants/{business.tenant.id}/analytics/graph/ask"
        response = client.post(url, json={"question": question(action)})
        assert response.status_code == 200, response.text
        assert response.json()["cost_basis"]["generation_ids"] == ids
        assert response.json()["rows"][0]["inventory_acquisition_value"] == "840.0000"
        refused = client.post(
            url, json={"question": question(action, inventory_cost_context=None)}
        )
        assert refused.status_code == 422
        assert refused.json()["detail"]["code"] == "cost_context_required"
