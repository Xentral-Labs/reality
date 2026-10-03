"""Kit components: the bill of materials of a kit (spec 333).

Revision ID: 0127_kit_components
Revises: 0125_delivery_failures
"""

import sqlalchemy as sa
from alembic import op

revision = "0127_kit_components"
down_revision = "0125_delivery_failures"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "kit_component",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("kit_item_id", sa.String(), nullable=False),
        sa.Column("component_item_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("share", sa.Numeric(9, 6), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "kit_item_id"], ["item.tenant_id", "item.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "component_item_id"], ["item.tenant_id", "item.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "kit_item_id",
            "component_item_id",
            name="uq_kit_component_kit_component",
        ),
        sa.CheckConstraint(
            "quantity > 0 AND (share IS NULL OR (share >= 0 AND share <= 1))"
            " AND kit_item_id <> component_item_id",
            name="ck_kit_component_values",
        ),
    )
    op.create_index("ix_kit_component_tenant_id", "kit_component", ["tenant_id"])
    op.create_index(
        "ix_kit_component_component_item_id",
        "kit_component",
        ["tenant_id", "component_item_id"],
    )
    op.create_index(
        "ix_kit_component_source_record_id",
        "kit_component",
        ["tenant_id", "source_record_id"],
    )


def downgrade() -> None:
    stated = (
        op.get_bind().execute(sa.text("SELECT count(*) FROM kit_component")).scalar()
    )
    if stated:
        raise RuntimeError(
            f"{stated} kit components are stated; they cannot be removed."
        )
    op.drop_table("kit_component")
