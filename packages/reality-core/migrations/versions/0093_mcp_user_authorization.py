"""Add interactive MCP user authorization authority.

Revision ID: 0093_mcp_user_authorization
Revises: 0092_party_email_addresses
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0093_mcp_user_authorization"
down_revision = "0092_party_email_addresses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mcp_client_grant",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("client_id", sa.String(2048), nullable=False),
        sa.Column("client_name", sa.String(200), nullable=False),
        sa.Column("client_uri", sa.String(2048)),
        sa.Column("allowed_tools", postgresql.JSONB(), nullable=False),
        sa.Column("scopes", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_by_user_id", sa.String()),
        sa.Column("revoke_reason", sa.String(80)),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_mcp_client_grant_tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"]),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["app_user.id"]),
        sa.CheckConstraint(
            "jsonb_typeof(allowed_tools) = 'array' AND jsonb_array_length(allowed_tools) > 0",
            name="ck_mcp_client_grant_tools",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(scopes) = 'array' AND jsonb_array_length(scopes) > 0",
            name="ck_mcp_client_grant_scopes",
        ),
        sa.CheckConstraint(
            "length(client_id) BETWEEN 1 AND 2048", name="ck_mcp_client_grant_client_id"
        ),
    )
    op.create_index("ix_mcp_client_grant_tenant_id", "mcp_client_grant", ["tenant_id"])
    op.create_index("ix_mcp_client_grant_user_id", "mcp_client_grant", ["user_id"])
    op.create_index("ix_mcp_client_grant_client_id", "mcp_client_grant", ["client_id"])

    op.create_table(
        "mcp_authorization_interaction",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("client_id", sa.String(2048), nullable=False),
        sa.Column("client_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("redirect_uri", sa.String(2048), nullable=False),
        sa.Column("resource", sa.String(2048), nullable=False),
        sa.Column("requested_scopes", postgresql.JSONB(), nullable=False),
        sa.Column("code_challenge", sa.String(128), nullable=False),
        sa.Column(
            "code_challenge_method", sa.String(8), server_default="S256", nullable=False
        ),
        sa.Column("client_state", sa.Text(), server_default="", nullable=False),
        sa.Column("user_id", sa.String()),
        sa.Column("tenant_id", sa.String()),
        sa.Column("grant_id", sa.String()),
        sa.Column("authorization_code_hash", sa.String(64), unique=True),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "grant_id"],
            ["mcp_client_grant.tenant_id", "mcp_client_grant.id"],
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'denied', 'consumed', 'expired')",
            name="ck_mcp_authorization_interaction_status",
        ),
        sa.CheckConstraint(
            "code_challenge_method = 'S256'",
            name="ck_mcp_authorization_interaction_pkce",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(requested_scopes) = 'array'",
            name="ck_mcp_authorization_interaction_scopes",
        ),
        sa.CheckConstraint(
            "(status = 'pending' AND grant_id IS NULL AND authorization_code_hash IS NULL AND decided_at IS NULL AND consumed_at IS NULL) OR "
            "(status = 'approved' AND tenant_id IS NOT NULL AND grant_id IS NOT NULL AND authorization_code_hash IS NOT NULL AND decided_at IS NOT NULL AND consumed_at IS NULL) OR "
            "(status = 'denied' AND grant_id IS NULL AND authorization_code_hash IS NULL AND decided_at IS NOT NULL AND consumed_at IS NULL) OR "
            "(status = 'consumed' AND tenant_id IS NOT NULL AND grant_id IS NOT NULL AND authorization_code_hash IS NOT NULL AND decided_at IS NOT NULL AND consumed_at IS NOT NULL) OR "
            "(status = 'expired' AND consumed_at IS NULL)",
            name="ck_mcp_authorization_interaction_lifecycle",
        ),
    )
    op.create_index(
        "ix_mcp_authorization_interaction_client_id",
        "mcp_authorization_interaction",
        ["client_id"],
    )
    op.create_index(
        "ix_mcp_authorization_interaction_tenant_id",
        "mcp_authorization_interaction",
        ["tenant_id"],
    )
    op.create_index(
        "ix_mcp_authorization_interaction_status",
        "mcp_authorization_interaction",
        ["status"],
    )

    op.create_table(
        "mcp_user_credential",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("grant_id", sa.String(), nullable=False),
        sa.Column("access_token_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("access_token_prefix", sa.String(24), nullable=False),
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), unique=True),
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True)),
        sa.Column("generation", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("rotated_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("replaced_by_id", sa.String()),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_mcp_user_credential_tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "grant_id"],
            ["mcp_client_grant.tenant_id", "mcp_client_grant.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "replaced_by_id"],
            ["mcp_user_credential.tenant_id", "mcp_user_credential.id"],
        ),
        sa.CheckConstraint("generation > 0", name="ck_mcp_user_credential_generation"),
        sa.CheckConstraint(
            "(refresh_token_hash IS NULL AND refresh_expires_at IS NULL) OR "
            "(refresh_token_hash IS NOT NULL AND refresh_expires_at IS NOT NULL)",
            name="ck_mcp_user_credential_refresh_pair",
        ),
    )
    op.create_index(
        "ix_mcp_user_credential_tenant_id", "mcp_user_credential", ["tenant_id"]
    )
    op.create_index(
        "ix_mcp_user_credential_grant_id",
        "mcp_user_credential",
        ["tenant_id", "grant_id"],
    )
    op.create_index(
        "ix_mcp_user_credential_access_token_prefix",
        "mcp_user_credential",
        ["access_token_prefix"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    for table in (
        "mcp_user_credential",
        "mcp_authorization_interaction",
        "mcp_client_grant",
    ):
        if connection.execute(
            sa.text(f"SELECT EXISTS (SELECT 1 FROM {table} LIMIT 1)")
        ).scalar():
            raise RuntimeError(
                "Refusing to remove populated MCP user authorization tables."
            )
    op.drop_table("mcp_user_credential")
    op.drop_table("mcp_authorization_interaction")
    op.drop_table("mcp_client_grant")
