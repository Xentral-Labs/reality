"""Account-security authority for interactive MCP authorization."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now


class MCPClientGrant(Base):
    __tablename__ = "mcp_client_grant"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "id", name="uq_mcp_client_grant_tenant_id"),
        CheckConstraint(
            "jsonb_typeof(allowed_tools) = 'array' AND jsonb_array_length(allowed_tools) > 0",
            name="ck_mcp_client_grant_tools",
        ),
        CheckConstraint(
            "jsonb_typeof(scopes) = 'array' AND jsonb_array_length(scopes) > 0",
            name="ck_mcp_client_grant_scopes",
        ),
        CheckConstraint(
            "length(client_id) BETWEEN 1 AND 2048", name="ck_mcp_client_grant_client_id"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"), index=True)
    client_id: Mapped[str] = mapped_column(String(2048), index=True)
    client_name: Mapped[str] = mapped_column(String(200))
    client_uri: Mapped[str | None] = mapped_column(String(2048), default=None)
    allowed_tools: Mapped[list[str]] = mapped_column(JSONB)
    scopes: Mapped[list[str]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=now, server_default=text("now()")
    )
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    revoked_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), default=None
    )
    revoke_reason: Mapped[str | None] = mapped_column(String(80), default=None)


class MCPAuthorizationInteraction(Base):
    __tablename__ = "mcp_authorization_interaction"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'denied', 'consumed', 'expired')",
            name="ck_mcp_authorization_interaction_status",
        ),
        CheckConstraint(
            "code_challenge_method = 'S256'",
            name="ck_mcp_authorization_interaction_pkce",
        ),
        CheckConstraint(
            "jsonb_typeof(requested_scopes) = 'array'",
            name="ck_mcp_authorization_interaction_scopes",
        ),
        CheckConstraint(
            "(status = 'pending' AND grant_id IS NULL AND authorization_code_hash IS NULL AND decided_at IS NULL AND consumed_at IS NULL) OR "
            "(status = 'approved' AND tenant_id IS NOT NULL AND grant_id IS NOT NULL AND authorization_code_hash IS NOT NULL AND decided_at IS NOT NULL AND consumed_at IS NULL) OR "
            "(status = 'denied' AND grant_id IS NULL AND authorization_code_hash IS NULL AND decided_at IS NOT NULL AND consumed_at IS NULL) OR "
            "(status = 'consumed' AND tenant_id IS NOT NULL AND grant_id IS NOT NULL AND authorization_code_hash IS NOT NULL AND decided_at IS NOT NULL AND consumed_at IS NOT NULL) OR "
            "(status = 'expired' AND consumed_at IS NULL)",
            name="ck_mcp_authorization_interaction_lifecycle",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "grant_id"],
            ["mcp_client_grant.tenant_id", "mcp_client_grant.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    client_id: Mapped[str] = mapped_column(String(2048), index=True)
    client_metadata: Mapped[dict] = mapped_column(JSONB)
    redirect_uri: Mapped[str] = mapped_column(String(2048))
    resource: Mapped[str] = mapped_column(String(2048))
    requested_scopes: Mapped[list[str]] = mapped_column(JSONB)
    code_challenge: Mapped[str] = mapped_column(String(128))
    code_challenge_method: Mapped[str] = mapped_column(
        String(8), default="S256", server_default="S256"
    )
    client_state: Mapped[str] = mapped_column(Text, default="")
    user_id: Mapped[str | None] = mapped_column(ForeignKey("app_user.id"), default=None)
    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("tenant.id"), default=None, index=True
    )
    grant_id: Mapped[str | None] = mapped_column(String, default=None)
    authorization_code_hash: Mapped[str | None] = mapped_column(
        String(64), unique=True, default=None
    )
    status: Mapped[str] = mapped_column(
        String(16), default="pending", server_default="pending", index=True
    )
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=now, server_default=text("now()")
    )
    decided_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    consumed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class MCPUserCredential(Base):
    __tablename__ = "mcp_user_credential"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "id", name="uq_mcp_user_credential_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "grant_id"],
            ["mcp_client_grant.tenant_id", "mcp_client_grant.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "replaced_by_id"],
            ["mcp_user_credential.tenant_id", "mcp_user_credential.id"],
        ),
        CheckConstraint("generation > 0", name="ck_mcp_user_credential_generation"),
        CheckConstraint(
            "(refresh_token_hash IS NULL AND refresh_expires_at IS NULL) OR "
            "(refresh_token_hash IS NOT NULL AND refresh_expires_at IS NOT NULL)",
            name="ck_mcp_user_credential_refresh_pair",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    grant_id: Mapped[str] = mapped_column(String)
    access_token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    access_token_prefix: Mapped[str] = mapped_column(String(24), index=True)
    access_expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    refresh_token_hash: Mapped[str | None] = mapped_column(
        String(64), unique=True, default=None
    )
    refresh_expires_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime, default=None
    )
    generation: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=now, server_default=text("now()")
    )
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    rotated_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    replaced_by_id: Mapped[str | None] = mapped_column(String, default=None)
