"""One retained basis accompanies each cost answer without inventing global authority."""

import pytest
import test_cost_records as fixtures
from pydantic import ValidationError
from sqlalchemy import event

from reality.domain.cost_query import (
    CostQueryRequest,
    compatible_contexts,
    cost_guidance,
)
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core
from reality.services.costing import cost_query
from reality.tools.application import run_read_tool

cost_owner = fixtures.cost_owner


@pytest.mark.parametrize(
    ("stage", "tool", "principal"),
    [
        ("uninitialized", "cost_change_propose", "authenticated_active_owner"),
        ("pending", "cost_query_get", "authorized_reader"),
        ("stale", "cost_change_propose", "authenticated_active_owner"),
        ("failed", "cost_evidence_get", "authorized_reader"),
        ("complete", None, None),
    ],
)
def test_cost_guidance_stages_name_bounded_next_authority(stage, tool, principal):
    guidance = cost_guidance(
        kind="inventory",
        scope_id="item_opaque",
        stage=stage,
        missing_basis=["acquisition_evidence"] if stage != "complete" else [],
        review_state="test_state",
        explanation_links=[{"kind": "movement", "id": "mov_opaque"}],
    )

    assert guidance["scope"] == {"kind": "inventory", "id": "item_opaque"}
    assert guidance["stage"] == stage
    assert guidance["review_state"] == "test_state"
    assert guidance["reason"]
    assert guidance["explanation_links"] == [{"kind": "movement", "id": "mov_opaque"}]
    if tool is None:
        assert guidance["next_action"] is None
    else:
        assert guidance["next_action"]["tool"] == tool
        assert guidance["next_action"]["required_principal"] == principal


def test_request_is_strict_and_timezone_aware():
    for values in [
        {"kind": "table", "scope_id": "x"},
        {"kind": "inventory", "scope_id": ""},
        {"kind": "inventory", "scope_id": "x", "effective_at": "2026-01-01"},
        {"kind": "inventory", "scope_id": "x", "tenant_id": "other"},
    ]:
        with pytest.raises(ValidationError):
            CostQueryRequest(**values)
    request = CostQueryRequest(
        kind="inventory", scope_id="x", effective_at="2026-01-01T02:00:00+02:00"
    )
    assert request.effective_at.isoformat() == "2026-01-01T00:00:00+00:00"


def test_context_current_history_constraints_and_shared_tools(
    session, business, cost_owner
):
    review, data, _ = fixtures.prepared(session, business, cost_owner)
    args = {"kind": "contribution", "scope_id": data[0].id}
    core.emit_business_event(
        session,
        business.tenant.id,
        "payment.recorded",
        "tenant",
        business.tenant.id,
        {"amount": "1"},
    )
    current = cost_query(session, business.tenant.id, **args)
    assert current["freshness"]["state"] == "ready"
    assert current["result"]["db2"] == "456.0000"
    assert current["resolved"]["generation_id"] is None
    assert current["resolved"]["profile_revision_id"] is None
    assert current["resolved"]["scope_profile_review_id"] == review["review_id"]
    historical = cost_query(
        session, business.tenant.id, **args, review_id=review["review_id"]
    )
    assert historical["freshness"]["state"] == "historical"
    assert compatible_contexts(current, historical)
    assert historical["requested"]["review_id"] == review["review_id"]
    assert run_read_tool(session, business.tenant.id, "cost.query.get", args) == current
    assert (
        MCP_TOOL_REGISTRY["cost_query_get"].handler(session, business.tenant.id, args)
        == current
    )
    for constraint in [
        {"effective_at": "2000-01-01T00:00:00Z"},
        {"knowledge_at": "2000-01-01T00:00:00Z"},
        {"policy_revision_id": "absent"},
    ]:
        with pytest.raises(core.InvalidOperation, match="cost_context_unsupported"):
            cost_query(session, business.tenant.id, **args, **constraint)
    assert (
        cost_query(
            session,
            business.tenant.id,
            **args,
            effective_at=current["resolved"]["effective_at"],
        )["context_id"]
        == current["context_id"]
    )
    other = core.create_tenant(session, "Neighbor")
    with pytest.raises(core.NotFound):
        cost_query(session, other.id, **args, review_id=review["review_id"])


