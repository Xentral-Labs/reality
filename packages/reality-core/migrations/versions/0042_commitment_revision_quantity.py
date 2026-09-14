"""Let one statement restate a promise's quantity as well as its date.

Revision ID: 0042_commitment_revision_quantity
Revises: 0041_playground_main_merge
"""

import sqlalchemy as sa
from alembic import op

revision = "0042_commitment_revision_quantity"
down_revision = "0041_playground_main_merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # One column rather than a second table, because "eighty pieces, two weeks
    # later" is one sentence. Two tables would give it two timestamps that can
    # disagree about when the supplier said it.
    #
    # Both figures are nullable and a statement must carry at least one; the
    # service refuses one that restates nothing. No backfill: every revision
    # recorded so far states a date and no quantity, which is exactly what it
    # meant.
    op.add_column(
        "commitment_revision",
        sa.Column("quantity", sa.Numeric(18, 4), nullable=True),
    )
    op.alter_column(
        "commitment_revision", "due_at", existing_type=sa.DateTime(timezone=True), nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "commitment_revision", "due_at", existing_type=sa.DateTime(timezone=True), nullable=False
    )
    op.drop_column("commitment_revision", "quantity")
