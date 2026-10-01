"""Down-payment and pro-forma invoices for an order, and down-payment offsets (spec 299).

Revision ID: 0105_down_payments
Revises: 0104_line_price_optional
"""

import sqlalchemy as sa
from alembic import op

revision = "0105_down_payments"
down_revision = "0104_line_price_optional"
branch_labels = None
depends_on = None

_OLD_ROLES = (
    "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory',"
    "'customer_reduction','supplier_reduction','bad_debt_expense',"
    "'dunning_fee_revenue','payment_fee_expense','opening_counterpart'"
)
_NEW_ROLES = (
    "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory',"
    "'customer_reduction','supplier_reduction','bad_debt_expense',"
    "'dunning_fee_revenue','payment_fee_expense','customer_down_payments',"
    "'opening_counterpart'"
)


def _roles(roles: str) -> None:
    op.drop_constraint("ck_subledger_account_role", "subledger_account", type_="check")
    op.create_check_constraint(
        "ck_subledger_account_role", "subledger_account", f"role IN ({roles})"
    )


def upgrade() -> None:
    _roles(_NEW_ROLES)
    op.add_column(
        "document", sa.Column("order_document_id", sa.String(), nullable=True)
    )
    op.create_foreign_key(
        "fk_document_order_document",
        "document",
        "document",
        ["tenant_id", "order_document_id"],
        ["tenant_id", "id"],
    )
    op.create_index(
        "ix_document_order_document_id", "document", ["tenant_id", "order_document_id"]
    )
    op.create_table(
        "down_payment_offset",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("final_invoice_document_id", sa.String(), nullable=False),
        sa.Column("down_payment_document_id", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "final_invoice_document_id"],
            ["document.tenant_id", "document.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "down_payment_document_id"],
            ["document.tenant_id", "document.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.CheckConstraint("amount > 0", name="ck_down_payment_offset_amount"),
    )
    op.create_index(
        "ix_down_payment_offset_tenant_id", "down_payment_offset", ["tenant_id"]
    )
    for column in (
        "final_invoice_document_id",
        "down_payment_document_id",
        "source_record_id",
    ):
        op.create_index(
            f"ix_down_payment_offset_{column}",
            "down_payment_offset",
            ["tenant_id", column],
        )


def downgrade() -> None:
    bind = op.get_bind()
    held = bind.execute(
        sa.text(
            "SELECT count(*) FROM document WHERE type IN "
            "('down_payment_invoice','proforma_invoice')"
        )
    ).scalar()
    if held:
        raise RuntimeError(
            f"{held} down-payment or pro-forma invoices exist; they cannot be removed."
        )
    accounts = bind.execute(
        sa.text(
            "SELECT count(*) FROM subledger_account "
            "WHERE role = 'customer_down_payments'"
        )
    ).scalar()
    if accounts:
        raise RuntimeError(
            f"{accounts} received down-payment accounts exist; they cannot be removed."
        )
    op.drop_table("down_payment_offset")
    op.drop_index("ix_document_order_document_id", table_name="document")
    op.drop_constraint("fk_document_order_document", "document", type_="foreignkey")
    op.drop_column("document", "order_document_id")
    _roles(_OLD_ROLES)
