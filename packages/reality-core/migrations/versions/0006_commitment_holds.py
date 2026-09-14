"""Add reversible execution holds for commitments.

Revision ID: 0006_commitment_holds
Revises: 0005_operational_fields
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_commitment_holds"
down_revision = "0005_operational_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commitment_hold",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "commitment_id", sa.String(), sa.ForeignKey("commitment.id"), nullable=False
        ),
        sa.Column("reason_code", sa.String(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by", sa.String(), nullable=False, server_default="human"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("released_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_commitment_hold_tenant_id", "commitment_hold", ["tenant_id"])
    op.create_index(
        "ix_commitment_hold_commitment_id", "commitment_hold", ["commitment_id"]
    )


def downgrade() -> None:
    op.drop_table("commitment_hold")
