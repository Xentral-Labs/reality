"""Keep source-unstated order totals unknown (spec 353)."""

import sqlalchemy as sa
from alembic import op

revision = "0140_unstated_document_totals"
down_revision = "0139_unstated_source_amounts"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "document", "gross_amount", existing_type=sa.Numeric(18, 4), nullable=True
    )


def downgrade():
    if (
        op.get_bind()
        .execute(sa.text("SELECT 1 FROM document WHERE gross_amount IS NULL LIMIT 1"))
        .first()
    ):
        raise RuntimeError(
            "Cannot roll back while source-unstated order totals remain; never invent replacement amounts."
        )
    op.alter_column(
        "document", "gross_amount", existing_type=sa.Numeric(18, 4), nullable=False
    )
