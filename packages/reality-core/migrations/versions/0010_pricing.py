"""Add explainable sales and purchase pricing.

Revision ID: 0010_pricing
Revises: 0009_payment_terms
"""

import sqlalchemy as sa
from alembic import op

revision = "0010_pricing"
down_revision = "0009_payment_terms"
branch_labels = None
depends_on = None


def time_column(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=True)


def upgrade() -> None:
    op.create_table(
        "price_list",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        time_column("valid_from"),
        time_column("valid_until"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("source_record_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_record.id"]),
        sa.UniqueConstraint("tenant_id", "code"),
    )
    op.create_index("ix_price_list_tenant_id", "price_list", ["tenant_id"])
    op.create_table(
        "price_list_entry",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("price_list_id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("min_quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        time_column("valid_from"),
        time_column("valid_until"),
        sa.Column("source_record_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["price_list_id"], ["price_list.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"]),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_record.id"]),
        sa.UniqueConstraint("tenant_id", "price_list_id", "item_id", "min_quantity"),
    )
    for name, columns in (
        ("ix_price_list_entry_tenant_id", ["tenant_id"]),
        ("ix_price_list_entry_price_list_id", ["price_list_id"]),
        ("ix_price_list_entry_item_id", ["item_id"]),
    ):
        op.create_index(name, "price_list_entry", columns)
    op.create_table(
        "party_price_list",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("party_id", sa.String(), nullable=False),
        sa.Column("price_list_id", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        time_column("valid_from"),
        time_column("valid_until"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["party_id"], ["party.id"]),
        sa.ForeignKeyConstraint(["price_list_id"], ["price_list.id"]),
        sa.UniqueConstraint("tenant_id", "party_id", "price_list_id"),
    )
    op.create_table(
        "party_group",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("group_type", sa.String(), nullable=False, server_default="pricing"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("source_record_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_record.id"]),
        sa.UniqueConstraint("tenant_id", "code"),
    )
    op.create_table(
        "party_group_member",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("party_group_id", sa.String(), nullable=False),
        sa.Column("party_id", sa.String(), nullable=False),
        time_column("valid_from"),
        time_column("valid_until"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["party_group_id"], ["party_group.id"]),
        sa.ForeignKeyConstraint(["party_id"], ["party.id"]),
        sa.UniqueConstraint("tenant_id", "party_group_id", "party_id"),
    )
    op.create_table(
        "party_group_price_list",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("party_group_id", sa.String(), nullable=False),
        sa.Column("price_list_id", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        time_column("valid_from"),
        time_column("valid_until"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["party_group_id"], ["party_group.id"]),
        sa.ForeignKeyConstraint(["price_list_id"], ["price_list.id"]),
        sa.UniqueConstraint("tenant_id", "party_group_id", "price_list_id"),
    )
    for table, columns in (
        ("party_price_list", ("tenant_id", "party_id", "price_list_id")),
        ("party_group", ("tenant_id",)),
        ("party_group_member", ("tenant_id", "party_group_id", "party_id")),
        ("party_group_price_list", ("tenant_id", "party_group_id", "price_list_id")),
    ):
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column])
    with op.batch_alter_table("document_line") as batch:
        batch.add_column(sa.Column("price_list_entry_id", sa.String(), nullable=True))
        batch.create_foreign_key(
            "fk_document_line_price_entry",
            "price_list_entry",
            ["price_list_entry_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("document_line") as batch:
        batch.drop_constraint("fk_document_line_price_entry", type_="foreignkey")
        batch.drop_column("price_list_entry_id")
    for table in (
        "party_group_price_list",
        "party_group_member",
        "party_group",
        "party_price_list",
        "price_list_entry",
        "price_list",
    ):
        op.drop_table(table)
