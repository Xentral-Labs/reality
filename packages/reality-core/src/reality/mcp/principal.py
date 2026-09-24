"""Transport-neutral authenticated authority for one MCP request."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class MCPPrincipal:
    authentication_kind: Literal["manual", "interactive"]
    credential_id: str
    grant_id: str | None
    user_id: str | None
    tenant_id: str
    client_id: str
    scopes: frozenset[str]
    allowed_tools: frozenset[str]

    def permits(self, tool_name: str) -> bool:
        return "*" in self.allowed_tools or tool_name in self.allowed_tools


_CURRENT_MCP_PRINCIPAL: ContextVar[MCPPrincipal | None] = ContextVar(
    "current_mcp_principal", default=None
)


def current_mcp_principal() -> MCPPrincipal | None:
    """Return server-verified MCP authority during canonical tool dispatch."""
    return _CURRENT_MCP_PRINCIPAL.get()


@contextmanager
def mcp_principal_context(principal: MCPPrincipal) -> Iterator[None]:
    """Propagate MCP actor authority internally without public tool arguments."""
    token = _CURRENT_MCP_PRINCIPAL.set(principal)
    try:
        yield
    finally:
        _CURRENT_MCP_PRINCIPAL.reset(token)
