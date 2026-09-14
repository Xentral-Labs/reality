"""Record who decided a change proposal and when.

The audit record kept who requested a change but discarded who approved or
rejected it, which is the one attribution an approval boundary exists to keep.
Both columns are nullable: decisions settled before this migration cannot be
reconstructed, and a decision taken without a signed-in principal has no user.

Revision ID: 0034_decision_attribution
Revises: 0033_interpretation_outcomes
"""

import sqlalchemy as sa
from alembic import op

revision = "0034_decision_attribution"
down_revision = "0033_interpretation_outcomes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "action", sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "action",
        sa.Column(
            "decided_by_user_id",
            sa.String(),
            sa.ForeignKey("app_user.id"),
            nullable=True,
        ),
    )
    op.create_index("ix_action_decided_by_user_id", "action", ["decided_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_action_decided_by_user_id", table_name="action")
    op.drop_column("action", "decided_by_user_id")
    op.drop_column("action", "decided_at")
