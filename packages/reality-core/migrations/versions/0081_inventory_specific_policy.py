"""Permit explicitly confirmed specific-identification inventory policies."""

from alembic import op
from sqlalchemy import text

revision = "0081_inventory_specific_policy"
down_revision = "0080_company_generations"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_inventory_policy", "cost_policy_revision", type_="check")
    op.create_check_constraint(
        "ck_inventory_policy",
        "cost_policy_revision",
        "revision>0 AND method IN ('fifo','specific')",
    )


def downgrade():
    connection = op.get_bind()
    if connection.execute(
        text("SELECT 1 FROM cost_policy_revision WHERE method='specific' LIMIT 1")
    ).scalar():
        raise RuntimeError(
            "Cannot remove specific-identification support while retained policies exist."
        )
    op.drop_constraint("ck_inventory_policy", "cost_policy_revision", type_="check")
    op.create_check_constraint(
        "ck_inventory_policy",
        "cost_policy_revision",
        "revision>0 AND method='fifo'",
    )
