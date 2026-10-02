"""A customer's own number and name for our items (spec 308).

Revision ID: 0114_customer_item_number
Revises: 0113_stock_count
"""

import sqlalchemy as sa
from alembic import op

revision = "0114_customer_item_number"
down_revision = "0113_stock_count"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_item_number",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("party_id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("customer_item_number", sa.String(), nullable=False),
        sa.Column("match_key", sa.String(), nullable=False),
        sa.Column("customer_item_name", sa.String(), nullable=False),
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
            "tenant_id", "party_id", "match_key", name="uq_customer_item_number_key"
        ),
        sa.CheckConstraint(
            "btrim(customer_item_number) <> ''", name="ck_customer_item_number_number"
        ),
    )
    op.create_index(
        "ix_customer_item_number_tenant_id", "customer_item_number", ["tenant_id"]
    )
    op.create_index(
        "ix_customer_item_number_item_id",
        "customer_item_number",
        ["tenant_id", "item_id"],
    )
    op.create_index(
        "ix_customer_item_number_source_record_id",
        "customer_item_number",
        ["tenant_id", "source_record_id"],
    )


def downgrade() -> None:
    stated = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM customer_item_number"))
        .scalar()
    )
    if stated:
        raise RuntimeError(
            f"{stated} customer item numbers are stated; they cannot be removed."
        )
    op.drop_table("customer_item_number")
