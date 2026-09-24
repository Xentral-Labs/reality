import json

import pytest
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from mcp.server.mcpserver.exceptions import ToolError

from reality.mcp import server as mcp_module
from reality.services.core import (
    Conflict,
    InterpretationNeedsReview,
    InvalidOperation,
    NotFound,
    RealityError,
    create_tenant,
)


def _authenticated(tenant_id: str, scopes: list[str] | None = None):
    access = AccessToken(
        token="test",
        client_id="mcp_test",
        scopes=scopes or ["reality:read", "reality:tool:*"],
        subject=tenant_id,
    )
    return auth_context_var.set(AuthenticatedUser(access))


def test_error_codes_follow_the_service_error_hierarchy():
    assert mcp_module.error_code(NotFound("missing")) == "not_found"
    assert mcp_module.error_code(Conflict("stale")) == "conflict"
    assert mcp_module.error_code(InvalidOperation("bad")) == "invalid_operation"
    assert mcp_module.error_code(InterpretationNeedsReview("unclear")) == "needs_review"
    assert mcp_module.error_code(RealityError("other")) == "reality_error"


@pytest.mark.anyio
async def test_service_errors_reach_the_client_as_code_and_message(session):
    tenant = create_tenant(session, "Error codes")
    session.commit()
    server = mcp_module.build_server()
    context = _authenticated(tenant.id)
    try:
        with pytest.raises(ToolError) as refused:
            await server.call_tool("order_explain", {"order_reference": "SO-NOT-THERE"})
        payload = json.loads(str(refused.value))
        assert payload["code"] == "not_found"
        assert payload["tool"] == "order_explain"
        assert payload["message"]
        assert "Error executing tool" not in payload["message"]
        with pytest.raises(ToolError) as invalid:
            await server.call_tool(
                "business_records_discover", {"family": "document", "limit": 0}
            )
        assert json.loads(str(invalid.value))["code"] == "invalid_operation"
    finally:
        auth_context_var.reset(context)


@pytest.mark.anyio
async def test_other_failures_keep_their_text(session):
    tenant = create_tenant(session, "Error text")
    session.commit()
    server = mcp_module.build_server()
    context = _authenticated(tenant.id, ["reality:read", "reality:tool:inventory_read"])
    try:
        with pytest.raises(ToolError) as forbidden:
            await server.call_tool("business_records_discover", {"family": "document"})
        text = str(forbidden.value)
        assert text.startswith("Error executing tool business_records_discover")
        with pytest.raises(ValueError):
            json.loads(text)
    finally:
        auth_context_var.reset(context)
