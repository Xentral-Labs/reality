"""Add tenant-scoped AI provider settings.

Revision ID: 0017_ai_settings
Revises: 0016_inventory_tracking_dimensions
"""

import sqlalchemy as sa
from alembic import op

revision = "0017_ai_settings"
down_revision = "0016_inventory_tracking_dimensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_settings",
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), primary_key=True),
        sa.Column("provider", sa.String(), nullable=False, server_default="local"),
        sa.Column("model", sa.String(), nullable=False, server_default=""),
        sa.Column(
            "base_url",
            sa.String(),
            nullable=False,
            server_default="https://api.openai.com/v1",
        ),
        sa.Column("encrypted_api_key", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ai_settings")
