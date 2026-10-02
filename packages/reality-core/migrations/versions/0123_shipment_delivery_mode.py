"""A shipment's delivery mode: carrier or customer pickup (spec 312).

Revision ID: 0123_shipment_delivery_mode
Revises: 0122_purchasing_depth
"""

import sqlalchemy as sa
from alembic import op

revision = "0123_shipment_delivery_mode"
down_revision = "0122_purchasing_depth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("shipment", sa.Column("delivery_mode", sa.String(), nullable=True))
    op.create_check_constraint(
        "ck_shipment_delivery_mode",
        "shipment",
        "delivery_mode IS NULL OR delivery_mode IN ('carrier', 'pickup')",
    )


def downgrade() -> None:
    pickups = (
        op.get_bind()
        .execute(
            sa.text("SELECT count(*) FROM shipment WHERE delivery_mode IS NOT NULL")
        )
        .scalar()
    )
    if pickups:
        raise RuntimeError(
            f"{pickups} shipments state a delivery mode; it cannot be removed."
        )
    op.drop_constraint("ck_shipment_delivery_mode", "shipment", type_="check")
    op.drop_column("shipment", "delivery_mode")
