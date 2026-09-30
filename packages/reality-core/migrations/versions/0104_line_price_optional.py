"""Let a document line state no price when its source gave none (spec 314).

Revision ID: 0104_line_price_optional
Revises: 0103_payment_returns
"""

import sqlalchemy as sa
from alembic import op

revision = "0104_line_price_optional"
down_revision = "0103_payment_returns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "document_line", "unit_price", existing_type=sa.Numeric(18, 4), nullable=True
    )


def downgrade() -> None:
    # A price nobody stated is not invented to make the column required again.
    unpriced = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM document_line WHERE unit_price IS NULL"))
        .scalar()
    )
    if unpriced:
        raise RuntimeError(
            f"{unpriced} document lines state no price; state them before downgrading."
        )
    op.alter_column(
        "document_line", "unit_price", existing_type=sa.Numeric(18, 4), nullable=False
    )
