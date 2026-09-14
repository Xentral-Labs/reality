"""Retain archived chat sessions and their audit context.

Revision ID: 0031_chat_session_archiving
Revises: 0030_company_membership_invitations
"""

import sqlalchemy as sa
from alembic import op

revision = "0031_chat_session_archiving"
down_revision = "0030_company_membership_invitations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_session", sa.Column("archived_at", sa.DateTime(timezone=True))
    )
    op.create_index(
        "ix_chat_session_tenant_archived",
        "chat_session",
        ["tenant_id", "archived_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_chat_session_tenant_archived", table_name="chat_session")
    op.drop_column("chat_session", "archived_at")
