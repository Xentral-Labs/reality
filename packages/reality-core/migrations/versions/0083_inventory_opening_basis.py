"""Retain evidenced inventory opening acquisition-cost authority."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "0083_inventory_opening_basis"
down_revision = "0082_inventory_returns_losses"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cost_opening_basis",
        sa.Column("movement_basis_id", sa.String(), nullable=False),
        sa.Column("owner_party_id", sa.String(), nullable=False),
        sa.Column("evidence_source_record_id", sa.String(), nullable=False),
        sa.Column("acquisition_cost", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("input_schema_version", sa.Integer(), nullable=False),
        sa.Column("introduced_event_id", sa.String(), nullable=False),
        sa.Column("action_id", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "movement_basis_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "movement_basis_id"],
            ["cost_movement_basis.tenant_id", "cost_movement_basis.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "owner_party_id"], ["party.tenant_id", "party.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "evidence_source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "introduced_event_id"],
            ["business_event.tenant_id", "business_event.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "action_id"], ["action.tenant_id", "action.id"]
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.CheckConstraint(
            "acquisition_cost>=0 AND input_schema_version=1",
            name="ck_inventory_opening",
        ),
    )
    op.drop_constraint("ck_inventory_movement", "cost_movement_basis", type_="check")
    op.create_check_constraint(
        "ck_inventory_movement",
        "cost_movement_basis",
        "base_quantity>0 AND movement_type IN ('receipt','shipment','transfer','return','supplier_return','adjustment','opening_stock') AND input_schema_version=1",
    )
    op.drop_constraint("ck_inventory_member", "cost_inventory_member", type_="check")
    op.create_check_constraint(
        "ck_inventory_member",
        "cost_inventory_member",
        "(kind='receipt' AND receipt_manifest_id IS NOT NULL AND ownership_revision_id IS NOT NULL) OR (kind IN ('issue','transfer','loss','supplier_return','customer_return','opening') AND receipt_manifest_id IS NULL AND ownership_revision_id IS NULL)",
    )


def downgrade():
    if op.get_bind().execute(text("SELECT 1 FROM cost_opening_basis LIMIT 1")).scalar():
        raise RuntimeError(
            "Cannot remove opening-basis support while retained inputs exist."
        )
    op.drop_constraint("ck_inventory_member", "cost_inventory_member", type_="check")
    op.create_check_constraint(
        "ck_inventory_member",
        "cost_inventory_member",
        "(kind='receipt' AND receipt_manifest_id IS NOT NULL AND ownership_revision_id IS NOT NULL) OR (kind IN ('issue','transfer','loss','supplier_return','customer_return') AND receipt_manifest_id IS NULL AND ownership_revision_id IS NULL)",
    )
    op.drop_constraint("ck_inventory_movement", "cost_movement_basis", type_="check")
    op.create_check_constraint(
        "ck_inventory_movement",
        "cost_movement_basis",
        "base_quantity>0 AND movement_type IN ('receipt','shipment','transfer','return','supplier_return','adjustment') AND input_schema_version=1",
    )
    op.drop_table("cost_opening_basis")
