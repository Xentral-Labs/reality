"""Retain explicit economic-ownership portions for inventory movements."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "0084_inventory_ownership_parts"
down_revision = "0083_inventory_opening_basis"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cost_inventory_ownership_part",
        sa.Column("review_id", sa.String(), nullable=False),
        sa.Column("movement_basis_id", sa.String(), nullable=False),
        sa.Column("owner_party_id", sa.String(), nullable=False),
        sa.Column("evidence_source_record_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("input_schema_version", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint(
            "tenant_id", "review_id", "movement_basis_id", "owner_party_id"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "review_id"],
            ["cost_inventory_review.tenant_id", "cost_inventory_review.id"],
        ),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.CheckConstraint(
            "quantity>0 AND input_schema_version=1", name="ck_inventory_ownership_part"
        ),
    )
    op.create_index(
        "ix_cost_inventory_ownership_part_review_id",
        "cost_inventory_ownership_part",
        ["review_id"],
    )


def downgrade():
    if (
        op.get_bind()
        .execute(text("SELECT 1 FROM cost_inventory_ownership_part LIMIT 1"))
        .scalar()
    ):
        raise RuntimeError(
            "Cannot remove ownership-part support while retained inputs exist."
        )
    op.drop_index(
        "ix_cost_inventory_ownership_part_review_id",
        table_name="cost_inventory_ownership_part",
    )
    op.drop_table("cost_inventory_ownership_part")
