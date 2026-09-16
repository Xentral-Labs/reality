from __future__ import annotations

import inspect
import json
from collections.abc import Sequence
from typing import Annotated, Any
from urllib.parse import urlparse

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ContentBlock, ToolAnnotations
from pydantic import WithJsonSchema

from reality.db.core import Session
from reality.mcp.auth import DatabaseTokenVerifier
from reality.mcp.catalog import MCPToolDefinition, dispatch_tool, tool_definitions
from reality.services.core import (
    Conflict,
    InterpretationNeedsReview,
    InvalidOperation,
    NotFound,
    RealityError,
)

ERROR_CODES: tuple[tuple[type[RealityError], str], ...] = (
    (NotFound, "not_found"),
    (Conflict, "conflict"),
    (InterpretationNeedsReview, "needs_review"),
    (InvalidOperation, "invalid_operation"),
    (RealityError, "reality_error"),
)


def error_code(error: RealityError) -> str:
    return next(code for kind, code in ERROR_CODES if isinstance(error, kind))


def tool_error_payload(tool_name: str, error: RealityError) -> dict[str, str]:
    return {"code": error_code(error), "message": str(error), "tool": tool_name}


class RealityServer(FastMCP):
    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> Sequence[ContentBlock] | dict[str, Any]:
        try:
            return await super().call_tool(name, arguments)
        except ToolError as error:
            cause = error.__cause__
            if isinstance(cause, RealityError):
                raise ToolError(json.dumps(tool_error_payload(name, cause))) from cause
            raise


def _annotation(schema: dict[str, Any]) -> Any:
    schema_type = schema.get("type")
    if isinstance(schema_type, list) and "null" in schema_type:
        concrete = next(item for item in schema_type if item != "null")
        return _annotation({"type": concrete}) | None
    primitive = {"string": str, "boolean": bool, "integer": int, "number": float}
    if schema_type in primitive:
        return primitive[schema_type]
    return Annotated[Any, WithJsonSchema(_inline_refs(schema, schema.get("$defs", {})))]


def _inline_refs(schema: Any, defs: dict[str, Any], depth: int = 0) -> Any:
    if depth > 32:
        return {}
    if isinstance(schema, dict):
        ref = schema.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            return _inline_refs(defs.get(ref.split("/")[-1], {}), defs, depth + 1)
        return {
            key: _inline_refs(value, defs, depth + 1)
            for key, value in schema.items()
            if key != "$defs"
        }
    if isinstance(schema, list):
        return [_inline_refs(item, defs, depth + 1) for item in schema]
    return schema


def _handler(definition: MCPToolDefinition):
    def invoke(**arguments: Any) -> Any:
        access_token = get_access_token()
        if access_token is None or not access_token.subject:
            raise RuntimeError("Authenticated tenant context is required.")
        scopes = set(access_token.scopes)
        if (
            "reality:tool:*" not in scopes
            and f"reality:tool:{definition.name}" not in scopes
        ):
            raise PermissionError(f"MCP token does not allow tool: {definition.name}")
        with Session() as session:
            return dispatch_tool(
                session, access_token.subject, definition.name, arguments
            )

    invoke.__name__ = definition.name
    invoke.__doc__ = definition.description
    required = set(definition.input_schema.get("required", ()))
    parameters = []
    for name, schema in definition.input_schema.get("properties", {}).items():
        default = inspect.Parameter.empty if name in required else schema.get("default")
        parameters.append(
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                default=default,
                annotation=_annotation(
                    _inline_refs(schema, definition.input_schema.get("$defs", {}))
                ),
            )
        )
    invoke.__signature__ = inspect.Signature(parameters)  # type: ignore[attr-defined]
    return invoke


def _annotations(definition: MCPToolDefinition) -> ToolAnnotations:
    return ToolAnnotations(
        title=definition.label,
        readOnlyHint=definition.access == "read",
        destructiveHint=definition.access == "confirm",
    )


def build_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8001,
    token_verifier: DatabaseTokenVerifier | None = None,
    public_url: str | None = None,
) -> FastMCP:
    endpoint_url = (public_url or f"http://{host}:{port}/").rstrip("/") + "/"
    parsed_url = urlparse(endpoint_url)
    server = RealityServer(
        "Reality",
        instructions=(
            "Inspect operational reality through shared application services. "
            "Mutations are proposals and require separate human approval."
        ),
        host=host,
        port=port,
        stateless_http=True,
        json_response=True,
        streamable_http_path="/",
        token_verifier=token_verifier or DatabaseTokenVerifier(),
        auth=AuthSettings(
            issuer_url=endpoint_url,
            resource_server_url=endpoint_url,
            required_scopes=["reality:read"],
        ),
        transport_security=TransportSecuritySettings(
            allowed_hosts=[parsed_url.netloc],
            allowed_origins=[f"{parsed_url.scheme}://{parsed_url.netloc}"],
        ),
    )
    for definition in tool_definitions():
        server.add_tool(
            _handler(definition),
            name=definition.name,
            annotations=_annotations(definition),
        )
    return server


def build_remote_server(
    public_url: str | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8001,
) -> FastMCP:
    """Build the authenticated HTTP MCP resource server."""
    return build_server(host=host, port=port, public_url=public_url)
