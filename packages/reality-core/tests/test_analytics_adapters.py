"""Application and MCP analytics expose strict shared contracts."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from test_analytics_execution import orders, request
from test_analytics_reports import create_args
from typer.testing import CliRunner

from reality.mcp.catalog import MCP_TOOL_REGISTRY, dispatch_tool
from reality.services.analytics.contributors import contributors
from reality.services.analytics.execution import query
from reality.services.analytics.exports import export_csv
from reality.services.analytics.reports import change_report, get_report, list_reports
from reality.services.core import NotFound, create_tenant
from reality.services.memberships import Principal
from reality.tools.application import run_read_tool


def test_catalog_is_the_same_application_capability(session, business):
    direct = run_read_tool(session, business.tenant.id, "analytics.catalog", {})
    remote = dispatch_tool(session, business.tenant.id, "analytics_catalog", {})
    assert direct == remote
    assert any(d["key"] == "sales_order_lines" for d in remote["datasets"])
    schema = MCP_TOOL_REGISTRY["analytics_query"].input_schema
    assert schema["additionalProperties"] is False
    assert "definition" in schema["properties"]
    assert "sql" not in schema["properties"]


def test_catalog_web_and_cli_adapters_reuse_the_application_capability(
    session, business, monkeypatch
):
    from reality.cli import app as cli_module
    from reality.web import api as api_module
    from reality.web import auth as auth_module
    from reality.web.app import app

    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    monkeypatch.setattr(cli_module, "read_current_tenant", lambda: business.tenant.id)

    def database():
        with factory() as api_session:
            yield api_session

    app.dependency_overrides[api_module.database_session] = database
    app.dependency_overrides[auth_module.database_session] = database
    try:
        web = TestClient(app).get(
            f"/api/tenants/{business.tenant.id}/analytics/catalog",
            params={"dataset": "sales_orders"},
        )
        cli = CliRunner().invoke(
            cli_module.app, ["analytics", "catalog", "--dataset", "sales_orders"]
        )
    finally:
        app.dependency_overrides.clear()
    assert web.status_code == 200, (
        web.text,
        [
            getattr(route, "path", "")
            for route in app.routes
            if "analytics" in getattr(route, "path", "")
        ],
    )
    assert cli.exit_code == 0, cli.stdout
    assert web.json()["datasets"][0]["key"] == "sales_orders"
    assert '"sales_orders"' in cli.stdout


def test_analytics_tenant_and_private_owner_boundaries(
    session, business, scheduled_owner
):
    orders(session, business)
    foreign = create_tenant(session, "Other analytics company")
    assert query(session, foreign.id, request())["rows"] == []
    assert (
        contributors(session, foreign.id, {**request(), "measure": "order_count"})[
            "total"
        ]
        == 0
    )
    assert export_csv(session, foreign.id, request())["row_count"] == 0
    principal = Principal(scheduled_owner.id)
    saved = change_report(session, business.tenant.id, principal, create_args())
    from reality.services.analytics.proposals import preview

    for operation in (
        lambda: preview(session, foreign.id, principal, "foreign_proposal"),
        lambda: get_report(session, foreign.id, principal, saved["id"]),
        lambda: list_reports(session, foreign.id, principal),
        lambda: change_report(session, foreign.id, principal, create_args()),
    ):
        with pytest.raises(NotFound):
            operation()
    assert len(list_reports(session, business.tenant.id, principal)["records"]) == 1
