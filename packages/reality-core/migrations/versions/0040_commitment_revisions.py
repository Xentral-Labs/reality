"""Let a counterparty state a new date without erasing the old one.

Revision ID: 0040_commitment_revisions
Revises: 0039_early_payment_discount
"""

import sqlalchemy as sa
from alembic import op

revision = "0040_commitment_revisions"
down_revision = "0039_early_payment_discount"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Append-only, and a table rather than a column for one reason: a date a
    # counterparty stated is a received value, and a column would let the second
    # statement overwrite the first. No backfill — no promise has been revised,
    # and none is treated as revised.
    op.create_table(
        "commitment_revision",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False
        ),
        sa.Column(
            "commitment_id",
            sa.String(),
            sa.ForeignKey("commitment.id"),
            nullable=False,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "source_record_id",
            sa.String(),
            sa.ForeignKey("source_record.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_commitment_revision_tenant_id", "commitment_revision", ["tenant_id"]
    )
    op.create_index(
        "ix_commitment_revision_commitment_id",
        "commitment_revision",
        ["commitment_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_commitment_revision_commitment_id", "commitment_revision")
    op.drop_index("ix_commitment_revision_tenant_id", "commitment_revision")
    op.drop_table("commitment_revision")
