"""Stock held back where it lies, with its reason (spec 304).

Revision ID: 0108_stock_block
Revises: 0107_item_reorder_point
"""

import sqlalchemy as sa
from alembic import op

revision = "0108_stock_block"
down_revision = "0107_item_reorder_point"
branch_labels = None
depends_on = None

_REFERENCES = (
    "location_id",
    "handling_unit_id",
    "lot_id",
    "serial_unit_id",
    "previous_block_id",
    "movement_id",
)


def upgrade() -> None:
    op.create_table(
        "stock_block",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("location_id", sa.String(), nullable=False),
        sa.Column("handling_unit_id", sa.String(), nullable=True),
        sa.Column("lot_id", sa.String(), nullable=True),
        sa.Column("serial_unit_id", sa.String(), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("reason_code", sa.String(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(), nullable=True),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        sa.Column("previous_block_id", sa.String(), nullable=True),
        sa.Column("movement_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "item_id"], ["item.tenant_id", "item.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "location_id"], ["location.tenant_id", "location.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "handling_unit_id"],
            ["handling_unit.tenant_id", "handling_unit.id"],
        ),
        sa.ForeignKeyConstraint(["tenant_id", "lot_id"], ["lot.tenant_id", "lot.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "serial_unit_id"],
            ["serial_unit.tenant_id", "serial_unit.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "previous_block_id"],
            ["stock_block.tenant_id", "stock_block.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "movement_id"], ["movement.tenant_id", "movement.id"]
        ),
        sa.CheckConstraint("quantity > 0", name="ck_stock_block_quantity"),
        sa.CheckConstraint(
            "reason_code IN ('quality','damage','expiry','inspection')",
            name="ck_stock_block_reason",
        ),
        sa.CheckConstraint(
            "status IN ('active','released','scrapped')", name="ck_stock_block_status"
        ),
    )
    op.create_index("ix_stock_block_tenant_id", "stock_block", ["tenant_id"])
    op.create_index(
        "ix_stock_block_item_location_status",
        "stock_block",
        ["tenant_id", "item_id", "location_id", "status"],
    )
    for column in _REFERENCES:
        op.create_index(
            f"ix_stock_block_{column}", "stock_block", ["tenant_id", column]
        )


def downgrade() -> None:
    held = op.get_bind().execute(sa.text("SELECT count(*) FROM stock_block")).scalar()
    if held:
        raise RuntimeError(f"{held} stock blocks exist; they cannot be removed.")
    op.drop_table("stock_block")
