"""Let a payment term state an early-payment discount.

Revision ID: 0039_early_payment_discount
Revises: 0038_return_resolution
"""

import sqlalchemy as sa
from alembic import op

revision = "0039_early_payment_discount"
down_revision = "0038_return_resolution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable by design, and no backfill: most payment terms grant no early
    # payment discount, and their absence says exactly that. A zero would say
    # "nothing off", which is a different and wrong statement.
    #
    # Three decimal places is past anything trade quotes, so a stored rate is
    # never a rounded version of the rate somebody stated.
    op.add_column(
        "payment_term",
        sa.Column("discount_percent", sa.Numeric(6, 3), nullable=True),
    )
    op.add_column(
        "payment_term",
        sa.Column("discount_days", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("payment_term", "discount_days")
    op.drop_column("payment_term", "discount_percent")
