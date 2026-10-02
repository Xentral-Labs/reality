"""A count of one location and its counted lines (spec 307).

Revision ID: 0113_stock_count
Revises: 0112_delivery_rule
"""

import sqlalchemy as sa
from alembic import op

revision = "0113_stock_count"
down_revision = "0112_delivery_rule"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_count",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("location_id", sa.String(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "location_id"], ["location.tenant_id", "location.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
    )
    op.create_index("ix_stock_count_tenant_id", "stock_count", ["tenant_id"])
    op.create_index(
        "ix_stock_count_location_id", "stock_count", ["tenant_id", "location_id"]
    )
    op.create_index(
        "uq_stock_count_source",
        "stock_count",
        ["tenant_id", "source_record_id"],
        unique=True,
    )
    op.create_table(
        "stock_count_line",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("stock_count_id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("lot_id", sa.String(), nullable=True),
        sa.Column("counted_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("counted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("movement_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "stock_count_id"], ["stock_count.tenant_id", "stock_count.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "item_id"], ["item.tenant_id", "item.id"]
        ),
        sa.ForeignKeyConstraint(["tenant_id", "lot_id"], ["lot.tenant_id", "lot.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "movement_id"], ["movement.tenant_id", "movement.id"]
        ),
        sa.CheckConstraint(
            "counted_quantity >= 0", name="ck_stock_count_line_counted_quantity"
        ),
    )
    op.create_index("ix_stock_count_line_tenant_id", "stock_count_line", ["tenant_id"])
    op.create_index(
        "uq_stock_count_line_item_lot",
        "stock_count_line",
        ["tenant_id", "stock_count_id", "item_id", sa.text("coalesce(lot_id, '')")],
        unique=True,
    )
    op.create_index(
        "ix_stock_count_line_movement_id",
        "stock_count_line",
        ["tenant_id", "movement_id"],
    )
    op.create_index(
        "ix_stock_count_line_item_id", "stock_count_line", ["tenant_id", "item_id"]
    )
    op.create_index(
        "ix_stock_count_line_lot_id", "stock_count_line", ["tenant_id", "lot_id"]
    )


def downgrade() -> None:
    counted = (
        op.get_bind().execute(sa.text("SELECT count(*) FROM stock_count")).scalar()
    )
    if counted:
        raise RuntimeError(
            f"{counted} stock counts are recorded; they cannot be removed."
        )
    op.drop_table("stock_count_line")
    op.drop_table("stock_count")
