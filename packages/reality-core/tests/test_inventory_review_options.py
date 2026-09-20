"""Discovery is scoped confirmation metadata, never valuation approval or readiness."""

from types import SimpleNamespace

import pytest
import test_inventory_batch_generations as fixtures
from sqlalchemy import event

from reality.services import core
from reality.services.analytics import inventory_options
from reality.tools.application import run_read_tool

cost_owner = fixtures.cost_owner


def test_options_are_scoped_bounded_and_not_cache_readiness(
    session, business, cost_owner, monkeypatch
):
    tenant = business.tenant.id
    older, _ = fixtures.confirmed(session, business, cost_owner)
    other = SimpleNamespace(**vars(business))
    other.item = core.create_item(session, tenant, "THIRD", "Third")
    newer, _ = fixtures.confirmed(session, other, cost_owner)

    def forbidden(*args, **kwargs):
        raise AssertionError("Discovery must not flush or replay")

    monkeypatch.setattr(session, "flush", forbidden)
    statements = []
    connection = session.connection()

    def track(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(connection, "before_cursor_execute", track)
    try:
        first = run_read_tool(
            session, tenant, "graph.inventory_reviews.list", {"limit": 1}
        )
    finally:
        event.remove(connection, "before_cursor_execute", track)
    assert len(statements) <= 3
    assert first["next_cursor"] == newer
    assert first["items"][0]["action_id"] == newer
    assert first["items"][0]["item_count"] == 2
    assert first["items"][0]["currency"] == "EUR"
    assert first["items"][0]["owner_name"] == business.company.name
    assert "acquisition_value" not in first["items"][0]
    second = inventory_options.inventory_review_options(
        session, tenant, limit=1, cursor=newer
    )
    assert second["items"][0]["action_id"] == older
    assert second["next_cursor"] is None
    assert all("cost_inventory_generation" not in sql for sql in statements)


def test_foreign_and_missing_cursors_do_not_disclose(session, business, cost_owner):
    action, _ = fixtures.confirmed(session, business, cost_owner)
    foreign = core.create_tenant(session, "Other company")
    assert (
        inventory_options.inventory_review_options(session, foreign.id)["items"] == []
    )
    for tenant, cursor in [(foreign.id, action), (foreign.id, "missing")]:
        with pytest.raises(core.NotFound, match="Inventory selection not found"):
            inventory_options.inventory_review_options(session, tenant, cursor=cursor)


@pytest.mark.parametrize("limit", [0, 51, True, "2"])
def test_bounds_refuse_before_sql(session, business, limit):
    with pytest.raises(core.InvalidOperation):
        inventory_options.inventory_review_options(
            session, business.tenant.id, limit=limit
        )


def test_http_metadata_and_foreign_cursor(session, business, cost_owner):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from reality.web import analytics_api, auth

    action, _ = fixtures.confirmed(session, business, cost_owner)
    foreign = core.create_tenant(session, "Other company")
    app = FastAPI()
    app.include_router(analytics_api.router, prefix="/tenants/{tenant_id}")
    app.dependency_overrides[auth.database_session] = lambda: session
    with TestClient(app) as client:
        path = f"/tenants/{business.tenant.id}/analytics/graph/inventory-reviews"
        response = client.get(path)
        assert response.status_code == 200, response.text
        assert response.json()["items"][0]["action_id"] == action
        hidden = client.get(
            f"/tenants/{foreign.id}/analytics/graph/inventory-reviews",
            params={"cursor": action},
        )
        assert hidden.status_code == 404


def test_single_item_confirmation_is_not_offered_as_joint_scope(
    session, business, cost_owner
):
    single = fixtures.fixtures.fixtures
    args, _, _ = single.prepared(session, business, cost_owner)
    action, _ = single.commit_review(session, business, cost_owner, args)
    assert (
        inventory_options.inventory_review_options(session, business.tenant.id)["items"]
        == []
    )
    with pytest.raises(core.NotFound):
        inventory_options.inventory_review_options(
            session, business.tenant.id, cursor=action.id
        )
