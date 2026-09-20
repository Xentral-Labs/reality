"""Admit explicitly classified inventory returns and losses."""

from alembic import op
from sqlalchemy import text

revision = "0082_inventory_returns_losses"
down_revision = "0081_inventory_specific_policy"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_inventory_movement", "cost_movement_basis", type_="check")
    op.create_check_constraint(
        "ck_inventory_movement",
        "cost_movement_basis",
        "base_quantity>0 AND movement_type IN ('receipt','shipment','transfer','return','supplier_return','adjustment') AND input_schema_version=1",
    )
    op.drop_constraint("ck_inventory_member", "cost_inventory_member", type_="check")
    op.create_check_constraint(
        "ck_inventory_member",
        "cost_inventory_member",
        "(kind='receipt' AND receipt_manifest_id IS NOT NULL AND ownership_revision_id IS NOT NULL) OR (kind IN ('issue','transfer','loss','supplier_return','customer_return') AND receipt_manifest_id IS NULL AND ownership_revision_id IS NULL)",
    )


def downgrade():
    retained = (
        op.get_bind()
        .execute(
            text(
                "SELECT 1 FROM cost_inventory_member m JOIN cost_movement_basis b ON b.tenant_id=m.tenant_id AND b.id=m.movement_basis_id WHERE m.kind IN ('loss','supplier_return','customer_return') OR b.movement_type IN ('return','supplier_return','adjustment') LIMIT 1"
            )
        )
        .scalar()
    )
    if retained:
        raise RuntimeError(
            "Cannot remove return/loss support while retained inventory inputs exist."
        )
    op.drop_constraint("ck_inventory_member", "cost_inventory_member", type_="check")
    op.create_check_constraint(
        "ck_inventory_member",
        "cost_inventory_member",
        "(kind='receipt' AND receipt_manifest_id IS NOT NULL AND ownership_revision_id IS NOT NULL) OR (kind IN ('issue','transfer') AND receipt_manifest_id IS NULL AND ownership_revision_id IS NULL)",
    )
    op.drop_constraint("ck_inventory_movement", "cost_movement_basis", type_="check")
    op.create_check_constraint(
        "ck_inventory_movement",
        "cost_movement_basis",
        "base_quantity>0 AND movement_type IN ('receipt','shipment','transfer') AND input_schema_version=1",
    )
