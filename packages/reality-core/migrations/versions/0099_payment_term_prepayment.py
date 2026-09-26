"""Add an explicit prepayment policy to payment terms.

Revision ID: 0099_payment_term_prepayment
Revises: 0098_chat_agent_decisions
"""

import sqlalchemy as sa
from alembic import op

revision = "0099_payment_term_prepayment"
down_revision = "0098_chat_agent_decisions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payment_term",
        sa.Column(
            "requires_prepayment",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("payment_term", "requires_prepayment")
