"""Current contribution reads never label an older confirmation as fresh."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
import test_contribution_generations as fixtures
from sqlalchemy import event
from test_contribution_graph_reporting import question

from reality.domain.traversal import Traversal
from reality.services import core, costing
from reality.services.analytics.traversal import TraversalRefused, run_traversal

cost_owner = fixtures.cost_owner


def current_question(action, **changes):
    return question(
        action,
        contribution_cost_context={"action_id": action, "mode": "current"},
        **changes,
    )


def test_current_missing_ready_pending_and_historical(
    session, business, cost_owner, monkeypatch
):
    tenant = business.tenant.id
    action, _ = fixtures.confirmed(session, business, cost_owner)
    missing = costing.contribution_snapshot(session, tenant, action, mode="current")
    assert missing["state"] == missing["freshness"]["state"] == "uninitialized"
    assert missing["freshness"]["processed_event_sequence"] is None
    costing.build_contribution_generation(session, tenant, action)
    historical = costing.contribution_snapshot(session, tenant, action)
    ready = costing.contribution_snapshot(session, tenant, action, mode="current")
    assert ready["state"] == ready["freshness"]["state"] == "ready"
    assert ready["groups"] == historical["groups"]
    assert (
        ready["freshness"]["processed_event_sequence"]
        == ready["freshness"]["target_event_sequence"]
    )
    graph = run_traversal(
        session, tenant, Traversal.model_validate(current_question(action))
    )
    assert graph.cost_basis["freshness"] == ready["freshness"]
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    assert not costing.build_contribution_generation(session, tenant, action)["created"]

    def forbidden(*args, **kwargs):
        raise AssertionError("Current reads must not flush or replay")

    monkeypatch.setattr(session, "flush", forbidden)
    monkeypatch.setattr(costing, "reviewed_contribution", forbidden)
    pending = costing.contribution_snapshot(session, tenant, action, mode="current")
    assert pending["state"] == pending["freshness"]["state"] == "pending"
    assert pending["rows"] == pending["groups"] == []
    assert (
        pending["freshness"]["target_event_sequence"]
        > pending["freshness"]["processed_event_sequence"]
    )
    assert costing.contribution_snapshot(session, tenant, action) == historical
    for filters in ([], [{"field": "root.item_id", "op": "eq", "value": "absent"}]):
        with pytest.raises(TraversalRefused) as failure:
            run_traversal(
                session,
                tenant,
                Traversal.model_validate(current_question(action, filter=filters)),
            )
        assert failure.value.code == "cost_basis_pending"


@pytest.mark.parametrize("mode", ["latest", None, True, 1])
def test_invalid_mode_refuses_before_read(session, business, mode):
    with pytest.raises(core.InvalidOperation, match="mode"):
        costing.contribution_snapshot(session, business.tenant.id, "absent", mode=mode)


@pytest.mark.parametrize("reader", ["snapshot", "graph"])
def test_current_requires_read_committed(scheduled_database, reader):
    _, factory, tenant, actor = scheduled_database
    action, _, _ = fixtures.committed(factory, tenant, actor)
    with factory.begin() as session:
        costing.build_contribution_generation(session, tenant, action)
    with factory() as session:
        session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
        with pytest.raises(core.InvalidOperation, match="READ COMMITTED"):
            if reader == "snapshot":
                costing.contribution_snapshot(session, tenant, action, mode="current")
            else:
                run_traversal(
                    session, tenant, Traversal.model_validate(current_question(action))
                )
        assert (
            costing.contribution_snapshot(session, tenant, action)["state"]
            == "historical"
        )


@pytest.mark.parametrize("reader", ["snapshot", "graph"])
def test_late_intake_after_numeric_read_is_detected_without_blocking(
    scheduled_database, reader
):
    _, factory, tenant, actor = scheduled_database
    action, item, location = fixtures.committed(factory, tenant, actor)
    with factory.begin() as session:
        costing.build_contribution_generation(session, tenant, action)
    checked, resume = Event(), Event()

    def read():
        with factory.begin() as session:
            connection = session.connection()
            grouped_reads = 0

            def after_sql(conn, cursor, statement, parameters, context, executemany):
                nonlocal grouped_reads
                if (
                    "GROUP BY" in statement
                    and "cost_contribution_snapshot" in statement
                ):
                    grouped_reads += 1
                    if grouped_reads == (2 if reader == "snapshot" else 1):
                        checked.set()
                        assert resume.wait(15)

            event.listen(connection, "after_cursor_execute", after_sql)
            try:
                if reader == "snapshot":
                    return costing.contribution_snapshot(
                        session, tenant, action, mode="current"
                    )
                with pytest.raises(TraversalRefused) as failure:
                    run_traversal(
                        session,
                        tenant,
                        Traversal.model_validate(current_question(action)),
                    )
                assert failure.value.code == "cost_basis_pending"
                return None
            finally:
                event.remove(connection, "after_cursor_execute", after_sql)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(read)
        try:
            assert checked.wait(15)
            with factory.begin() as session:
                core.record_movement(
                    session, tenant, "receipt", item, "1", to_location_id=location
                )
        finally:
            resume.set()
        result = future.result(timeout=15)
    if reader == "snapshot":
        assert result["state"] == "pending" and result["rows"] == result["groups"] == []


def test_current_http_saved_mode_and_foreign_scope(session, business, cost_owner):
    from uuid import uuid4

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from reality.services.analytics.reports import change_graph_report, get_report
    from reality.services.memberships import Principal
    from reality.web import analytics_api, auth

    tenant = business.tenant.id
    action, _ = fixtures.confirmed(session, business, cost_owner)
    costing.build_contribution_generation(session, tenant, action)
    principal = Principal(cost_owner.id)
    saved = change_graph_report(
        session,
        tenant,
        principal,
        {
            "operation": "create",
            "request_id": str(uuid4()),
            "name": "Unchanged contribution",
            "question": current_question(action),
        },
    )
    reopened = get_report(session, tenant, principal, saved["id"], report_kind="graph")
    assert reopened["definition"]["contribution_cost_context"]["mode"] == "current"
    foreign = core.create_tenant(session, "Foreign")
    for fn in (
        lambda: costing.contribution_snapshot(
            session, foreign.id, action, mode="current"
        ),
        lambda: run_traversal(
            session, foreign.id, Traversal.model_validate(current_question(action))
        ),
    ):
        with pytest.raises(core.NotFound):
            fn()
    saved_read = run_traversal(
        session, tenant, Traversal.model_validate(reopened["definition"])
    )
    assert saved_read.cost_basis["freshness"]["state"] == "ready"
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    app = FastAPI()
    app.include_router(analytics_api.router, prefix="/tenants/{tenant_id}")
    app.dependency_overrides[auth.database_session] = lambda: session
    with TestClient(app) as client:
        path = f"/tenants/{tenant}/analytics/graph/ask"
        response = client.post(path, json={"question": reopened["definition"]})
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "cost_basis_pending"
        historical = client.post(path, json={"question": question(action)})
        assert historical.status_code == 200
        assert historical.json()["cost_basis"]["freshness"]["state"] == "historical"


def test_current_cursor_regression_refuses_and_history_avoids_live_cursor(
    session, business, cost_owner, monkeypatch
):
    from reality.services import contribution_generations

    tenant = business.tenant.id
    action, _ = fixtures.confirmed(session, business, cost_owner)
    costing.build_contribution_generation(session, tenant, action)
    monkeypatch.setattr(contribution_generations, "_sequence", lambda *_args: 0)
    with pytest.raises(core.InvalidOperation, match="cursor"):
        costing.contribution_snapshot(session, tenant, action, mode="current")
    with pytest.raises(core.InvalidOperation, match="cursor"):
        run_traversal(
            session, tenant, Traversal.model_validate(current_question(action))
        )

    def forbidden(*args, **kwargs):
        raise AssertionError("Historical reads must not consult the live cursor")

    monkeypatch.setattr(contribution_generations, "_sequence", forbidden)
    assert (
        costing.contribution_snapshot(session, tenant, action)["state"] == "historical"
    )
    assert run_traversal(
        session, tenant, Traversal.model_validate(question(action))
    ).rows
