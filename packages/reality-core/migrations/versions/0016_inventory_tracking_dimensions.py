"""Add lot and serial dimensions to movements and reservations.

Revision ID: 0016_inventory_tracking_dimensions
Revises: 0015_handling_units
"""

import sqlalchemy as sa
from alembic import op

revision = "0016_inventory_tracking_dimensions"
down_revision = "0015_handling_units"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Revision names from this point can exceed Alembic's original 32 characters.
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=32),
        type_=sa.String(length=128),
        existing_nullable=False,
    )
    op.create_table(
        "lot",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("item_id", sa.String(), sa.ForeignKey("item.id"), nullable=False),
        sa.Column("lot_number", sa.String(), nullable=False),
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "item_id", "lot_number"),
    )
    op.create_index("ix_lot_tenant_id", "lot", ["tenant_id"])
    op.create_index("ix_lot_item_id", "lot", ["item_id"])
    op.create_table(
        "serial_unit",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("item_id", sa.String(), sa.ForeignKey("item.id"), nullable=False),
        sa.Column("serial_number", sa.String(), nullable=False),
        sa.Column("lot_id", sa.String(), sa.ForeignKey("lot.id"), nullable=True),
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "item_id", "serial_number"),
    )
    op.create_index("ix_serial_unit_tenant_id", "serial_unit", ["tenant_id"])
    op.create_index("ix_serial_unit_item_id", "serial_unit", ["item_id"])
    for table_name in ("movement", "reservation"):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(sa.Column("lot_id", sa.String(), nullable=True))
            batch_op.add_column(sa.Column("serial_unit_id", sa.String(), nullable=True))
            batch_op.create_foreign_key(
                f"fk_{table_name}_lot_id", "lot", ["lot_id"], ["id"]
            )
            batch_op.create_foreign_key(
                f"fk_{table_name}_serial_unit_id",
                "serial_unit",
                ["serial_unit_id"],
                ["id"],
            )
    with op.batch_alter_table("reservation") as batch_op:
        batch_op.add_column(sa.Column("handling_unit_id", sa.String(), nullable=True))
        batch_op.create_foreign_key(
            "fk_reservation_handling_unit_id",
            "handling_unit",
            ["handling_unit_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("reservation") as batch_op:
        batch_op.drop_constraint("fk_reservation_handling_unit_id", type_="foreignkey")
        batch_op.drop_column("handling_unit_id")
    for table_name in ("reservation", "movement"):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(f"fk_{table_name}_serial_unit_id", type_="foreignkey")
            batch_op.drop_constraint(f"fk_{table_name}_lot_id", type_="foreignkey")
            batch_op.drop_column("serial_unit_id")
            batch_op.drop_column("lot_id")
    op.drop_table("serial_unit")
    op.drop_table("lot")
