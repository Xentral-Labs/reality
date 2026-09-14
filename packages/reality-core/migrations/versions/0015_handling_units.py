"""Add optional pallet handling units to movements.

Revision ID: 0015_handling_units
Revises: 0014_tenant_lifecycle
"""

import sqlalchemy as sa
from alembic import op

revision = "0015_handling_units"
down_revision = "0014_tenant_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "handling_unit",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("nve", sa.String(), nullable=True),
        sa.Column(
            "source_record_id",
            sa.String(),
            sa.ForeignKey("source_record.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "nve"),
    )
    op.create_index("ix_handling_unit_tenant_id", "handling_unit", ["tenant_id"])
    with op.batch_alter_table("movement") as batch_op:
        batch_op.add_column(
            sa.Column("handling_unit_id", sa.String(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_movement_handling_unit_id",
            "handling_unit",
            ["handling_unit_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("movement") as batch_op:
        batch_op.drop_constraint(
            "fk_movement_handling_unit_id", type_="foreignkey"
        )
        batch_op.drop_column("handling_unit_id")
    op.drop_table("handling_unit")
