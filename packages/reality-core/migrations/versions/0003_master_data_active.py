"""Add lifecycle state to master data.

Revision ID: 0003_master_data_active
Revises: 0002_settlement_allocations
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_master_data_active"
down_revision = "0002_settlement_allocations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("party", "item", "location"):
        op.add_column(
            table,
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
        )


def downgrade() -> None:
    for table in ("party", "item", "location"):
        op.drop_column(table, "is_active")
