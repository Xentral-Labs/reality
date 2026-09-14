"""Add the proven operational fields selected for V0.

Revision ID: 0005_operational_fields
Revises: 0004_master_data_source
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_operational_fields"
down_revision = "0004_master_data_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "party",
        sa.Column("accounting_code", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "party",
        sa.Column("payment_term_code", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "party",
        sa.Column(
            "default_currency", sa.String(), nullable=False, server_default="EUR"
        ),
    )
    op.add_column(
        "party",
        sa.Column(
            "credit_limit", sa.Numeric(18, 4), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "party",
        sa.Column("tax_identifier", sa.String(), nullable=False, server_default=""),
    )

    op.add_column(
        "item",
        sa.Column("item_type", sa.String(), nullable=False, server_default="stocked"),
    )
    op.add_column(
        "item",
        sa.Column("tracking_type", sa.String(), nullable=False, server_default="none"),
    )
    op.add_column(
        "item",
        sa.Column("purchase_unit", sa.String(), nullable=False, server_default="pcs"),
    )
    op.add_column(
        "item",
        sa.Column(
            "conversion_factor", sa.Numeric(18, 6), nullable=False, server_default="1"
        ),
    )
    op.add_column(
        "item",
        sa.Column("lead_time_days", sa.Integer(), nullable=False, server_default="0"),
    )

    op.add_column(
        "location",
        sa.Column(
            "allows_stock", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )

    for name, column_type, default in (
        ("ordered_at", sa.DateTime(), None),
        ("requested_delivery_at", sa.DateTime(), None),
        ("customer_reference", sa.String(), ""),
        ("sales_channel", sa.String(), ""),
        ("payment_term_code", sa.String(), ""),
    ):
        op.add_column(
            "document",
            sa.Column(
                name, column_type, nullable=default is None, server_default=default
            ),
        )

    op.add_column(
        "document_line",
        sa.Column("unit", sa.String(), nullable=False, server_default="pcs"),
    )
    op.add_column(
        "document_line", sa.Column("requested_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "document_line",
        sa.Column("line_type", sa.String(), nullable=False, server_default="item"),
    )

    op.add_column("commitment", sa.Column("cancelled_at", sa.DateTime(), nullable=True))
    op.add_column(
        "commitment",
        sa.Column("priority", sa.String(), nullable=False, server_default="normal"),
    )

    op.add_column(
        "item",
        sa.Column("default_location_id", sa.String(), sa.ForeignKey("location.id")),
    )
    op.add_column(
        "location",
        sa.Column("parent_location_id", sa.String(), sa.ForeignKey("location.id")),
    )
    op.add_column(
        "location",
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id")),
    )
    op.add_column(
        "document",
        sa.Column("ship_to_party_id", sa.String(), sa.ForeignKey("party.id")),
    )
    op.alter_column(
        "commitment",
        "due_at",
        existing_type=sa.String(),
        type_=sa.DateTime(),
        nullable=True,
        postgresql_using="NULLIF(due_at, '')::timestamp",
    )

    op.create_table(
        "party_role",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("party_id", sa.String(), sa.ForeignKey("party.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("default_location_id", sa.String(), sa.ForeignKey("location.id")),
        sa.UniqueConstraint("tenant_id", "party_id", "role"),
    )
    op.create_index("ix_party_role_tenant_id", "party_role", ["tenant_id"])
    op.create_index("ix_party_role_party_id", "party_role", ["party_id"])
    op.execute(
        "INSERT INTO party_role (id, tenant_id, party_id, role) "
        "SELECT 'pro_' || id, tenant_id, id, type FROM party"
    )


def downgrade() -> None:
    op.drop_table("party_role")
    for table, columns in (
        ("commitment", ("priority", "cancelled_at")),
        ("document_line", ("line_type", "requested_at", "unit")),
        (
            "document",
            (
                "ship_to_party_id",
                "payment_term_code",
                "sales_channel",
                "customer_reference",
                "requested_delivery_at",
                "ordered_at",
            ),
        ),
        ("location", ("source_record_id", "parent_location_id", "allows_stock")),
        (
            "item",
            (
                "lead_time_days",
                "conversion_factor",
                "purchase_unit",
                "default_location_id",
                "tracking_type",
                "item_type",
            ),
        ),
        (
            "party",
            (
                "tax_identifier",
                "credit_limit",
                "default_currency",
                "payment_term_code",
                "accounting_code",
            ),
        ),
    ):
        for column in columns:
            op.drop_column(table, column)
