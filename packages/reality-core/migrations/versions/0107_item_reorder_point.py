"""A reorder point and quantity per item and location (spec 302).

Revision ID: 0107_item_reorder_point
Revises: 0106_movement_stated_unit
"""

import sqlalchemy as sa
from alembic import op

revision = "0107_item_reorder_point"
down_revision = "0106_movement_stated_unit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "item_reorder_point",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("location_id", sa.String(), nullable=False),
        sa.Column("reorder_point", sa.Numeric(18, 4), nullable=False),
        sa.Column("reorder_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "item_id"], ["item.tenant_id", "item.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "location_id"], ["location.tenant_id", "location.id"]
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "item_id",
            "location_id",
            name="uq_item_reorder_point_item_location",
        ),
        sa.CheckConstraint(
            "reorder_point >= 0 AND reorder_quantity > 0",
            name="ck_item_reorder_point_values",
        ),
    )
    op.create_index(
        "ix_item_reorder_point_tenant_id", "item_reorder_point", ["tenant_id"]
    )
    op.create_index(
        "ix_item_reorder_point_location_id",
        "item_reorder_point",
        ["tenant_id", "location_id"],
    )


def downgrade() -> None:
    stated = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM item_reorder_point"))
        .scalar()
    )
    if stated:
        raise RuntimeError(
            f"{stated} reorder points are stated; they cannot be removed."
        )
    op.drop_table("item_reorder_point")
