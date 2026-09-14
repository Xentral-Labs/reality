"""Add explicit per-token MCP tool permissions.

Revision ID: 0022_mcp_tool_permissions
Revises: 0021_source_artifacts
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "0022_mcp_tool_permissions"
down_revision = "0021_source_artifacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("mcp_access_token") as batch:
        batch.add_column(
            sa.Column(
                "allowed_tools",
                sa.Text(),
                nullable=False,
                server_default=json.dumps(["*"]),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("mcp_access_token") as batch:
        batch.drop_column("allowed_tools")
