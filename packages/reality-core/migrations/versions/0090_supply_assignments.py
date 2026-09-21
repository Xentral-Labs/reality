"""Add explicit append-only supplier supply assignments.

Revision ID: 0090_supply_assignments
Revises: 0089_commercial_edge_workflows
"""

import sqlalchemy as sa
from alembic import op

revision = "0090_supply_assignments"
down_revision = "0089_commercial_edge_workflows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supply_assignment",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("supplier_commitment_id", sa.String(), nullable=False),
        sa.Column("customer_commitment_id", sa.String(), nullable=True),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("reverses_assignment_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "supplier_commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "customer_commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reverses_assignment_id"],
            ["supply_assignment.tenant_id", "supply_assignment.id"],
        ),
        sa.CheckConstraint(
            "purpose IN ('customer_demand', 'stock_replenishment')",
            name="ck_supply_assignment_purpose",
        ),
        sa.CheckConstraint(
            "quantity > 0", name="ck_supply_assignment_quantity_positive"
        ),
        sa.CheckConstraint(
            "(purpose = 'customer_demand' AND customer_commitment_id IS NOT NULL) "
            "OR (purpose = 'stock_replenishment' AND customer_commitment_id IS NULL)",
            name="ck_supply_assignment_customer_purpose",
        ),
        sa.CheckConstraint(
            "reverses_assignment_id IS NULL OR reverses_assignment_id <> id",
            name="ck_supply_assignment_not_self_reversal",
        ),
        sa.UniqueConstraint(
            "tenant_id", "source_record_id", name="uq_supply_assignment_source"
        ),
    )
    op.create_index(
        "ix_supply_assignment_tenant_id", "supply_assignment", ["tenant_id"]
    )
    op.create_index(
        "ix_supply_assignment_tenant_supplier",
        "supply_assignment",
        ["tenant_id", "supplier_commitment_id"],
    )
    op.create_index(
        "ix_supply_assignment_tenant_customer",
        "supply_assignment",
        ["tenant_id", "customer_commitment_id"],
    )


def downgrade() -> None:
    op.drop_table("supply_assignment")
