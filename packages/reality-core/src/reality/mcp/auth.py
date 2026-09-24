from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass

from mcp.server.auth.provider import AccessToken
from sqlalchemy import select

from reality.db.core import MCPAccessToken, Session, now, uid
from reality.mcp.catalog import validate_tool_permissions
from reality.services.tenant_policy import (
    PlaygroundOperationDenied,
    require_business_operation,
)

TOKEN_PREFIX = "ros_mcp_"


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_mcp_access_token(
    session,
    tenant_id: str,
    name: str,
    allowed_tools: list[str] | tuple[str, ...] = ("*",),
    *,
    issued_by_user_id: str | None = None,
) -> tuple[MCPAccessToken, str]:
    require_business_operation(session, tenant_id, "mcp_token_create")
    permissions = validate_tool_permissions(allowed_tools)
    clear_token = TOKEN_PREFIX + secrets.token_urlsafe(32)
    record = MCPAccessToken(
        id=uid("mcp"),
        tenant_id=tenant_id,
        name=name.strip() or "MCP client",
        token_prefix=clear_token[:16],
        token_hash=_token_hash(clear_token),
        allowed_tools=json.dumps(permissions),
        created_by_user_id=issued_by_user_id,
    )
    session.add(record)
    session.commit()
    return record, clear_token


def active_mcp_access_tokens(session, tenant_id: str) -> list[MCPAccessToken]:
    return list(
        session.scalars(
            select(MCPAccessToken)
            .where(
                MCPAccessToken.tenant_id == tenant_id,
                MCPAccessToken.revoked_at.is_(None),
            )
            .order_by(MCPAccessToken.created_at.desc())
        )
    )


def revoke_mcp_access_token(session, tenant_id: str, token_id: str) -> None:
    token = session.scalar(
        select(MCPAccessToken).where(
            MCPAccessToken.id == token_id,
            MCPAccessToken.tenant_id == tenant_id,
            MCPAccessToken.revoked_at.is_(None),
        )
    )
    if token is None:
        raise ValueError("Active MCP token not found.")
    token.revoked_at = now()
    session.commit()


@dataclass
class DatabaseTokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        digest = _token_hash(token)
        with Session() as session:
            record = session.scalar(
                select(MCPAccessToken).where(
                    MCPAccessToken.token_hash == digest,
                    MCPAccessToken.revoked_at.is_(None),
                )
            )
            if record is None:
                return None
            try:
                require_business_operation(session, record.tenant_id, "mcp_token_use")
            except PlaygroundOperationDenied:
                return None
            record.last_used_at = now()
            session.commit()
            allowed_tools = validate_tool_permissions(
                json.loads(record.allowed_tools or "[]")
            )
            tool_scopes = (
                ["reality:tool:*"]
                if "*" in allowed_tools
                else [f"reality:tool:{name}" for name in allowed_tools]
            )
            return AccessToken(
                token=token,
                client_id=record.id,
                scopes=["reality:read", *tool_scopes],
                subject=record.tenant_id,
            )
