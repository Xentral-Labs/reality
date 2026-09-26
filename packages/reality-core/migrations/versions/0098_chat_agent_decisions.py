"""Retain Chat-agent decision attribution.

Revision ID: 0098_chat_agent_decisions
Revises: 0097_chat_answer_basis
"""

import sqlalchemy as sa
from alembic import op

revision = "0098_chat_agent_decisions"
down_revision = "0097_chat_answer_basis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "action", sa.Column("decided_via_channel", sa.String(length=16), nullable=True)
    )
    op.create_check_constraint(
        "ck_action_decided_via_channel",
        "action",
        "decided_via_channel IS NULL OR decided_via_channel = 'chat'",
    )


def downgrade() -> None:
    op.drop_constraint("ck_action_decided_via_channel", "action", type_="check")
    op.drop_column("action", "decided_via_channel")
