"""Add generic tenant-scoped materialized projection storage.

Revision ID: 0018_materialized_projections
Revises: 0017_ai_settings
"""

import sqlalchemy as sa
from alembic import op

revision = "0018_materialized_projections"
down_revision = "0017_ai_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projection_row",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("projection_name", sa.String(), nullable=False),
        sa.Column("projection_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("record_key", sa.String(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("source_event_sequence", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "projection_name", "record_key"),
    )
    op.create_index("ix_projection_row_tenant_id", "projection_row", ["tenant_id"])
    op.create_index("ix_projection_row_projection_name", "projection_row", ["projection_name"])
    op.create_index("ix_projection_row_record_key", "projection_row", ["record_key"])
    op.create_table(
        "projection_checkpoint",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("projection_name", sa.String(), nullable=False),
        sa.Column("projection_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_event_sequence", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="ready"),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "projection_name"),
    )
    op.create_index("ix_projection_checkpoint_tenant_id", "projection_checkpoint", ["tenant_id"])
    op.create_index("ix_projection_checkpoint_projection_name", "projection_checkpoint", ["projection_name"])


def downgrade() -> None:
    op.drop_table("projection_checkpoint")
    op.drop_table("projection_row")
