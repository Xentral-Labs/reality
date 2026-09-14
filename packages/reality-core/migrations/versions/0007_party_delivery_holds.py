"""Add reversible delivery holds for customer parties.

Revision ID: 0007_party_delivery_holds
Revises: 0006_commitment_holds
"""

import sqlalchemy as sa
from alembic import op

revision = "0007_party_delivery_holds"
down_revision = "0006_commitment_holds"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "party_hold",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("party_id", sa.String(), sa.ForeignKey("party.id"), nullable=False),
        sa.Column("hold_type", sa.String(), nullable=False),
        sa.Column("reason_code", sa.String(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by", sa.String(), nullable=False, server_default="human"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("released_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_party_hold_tenant_id", "party_hold", ["tenant_id"])
    op.create_index("ix_party_hold_party_id", "party_hold", ["party_id"])


def downgrade() -> None:
    op.drop_table("party_hold")
