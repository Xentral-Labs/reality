"""Link parties and items to immutable source records.

Revision ID: 0004_master_data_source
Revises: 0003_master_data_active
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_master_data_source"
down_revision = "0003_master_data_active"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("party", "item"):
        op.add_column(
            table,
            sa.Column(
                "source_record_id",
                sa.String(),
                sa.ForeignKey("source_record.id"),
                nullable=True,
            ),
        )


def downgrade() -> None:
    for table in ("party", "item"):
        op.drop_column(table, "source_record_id")
