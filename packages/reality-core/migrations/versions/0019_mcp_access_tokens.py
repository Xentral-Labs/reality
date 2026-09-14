"""Add tenant-scoped MCP bearer tokens.

Revision ID: 0019_mcp_access_tokens
Revises: 0018_materialized_projections
"""

import sqlalchemy as sa
from alembic import op

revision = "0019_mcp_access_tokens"
down_revision = "0018_materialized_projections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mcp_access_token",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("token_prefix", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_mcp_access_token_tenant_id", "mcp_access_token", ["tenant_id"])
    op.create_index("ix_mcp_access_token_token_prefix", "mcp_access_token", ["token_prefix"])


def downgrade() -> None:
    op.drop_table("mcp_access_token")