def test_stale_context_keeps_only_retained_result_and_history_is_stable(
    session, business, cost_owner
):
    review, data, _ = fixtures.prepared(session, business, cost_owner)
    args = {"kind": "contribution", "scope_id": data[0].id}
    previous = cost_query(
        session, business.tenant.id, **args, review_id=review["review_id"]
    )
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    stale = cost_query(session, business.tenant.id, **args)
    assert stale["freshness"]["state"] == "stale"
    assert stale["guidance"]["stage"] == "stale"
    assert stale["guidance"]["next_action"] == {
        "tool": "cost_change_propose",
        "operation": "contribution_review",
        "required_principal": "authenticated_active_owner",
    }
    assert stale["result"] is None and stale["basis_result"]["basis_db2"] == "456.0000"
    statements = []

    def watch(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    event.listen(session.bind, "before_cursor_execute", watch)
    try:
        historical = cost_query(
            session, business.tenant.id, **args, review_id=review["review_id"]
        )
    finally:
        event.remove(session.bind, "before_cursor_execute", watch)
    assert historical == previous
    assert not any("max(business_event.sequence)" in sql for sql in statements)
    assert not any(
        sql.lstrip().startswith(("insert", "update", "delete")) for sql in statements
    )
    assert compatible_contexts(stale, historical)


def test_inventory_context_and_unreviewed_scope(session, business, cost_owner):
    empty = cost_query(
        session, business.tenant.id, kind="inventory", scope_id=business.item.id
    )
    assert empty["freshness"]["state"] == "uninitialized"
    assert empty["guidance"]["stage"] == "uninitialized"
    assert empty["guidance"]["scope"] == {
        "kind": "inventory",
        "id": business.item.id,
    }
    assert empty["resolved"] is None and empty["context_id"] is None
    assert not compatible_contexts(empty, empty)
    review, data, _ = fixtures.prepared(session, business, cost_owner)
    result = cost_query(
        session,
        business.tenant.id,
        kind="inventory",
        scope_id=business.item.id,
        review_id=review["trace"]["inventory_review_id"],
    )
    assert result["resolved"]["method"] == "fifo"
    assert result["result"]["acquisition_value"] == "420.0000"
    assert result["result"]["carrying_value"] is None
    assert result["resolved"]["profile_revision_id"] is None
    contribution = cost_query(
        session, business.tenant.id, kind="contribution", scope_id=data[0].id
    )
    assert not compatible_contexts(result, contribution)


def test_cli_no_initialization_and_read_does_not_flush(
    session, business, cost_owner, monkeypatch
):
    import json
    from contextlib import contextmanager

    from typer.testing import CliRunner

    from reality.cli import app as cli
    from reality.db.core import Item

    review, data, _ = fixtures.prepared(session, business, cost_owner)
    args = {
        "kind": "contribution",
        "scope_id": data[0].id,
        "review_id": review["review_id"],
    }
    expected = cost_query(session, business.tenant.id, **args)
    pending = Item(
        id="unflushed_context",
        tenant_id=business.tenant.id,
        sku="pending",
        name="pending",
    )
    session.add(pending)
    assert cost_query(session, business.tenant.id, **args) == expected
    assert pending in session.new
    session.expunge(pending)

    @contextmanager
    def scope():
        yield session

    monkeypatch.setattr(cli, "Session", scope)
    monkeypatch.setattr(
        cli, "init_db", lambda: pytest.fail("Read must not initialize schema")
    )
    output = CliRunner().invoke(
        cli.app,
        [
            "cost-query",
            "contribution",
            data[0].id,
            "--tenant-id",
            business.tenant.id,
            "--review-id",
            review["review_id"],
        ],
    )
    assert output.exit_code == 0, output.output
    assert json.loads(output.output) == expected


def test_missing_constraints_and_foreign_tool_scope_refuse(
    session, business, cost_owner
):
    with pytest.raises(core.InvalidOperation, match="cost_context_unsupported"):
        cost_query(
            session,
            business.tenant.id,
            kind="inventory",
            scope_id=business.item.id,
            policy_revision_id="missing",
        )
    review, data, _ = fixtures.prepared(session, business, cost_owner)
    other = core.create_tenant(session, "Neighbor")
    args = {
        "kind": "contribution",
        "scope_id": data[0].id,
        "review_id": review["review_id"],
    }
    for tenant in (other.id, "absent"):
        with pytest.raises(core.NotFound):
            run_read_tool(session, tenant, "cost.query.get", args)
        with pytest.raises(core.NotFound):
            MCP_TOOL_REGISTRY["cost_query_get"].handler(session, tenant, args)
    with pytest.raises(core.NotFound):
        cost_query(
            session,
            business.tenant.id,
            kind="inventory",
            scope_id=business.item.id,
            review_id=review["review_id"],
        )


def test_ready_does_not_promote_unknown_db2_and_repeatable_current_refuses(
    session, business, cost_owner, monkeypatch
):
    args, data = fixtures.revenue.prepared(session, business, cost_owner)
    _, review = fixtures.stock.commit_review(session, business, cost_owner, args)
    current = cost_query(
        session, business.tenant.id, kind="contribution", scope_id=data[0].id
    )
    assert current["freshness"]["state"] == "ready"
    assert current["result"]["db1"] == "570.0000"
    assert current["result"]["db2"] is None
    assert "selling_costs_unknown" in current["result"]["missing_basis"]
    connection = session.connection()
    monkeypatch.setattr(connection, "get_isolation_level", lambda: "REPEATABLE READ")
    with pytest.raises(core.InvalidOperation, match="READ COMMITTED"):
        cost_query(
            session, business.tenant.id, kind="contribution", scope_id=data[0].id
        )
    historical = cost_query(
        session,
        business.tenant.id,
        kind="contribution",
        scope_id=data[0].id,
        review_id=review["review_id"],
    )
    assert historical["result"]["db1"] == "570.0000"


def test_http_query_uses_same_context_and_refusals(
    session, business, cost_owner, monkeypatch
):
    from test_http_boundary import client_for

    review, data, _ = fixtures.prepared(session, business, cost_owner)
    args = {
        "kind": "contribution",
        "scope_id": data[0].id,
        "review_id": review["review_id"],
    }
    expected = cost_query(session, business.tenant.id, **args)
    client = client_for(session, monkeypatch)
    path = f"/api/tenants/{business.tenant.id}/cost-query"
    response = client.get(path, params=args)
    assert response.status_code == 200
    assert response.json() == expected
    assert (
        client.get(
            path, params={**args, "knowledge_at": "2000-01-01T00:00:00Z"}
        ).status_code
        == 422
    )
    other = core.create_tenant(session, "Neighbor")
    assert (
        client.get(f"/api/tenants/{other.id}/cost-query", params=args).status_code
        == 404
    )
