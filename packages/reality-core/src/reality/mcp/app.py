from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse

from reality.db.core import Session
from reality.mcp.catalog import MCP_TOOL_CATALOG, MCP_TOOL_NAMES
from reality.mcp.config import MCPRuntimeSettings
from reality.mcp.server import build_remote_server


def create_mcp_app(
    *,
    settings: MCPRuntimeSettings | None = None,
    session_factory: Callable = Session,
) -> Starlette:
    """Create the independently hosted authenticated HTTP MCP application."""

    runtime_settings = settings or MCPRuntimeSettings.from_environ()
    server = build_remote_server(
        runtime_settings.public_url,
        host=runtime_settings.bind_host,
        port=runtime_settings.bind_port,
    )

    @server.custom_route("/healthz", methods=["GET"], include_in_schema=False)
    async def healthcheck(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    @server.custom_route("/readyz", methods=["GET"], include_in_schema=False)
    async def readiness(_request: Request) -> JSONResponse:
        try:
            if len(MCP_TOOL_NAMES) != len(MCP_TOOL_CATALOG):
                raise RuntimeError("Invalid MCP tool registry")
            with session_factory() as session:
                session.execute(text("SELECT 1"))
        except (RuntimeError, SQLAlchemyError):
            return JSONResponse({"status": "not_ready"}, status_code=503)
        return JSONResponse({"status": "ready"})

    return server.streamable_http_app()


from reality import telemetry as _telemetry


def _mcp_engine():
    from reality.db.core import engine

    return engine


_telemetry.configure("reality-mcp")
app = create_mcp_app()
_telemetry.instrument_httpx()
_telemetry.instrument_engine(_mcp_engine())
