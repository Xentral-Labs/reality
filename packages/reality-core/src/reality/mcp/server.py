from __future__ import annotations

import inspect
import json
from typing import Annotated, Any

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.context import Context
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, ToolAnnotations
from pydantic import WithJsonSchema

from reality.db.core import Session
from reality.mcp.auth import DatabaseTokenVerifier
from reality.mcp.catalog import (
    MCPToolDefinition,
    dispatch_mcp_tool,
    schema_argument_names,
    schema_choices,
    tool_definitions,
)
from reality.mcp.principal import MCPPrincipal
from reality.services import interaction_recorder as interactions
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


class RealityServer(MCPServer):
    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        context: Context | None = None,
    ) -> CallToolResult:
        try:
            return await super().call_tool(name, arguments, context)
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
    union_branches = definition.input_schema.get("oneOf", ())

    def invoke(**arguments: Any) -> Any:
        access_token = get_access_token()
        if access_token is None or not access_token.subject:
            raise RuntimeError("Authenticated tenant context is required.")
        principal = (getattr(access_token, "claims", None) or {}).get(
            "reality_principal"
        )
        if not isinstance(principal, MCPPrincipal):
            scopes = set(access_token.scopes)
            client_id = getattr(access_token, "client_id", None) or "manual-token"
            allowed = frozenset(
                {"*"}
                if "reality:tool:*" in scopes
                else {
                    scope.removeprefix("reality:tool:")
                    for scope in scopes
                    if scope.startswith("reality:tool:")
                }
            )
            principal = MCPPrincipal(
                "manual",
                client_id,
                None,
                None,
                access_token.subject,
                client_id,
                frozenset(scopes),
                allowed,
            )
        if not principal.permits(definition.name):
            raise ToolError(f"MCP token does not allow tool: {definition.name}")
        # The signature gives every optional property without a declared default a
        # `None`, so a caller who leaves a filter out sends `None` for it. For a read
        # that means "no filter", which is what the service's own default already
        # says; passing `None` on made services that expect "" fail (`shipments_list`,
        # `finance_opening_context`). Proposals keep an explicit `None`, which can
        # mean "clear this field".
        if union_branches or definition.access == "read":
            arguments = {
                name: value for name, value in arguments.items() if value is not None
            }
        # Spec 266: one engine-room interaction per MCP tool call, attributed to the
        # person an interactive grant names, or else to the manual token.
        with (
            interactions.observe(
                principal.tenant_id,
                "mcp",
                definition.name,
                actor_user_id=principal.user_id,
                mcp_token_id=principal.credential_id
                if principal.authentication_kind == "manual"
                else None,
                arguments=schema_argument_names(definition.name, arguments),
                choices=schema_choices(definition.name, arguments),
            ),
            Session() as session,
        ):
            result = dispatch_mcp_tool(session, principal, definition.name, arguments)
            interactions.note_result(result)
            return result

    invoke.__name__ = definition.name
    invoke.__doc__ = definition.description
    signature_schema = definition.input_schema
    if union_branches:
        properties = {
            **definition.input_schema.get("properties", {}),
            **{
                name: schema
                for branch in union_branches
                for name, schema in branch.get("properties", {}).items()
            },
        }
        required_sets = [set(branch.get("required", ())) for branch in union_branches]
        required = set(definition.input_schema.get("required", ()))
        if required_sets:
            required.update(set.intersection(*required_sets))
        signature_schema = {"properties": properties}
    else:
        required = set(definition.input_schema.get("required", ()))
    parameters = []
    for name, schema in signature_schema.get("properties", {}).items():
        default = (
            inspect.Parameter.empty
            if name in required
            else None
            if union_branches
            else schema.get("default")
        )
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
    authorization_issuer: str | None = None,
) -> MCPServer:
    endpoint_url = (public_url or f"http://{host}:{port}/").rstrip("/") + "/"
    server = RealityServer(
        "Reality",
        instructions=(
            "Inspect operational reality through shared application services. "
            "Mutations are proposals and require a separate authorized decision. "
            "Call capability_catalog first: it names the business areas this company "
            "covers and marks which tools this credential may actually use, so a "
            "capability you are not granted is never mistaken for one that is absent."
        ),
        token_verifier=token_verifier or DatabaseTokenVerifier(resource=endpoint_url),
        auth=AuthSettings(
            issuer_url=authorization_issuer or "http://127.0.0.1:8000",
            resource_server_url=endpoint_url,
            required_scopes=["reality:read"],
            # Manual tokens intentionally have no RFC 8707 audience. Interactive
            # credentials are resource-bound by Reality's verifier instead.
            validate_token_resource=False,
        ),
    )
    for definition in tool_definitions():
        server.add_tool(
            _handler(definition),
            name=definition.name,
            annotations=_annotations(definition),
        )
        if "oneOf" in definition.input_schema:
            registered = server._tool_manager.get_tool(definition.name)
            if registered is None:  # pragma: no cover - registration invariant
                raise RuntimeError(f"MCP tool registration failed: {definition.name}")
            registered.parameters = definition.input_schema
    return server


def build_remote_server(
    public_url: str | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8001,
    authorization_issuer: str | None = None,
) -> MCPServer:
    """Build the authenticated HTTP MCP resource server."""
    # Spec 266: the serving process records interactions off the call path.
    interactions.start_background_writer()
    return build_server(
        host=host,
        port=port,
        public_url=public_url,
        authorization_issuer=authorization_issuer,
    )
