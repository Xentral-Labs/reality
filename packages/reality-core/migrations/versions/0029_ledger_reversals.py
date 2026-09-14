"""Add auditable Ledger posting-group reversals.

Revision ID: 0029_ledger_reversals
Revises: 0028_movement_corrections
"""

import sqlalchemy as sa
from alembic import op

revision = "0029_ledger_reversals"
down_revision = "0028_movement_corrections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ledger_reversal",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("original_posting_group_id", sa.String(), nullable=False, unique=True),
        sa.Column("reversing_posting_group_id", sa.String(), nullable=False, unique=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_context", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("request_fingerprint", sa.String(), nullable=False),
        sa.UniqueConstraint("tenant_id", "request_fingerprint"),
        sa.CheckConstraint(
            "original_posting_group_id <> reversing_posting_group_id",
            name="ck_ledger_reversal_groups_distinct",
        ),
    )
    op.create_index("ix_ledger_reversal_tenant_id", "ledger_reversal", ["tenant_id"])
    op.create_index(
        "ix_ledger_reversal_original_posting_group_id",
        "ledger_reversal",
        ["original_posting_group_id"],
    )
    op.create_index(
        "ix_ledger_reversal_reversing_posting_group_id",
        "ledger_reversal",
        ["reversing_posting_group_id"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    count = connection.scalar(sa.text("SELECT COUNT(*) FROM ledger_reversal"))
    if count:
        raise RuntimeError("Cannot remove Ledger reversal evidence after reversals exist.")
    op.drop_table("ledger_reversal")
