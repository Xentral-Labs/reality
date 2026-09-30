"""Add returned customer payments and the payment-fee account role.

Revision ID: 0103_payment_returns
Revises: 0102_dunning_run
"""

import sqlalchemy as sa
from alembic import op

revision = "0103_payment_returns"
down_revision = "0102_dunning_run"
branch_labels = None
depends_on = None

_OLD_ROLES = (
    "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory',"
    "'customer_reduction','supplier_reduction','bad_debt_expense',"
    "'dunning_fee_revenue','opening_counterpart'"
)
_NEW_ROLES = (
    "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory',"
    "'customer_reduction','supplier_reduction','bad_debt_expense',"
    "'dunning_fee_revenue','payment_fee_expense','opening_counterpart'"
)


def _roles(roles: str) -> None:
    op.drop_constraint("ck_subledger_account_role", "subledger_account", type_="check")
    op.create_check_constraint(
        "ck_subledger_account_role", "subledger_account", f"role IN ({roles})"
    )


def upgrade() -> None:
    _roles(_NEW_ROLES)
    op.create_table(
        "payment_return",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("payment_document_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reference", sa.String(), nullable=False),
        sa.Column("returned_on", sa.Date(), nullable=False),
        sa.Column("fee_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("fee_bearer", sa.String(), nullable=False),
        sa.Column("ledger_reversal_id", sa.String(), nullable=True),
        sa.Column("fee_document_id", sa.String(), nullable=True),
        sa.Column("fee_charge_document_id", sa.String(), nullable=True),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "payment_document_id"], ["document.tenant_id", "document.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "ledger_reversal_id"],
            ["ledger_reversal.tenant_id", "ledger_reversal.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "fee_document_id"], ["document.tenant_id", "document.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "fee_charge_document_id"],
            ["document.tenant_id", "document.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id", "payment_document_id", name="uq_payment_return_payment"
        ),
        sa.UniqueConstraint(
            "tenant_id", "ledger_reversal_id", name="uq_payment_return_reversal"
        ),
        sa.CheckConstraint(
            "kind IN ('direct_debit_return', 'chargeback')",
            name="ck_payment_return_kind",
        ),
        sa.CheckConstraint("fee_amount >= 0", name="ck_payment_return_fee"),
        sa.CheckConstraint(
            "(fee_amount = 0 AND fee_bearer = 'none') OR "
            "(fee_amount > 0 AND fee_bearer IN ('customer', 'company'))",
            name="ck_payment_return_fee_bearer",
        ),
        sa.CheckConstraint("btrim(reason) <> ''", name="ck_payment_return_reason"),
    )
    op.create_index("ix_payment_return_tenant_id", "payment_return", ["tenant_id"])
    op.create_index(
        "ix_payment_return_fee_document_id",
        "payment_return",
        ["tenant_id", "fee_document_id"],
    )
    op.create_index(
        "ix_payment_return_fee_charge_document_id",
        "payment_return",
        ["tenant_id", "fee_charge_document_id"],
    )
    op.create_index(
        "ix_payment_return_source_record_id",
        "payment_return",
        ["tenant_id", "source_record_id"],
    )


def downgrade() -> None:
    op.drop_table("payment_return")
    _roles(_OLD_ROLES)
