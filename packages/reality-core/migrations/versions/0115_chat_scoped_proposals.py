"""Remember which conversation made a proposal (spec 328).

Revision ID: 0115_chat_scoped_proposals
Revises: 0114_customer_item_number
"""

import sqlalchemy as sa
from alembic import op

revision = "0115_chat_scoped_proposals"
down_revision = "0114_customer_item_number"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable and never backfilled: a link for older proposals could only be
    # guessed from timestamps, and a guessed link would claim more than is known.
    op.add_column("action", sa.Column("chat_session_id", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_action_chat_session",
        "action",
        "chat_session",
        ["tenant_id", "chat_session_id"],
        ["tenant_id", "id"],
    )
    op.create_index(
        "ix_action_tenant_chat_session", "action", ["tenant_id", "chat_session_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_action_tenant_chat_session", table_name="action")
    op.drop_constraint("fk_action_chat_session", "action", type_="foreignkey")
    op.drop_column("action", "chat_session_id")
