"""Add tenant integration registry.

Revision ID: 0013_integration_registry
Revises: 0012_business_events
"""

import sqlalchemy as sa
from alembic import op

revision = "0013_integration_registry"
down_revision = "0012_business_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_system",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "code"),
    )
    op.create_index("ix_source_system_tenant_id", "source_system", ["tenant_id"])
    op.create_table(
        "source_capability",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("source_system_id", sa.String(), sa.ForeignKey("source_system.id"), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "source_system_id", "source_type"),
    )
    op.create_index("ix_source_capability_tenant_id", "source_capability", ["tenant_id"])
    op.create_index("ix_source_capability_source_system_id", "source_capability", ["source_system_id"])


def downgrade() -> None:
    op.drop_table("source_capability")
    op.drop_table("source_system")
