"""What this Reality can do, and what the calling credential may use of it.

Spec 270. An agent connected over MCP sees every tool in the listing whatever its
credential allows, and learns otherwise only when a call is refused. It reads that
refusal as the capability being absent. This module answers the other question: which
business areas exist, what each one holds, and which of it this credential may call.

It classifies nothing. `reality.tool_catalog` already assigns every MCP tool a topic, a
purpose, a description and, where the resource catalog holds one, a German business
label. This reads that and adds the grant state.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.catalogs import runtime_tool_catalog
from reality.db.mcp_authorization import MCPClientGrant
from reality.mcp.principal import MCPPrincipal, current_mcp_principal
from reality.services.core import InvalidOperation

#: Given a tool's name and access class, whether the caller may call it and why not.
GrantState = Callable[[str, str], tuple[bool, str | None]]


def topic_index(session: Session, tenant_id: str) -> dict[str, Any]:
    """Return every capability topic that holds at least one MCP tool."""
    catalog = runtime_tool_catalog()
    access = _access_classes(catalog)
    state = _grant_state(session, tenant_id)
    held: dict[str, dict[str, Any]] = {}
    limited = False
    for entry in _capability_entries(catalog):
        row = held.setdefault(entry["topic"], {"capabilities": 0, "tools": set()})
        row["capabilities"] += 1
        row["tools"].update(entry["mcp"])
        limited = limited or any(
            not state(name, access[name])[0] for name in entry["mcp"]
        )
    return {
        "credential": _credential(limited),
        "topics": [
            {
                "topic": topic["key"],
                "label": topic["label"],
                "capabilities": held[topic["key"]]["capabilities"],
                "tools": len(held[topic["key"]]["tools"]),
            }
            for topic in catalog["topics"]
            if topic["key"] in held
        ],
    }


def topic_capabilities(session: Session, tenant_id: str, topic: str) -> dict[str, Any]:
    """Return one topic's capabilities, their tools and this credential's reach."""
    catalog = runtime_tool_catalog()
    entries = [row for row in _capability_entries(catalog) if row["topic"] == topic]
    if not entries:
        known = sorted({row["topic"] for row in _capability_entries(catalog)})
        raise InvalidOperation(
            f"Unknown capability topic: {topic}. Known topics: {', '.join(known)}."
        )
    access = _access_classes(catalog)
    state = _grant_state(session, tenant_id)
    labels = {row["key"]: row["label"] for row in catalog["topics"]}
    capabilities = []
    limited = False
    for entry in entries:
        tools = []
        for name in entry["mcp"]:
            callable_here, reason = state(name, access[name])
            limited = limited or not callable_here
            tools.append(
                {
                    "name": name,
                    "access": access[name],
                    "callable": callable_here,
                    "reason": reason,
                }
            )
        capabilities.append(
            {
                "capability": entry["title"],
                "label_de": entry.get("labels", {}).get("de") or None,
                "purpose": entry["purpose"],
                "description": entry["description"],
                "tools": tools,
            }
        )
    return {
        "topic": topic,
        "label": labels[topic],
        "credential": _credential(limited),
        "capabilities": capabilities,
    }


def _capability_entries(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in catalog["entries"] if row.get("mcp")]


def _access_classes(catalog: dict[str, Any]) -> dict[str, str]:
    return {tool["name"]: tool["access"] for tool in catalog["mcp_tools"]}


def _credential(limits_tools: bool) -> dict[str, Any]:
    principal = current_mcp_principal()
    return {
        "kind": principal.authentication_kind if principal else "none",
        "limits_tools": limits_tools,
    }


def _grant_state(session: Session, tenant_id: str) -> GrantState:
    """Mirror what `dispatch_mcp_tool` would decide, and say why it decides against.

    An interactive principal cannot answer the why on its own.
    `resolve_interactive_principal` has already intersected the grant's tools with its
    scopes, so everything it excluded looks alike from the principal: simply absent.
    The grant row still holds both halves, so the reason is recoverable from it.

    Manual tokens model no access-class scopes at all — their scope set is
    `reality:read` plus one `reality:tool:<name>` per permission — so the only reason
    that can arise for them is that the token does not name the tool.
    """
    principal = current_mcp_principal()
    if principal is None:
        return lambda name, access: (True, None)
    if principal.authentication_kind == "manual":
        return lambda name, access: (
            (True, None) if principal.permits(name) else (False, "not_in_token")
        )
    grant = _grant_of(session, tenant_id, principal)
    if grant is None:
        return lambda name, access: (
            (True, None) if principal.permits(name) else (False, "not_in_grant")
        )
    from reality.services.mcp_authorization import ACCESS_SCOPE

    named = set(grant.allowed_tools)
    scopes = set(grant.scopes)

    def state(name: str, access: str) -> tuple[bool, str | None]:
        scoped = ACCESS_SCOPE[access] in scopes
        if name in named and scoped:
            return True, None
        # Which reason is the actionable one. `approve_interaction` refuses tools
        # outside the requested scopes, so a whole access class the credential never
        # asked for is absent from the grant for that reason, not by selection:
        # widening the tool list alone would not help, the client must ask for the
        # scope. A tool missing while its class is in scope simply was not selected.
        return False, "not_in_grant" if scoped else "scope_excluded"

    return state


def _grant_of(
    session: Session, tenant_id: str, principal: MCPPrincipal
) -> MCPClientGrant | None:
    if principal.grant_id is None:
        return None
    return session.scalar(
        select(MCPClientGrant).where(
            MCPClientGrant.tenant_id == tenant_id,
            MCPClientGrant.id == principal.grant_id,
        )
    )
