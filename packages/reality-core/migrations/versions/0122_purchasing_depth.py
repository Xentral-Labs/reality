"""Confirmed purchase prices and supplier item terms (spec 310).

Revision ID: 0122_purchasing_depth
Revises: 0121_census_members
"""

import sqlalchemy as sa
from alembic import op

revision = "0122_purchasing_depth"
down_revision = "0121_census_members"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "commitment_revision",
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=True),
    )
    op.create_check_constraint(
        "ck_commitment_revision_unit_price",
        "commitment_revision",
        "unit_price IS NULL OR unit_price >= 0",
    )
    op.create_table(
        "supplier_item_terms",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("party_id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("minimum_quantity", sa.Numeric(18, 4), nullable=True),
        sa.Column("order_multiple", sa.Numeric(18, 4), nullable=True),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "party_id"], ["party.tenant_id", "party.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "item_id"], ["item.tenant_id", "item.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id", "party_id", "item_id", name="uq_supplier_item_terms_item"
        ),
        sa.CheckConstraint(
            "minimum_quantity IS NOT NULL OR order_multiple IS NOT NULL",
            name="ck_supplier_item_terms_stated",
        ),
        sa.CheckConstraint(
            "(minimum_quantity IS NULL OR minimum_quantity > 0) "
            "AND (order_multiple IS NULL OR order_multiple > 0)",
            name="ck_supplier_item_terms_positive",
        ),
    )
    op.create_index(
        "ix_supplier_item_terms_tenant_id", "supplier_item_terms", ["tenant_id"]
    )
    op.create_index(
        "ix_supplier_item_terms_item_id",
        "supplier_item_terms",
        ["tenant_id", "item_id"],
    )
    op.create_index(
        "ix_supplier_item_terms_source_record_id",
        "supplier_item_terms",
        ["tenant_id", "source_record_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    prices = bind.execute(
        sa.text("SELECT count(*) FROM commitment_revision WHERE unit_price IS NOT NULL")
    ).scalar()
    terms = bind.execute(sa.text("SELECT count(*) FROM supplier_item_terms")).scalar()
    if prices or terms:
        raise RuntimeError(
            f"{prices} confirmed prices and {terms} supplier item terms are stated; "
            "they cannot be removed."
        )
    op.drop_table("supplier_item_terms")
    op.drop_constraint(
        "ck_commitment_revision_unit_price", "commitment_revision", type_="check"
    )
    op.drop_column("commitment_revision", "unit_price")
