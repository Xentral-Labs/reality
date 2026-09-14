"""Rename the materialized issue projection to operational exceptions.

Revision ID: 0023_exception_terminology
Revises: 0022_mcp_tool_permissions
"""

from alembic import op

revision = "0023_exception_terminology"
down_revision = "0022_mcp_tool_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE projection_row SET projection_name = 'exceptions' "
        "WHERE projection_name = 'issues'"
    )
    op.execute(
        "UPDATE projection_checkpoint SET projection_name = 'exceptions' "
        "WHERE projection_name = 'issues'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE projection_row SET projection_name = 'issues' "
        "WHERE projection_name = 'exceptions'"
    )
    op.execute(
        "UPDATE projection_checkpoint SET projection_name = 'issues' "
        "WHERE projection_name = 'exceptions'"
    )
