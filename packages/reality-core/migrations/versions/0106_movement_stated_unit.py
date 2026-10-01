"""The quantity and unit a receipt stated, beside its stock-unit quantity (spec 301).

Revision ID: 0106_movement_stated_unit
Revises: 0105_down_payments
"""

import sqlalchemy as sa
from alembic import op

revision = "0106_movement_stated_unit"
down_revision = "0105_down_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("movement", sa.Column("stated_quantity", sa.Numeric(18, 4)))
    op.add_column("movement", sa.Column("stated_unit", sa.String()))
    op.create_check_constraint(
        "ck_movement_stated_unit",
        "movement",
        "(stated_quantity IS NULL) = (stated_unit IS NULL)",
    )


def downgrade() -> None:
    stated = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM movement WHERE stated_unit IS NOT NULL"))
        .scalar()
    )
    if stated:
        raise RuntimeError(
            f"{stated} receipts were stated in a purchase unit; the stated quantity "
            "and unit cannot be removed."
        )
    op.drop_constraint("ck_movement_stated_unit", "movement", type_="check")
    op.drop_column("movement", "stated_unit")
    op.drop_column("movement", "stated_quantity")
