"""An MCP read tool called without its optional arguments behaves like its default.

The MCP server builds each tool's signature from the input schema, and an optional
property without a declared default arrives as `None` when the caller leaves it out.
`shipments_list` (spec 173 FR-017/FR-024) and `finance_opening_context` (spec 267
FR-014) then called `.strip()` on `None` and failed with an unexpected error instead
of reading. A business refusal is fine; a crash is not.
"""

from __future__ import annotations

import pytest
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from pydantic import ValidationError

from reality.mcp import server as mcp_module
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services.core import RealityError


def _read_tools_without_required_arguments() -> list[str]:
    return sorted(
        name
        for name, definition in MCP_TOOL_REGISTRY.items()
        if definition.access == "read" and not definition.input_schema.get("required")
    )


async def _call(session, monkeypatch, tenant_id: str, tool: str, arguments: dict):
    monkeypatch.setattr(mcp_module, "Session", lambda: session)
    access = AccessToken(
        token="test",
        client_id="optional-arguments",
        scopes=["reality:read", "reality:tool:*"],
        subject=tenant_id,
    )
    context = auth_context_var.set(AuthenticatedUser(access))
    try:
        return await mcp_module.build_server().call_tool(tool, arguments)
    finally:
        auth_context_var.reset(context)


@pytest.mark.anyio
async def test_every_read_tool_accepts_its_optional_arguments_left_out(
    session, business, monkeypatch
):
    tools = _read_tools_without_required_arguments()
    # Positive control: the sweep covers the registry, including both tools that failed.
    assert len(tools) >= 30
    assert {"shipments_list", "finance_opening_context"} <= set(tools)
    crashed = []
    for tool in tools:
        nested = session.begin_nested()
        try:
            await _call(session, monkeypatch, business.tenant.id, tool, {})
        except Exception as error:  # noqa: BLE001 - classified below
            # A business refusal or a rejected argument set is an answer, not a crash.
            if not isinstance(error.__cause__, RealityError | ValidationError):
                crashed.append(f"{tool}: {type(error.__cause__ or error).__name__}")
        finally:
            if nested.is_active:
                nested.rollback()
    assert crashed == []


@pytest.mark.anyio
async def test_shipments_list_without_filters_reads_the_register(
    session, business, monkeypatch
):
    result = await _call(session, monkeypatch, business.tenant.id, "shipments_list", {})
    assert result
