"""store UI language separately from locale

Revision ID: 0025_user_language
Revises: 0024_user_access
"""

import sqlalchemy as sa
from alembic import op

revision = "0025_user_language"
down_revision = "0024_user_access"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_user",
        sa.Column("language", sa.String(), nullable=False, server_default="en"),
    )


def downgrade() -> None:
    op.drop_column("app_user", "language")
