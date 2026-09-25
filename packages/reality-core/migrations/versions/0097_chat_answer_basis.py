"""Persist bounded support for each assistant reply (spec 272).

Revision ID: 0097_chat_answer_basis
Revises: 0096_engine_room_interaction
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0097_chat_answer_basis"
down_revision = "0096_engine_room_interaction"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_message",
        sa.Column(
            "answer_basis", postgresql.JSONB(none_as_null=True), nullable=True
        ),
    )
    op.create_check_constraint(
        "ck_chat_message_answer_basis_size",
        "chat_message",
        "answer_basis IS NULL OR octet_length(answer_basis::text) <= 16384",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_chat_message_answer_basis_size", "chat_message", type_="check"
    )
    op.drop_column("chat_message", "answer_basis")
