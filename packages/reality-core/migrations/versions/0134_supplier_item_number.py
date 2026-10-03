"""A supplier's own number and name for our items (spec 345).

Revision ID: 0134_supplier_item_number
Revises: 0133_external_stock
"""

import sqlalchemy as sa
from alembic import op

revision = "0134_supplier_item_number"
down_revision = "0133_external_stock"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_item_number",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("party_id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("supplier_item_number", sa.String(), nullable=False),
        sa.Column("match_key", sa.String(), nullable=False),
        sa.Column("supplier_item_name", sa.String(), nullable=False),
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
            "tenant_id", "party_id", "match_key", name="uq_supplier_item_number_key"
        ),
        sa.CheckConstraint(
            "btrim(supplier_item_number) <> ''", name="ck_supplier_item_number_number"
        ),
    )
    op.create_index(
        "ix_supplier_item_number_tenant_id", "supplier_item_number", ["tenant_id"]
    )
    op.create_index(
        "ix_supplier_item_number_item_id",
        "supplier_item_number",
        ["tenant_id", "item_id"],
    )
    op.create_index(
        "ix_supplier_item_number_source_record_id",
        "supplier_item_number",
        ["tenant_id", "source_record_id"],
    )


def downgrade() -> None:
    stated = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM supplier_item_number"))
        .scalar()
    )
    if stated:
        raise RuntimeError(
            f"{stated} supplier item numbers are stated; they cannot be removed."
        )
    op.drop_table("supplier_item_number")
