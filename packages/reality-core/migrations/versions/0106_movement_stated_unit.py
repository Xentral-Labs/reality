"""The quantity and unit a receipt stated, and the unit a promise is held in (spec 301).

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
    # Set on purchase promises made since spec 301: the stock unit they were
    # converted into. A promise without it keeps its line's unit.
    op.add_column("commitment", sa.Column("unit", sa.String()))


def downgrade() -> None:
    held = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM commitment WHERE unit IS NOT NULL"))
        .scalar()
    )
    if held:
        raise RuntimeError(
            f"{held} promises are held in the stock unit of a purchase unit; "
            "without the unit they would read as stated in their line's unit."
        )
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
    op.drop_column("commitment", "unit")
    op.drop_constraint("ck_movement_stated_unit", "movement", type_="check")
    op.drop_column("movement", "stated_unit")
    op.drop_column("movement", "stated_quantity")
