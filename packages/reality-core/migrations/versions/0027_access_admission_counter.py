"""Add the automatic access admission counter.

Revision ID: 0027_access_admission_counter
Revises: 0026_secret_vault
"""

import sqlalchemy as sa
from alembic import op

revision = "0027_access_admission_counter"
down_revision = "0026_secret_vault"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "access_admission_counter",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("used_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO access_admission_counter (id, used_slots, updated_at)
            SELECT 'automatic', COUNT(*), CURRENT_TIMESTAMP
            FROM app_user
            WHERE status = 'active' AND is_platform_admin = false
            """
        )
    )


def downgrade() -> None:
    op.drop_table("access_admission_counter")
