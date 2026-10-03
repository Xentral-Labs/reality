"""Keep source-unstated line and physical-promise amounts unknown (spec 352)."""

import sqlalchemy as sa
from alembic import op

revision = "0139_unstated_source_amounts"
down_revision = "0138_company_time_zone"
branch_labels = None
depends_on = None

COLUMNS = (("document_line", "gross_amount"), ("commitment", "amount"))


def upgrade() -> None:
    for table, column in COLUMNS:
        op.alter_column(table, column, existing_type=sa.Numeric(18, 4), nullable=True)


def downgrade() -> None:
    connection = op.get_bind()
    for table, column in COLUMNS:
        if connection.execute(
            sa.text(f"SELECT 1 FROM {table} WHERE {column} IS NULL LIMIT 1")
        ).first():
            raise RuntimeError(
                "Cannot roll back while source-unstated amounts remain; never replace unknown evidence with invented values."
            )
    for table, column in COLUMNS:
        op.alter_column(table, column, existing_type=sa.Numeric(18, 4), nullable=False)
