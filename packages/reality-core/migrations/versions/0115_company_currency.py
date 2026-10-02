"""The company currency and a company-currency amount on every ledger entry (spec 309).

Revision ID: 0115_company_currency
Revises: 0114_customer_item_number
"""

import sqlalchemy as sa
from alembic import op

revision = "0115_company_currency"
down_revision = "0114_customer_item_number"
branch_labels = None
depends_on = None

_OLD_ROLES = (
    "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory',"
    "'customer_reduction','supplier_reduction','bad_debt_expense',"
    "'dunning_fee_revenue','payment_fee_expense','customer_down_payments',"
    "'opening_counterpart'"
)
_NEW_ROLES = (
    "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory',"
    "'customer_reduction','supplier_reduction','bad_debt_expense',"
    "'dunning_fee_revenue','payment_fee_expense','customer_down_payments',"
    "'exchange_difference','opening_counterpart'"
)


def _roles(roles: str) -> None:
    op.drop_constraint("ck_subledger_account_role", "subledger_account", type_="check")
    op.create_check_constraint(
        "ck_subledger_account_role", "subledger_account", f"role IN ({roles})"
    )


def upgrade() -> None:
    _roles(_NEW_ROLES)
    op.create_table(
        "company_currency",
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.CheckConstraint("currency ~ '^[A-Z]{3}$'", name="ck_company_currency_code"),
    )
    op.create_index(
        "ix_company_currency_source_record_id",
        "company_currency",
        ["tenant_id", "source_record_id"],
    )
    op.add_column(
        "ledger_entry", sa.Column("company_amount", sa.Numeric(18, 4), nullable=True)
    )
    op.add_column(
        "ledger_entry", sa.Column("exchange_rate", sa.Numeric(18, 8), nullable=True)
    )
    # Every company is in EUR until it states otherwise, and it can only state
    # otherwise before its first posting: EUR entries are their own value.
    op.execute(
        "UPDATE ledger_entry SET company_amount = amount, exchange_rate = 1 "
        "WHERE currency = 'EUR'"
    )
    op.create_check_constraint(
        "ck_ledger_entry_company_amount",
        "ledger_entry",
        "company_amount IS NULL OR company_amount >= 0",
    )
    op.create_check_constraint(
        "ck_ledger_entry_exchange_rate",
        "ledger_entry",
        "exchange_rate IS NULL OR exchange_rate > 0",
    )


def downgrade() -> None:
    converted = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT count(*) FROM ledger_entry WHERE exchange_rate <> 1 "
                "OR amount = 0"
            )
        )
        .scalar()
    )
    stated = (
        op.get_bind().execute(sa.text("SELECT count(*) FROM company_currency")).scalar()
    )
    if converted or stated:
        raise RuntimeError(
            f"{converted} converted ledger entries and {stated} company currencies "
            "exist; they cannot be removed."
        )
    # Exchange-difference accounts nothing was posted to go with their role.
    op.execute(
        "DELETE FROM finance_role_destination WHERE role = 'exchange_difference'"
    )
    op.execute(
        "DELETE FROM subledger_account a WHERE a.role = 'exchange_difference' "
        "AND NOT EXISTS (SELECT 1 FROM ledger_entry e WHERE e.tenant_id = a.tenant_id "
        "AND e.account_id = a.id)"
    )
    op.drop_constraint("ck_ledger_entry_exchange_rate", "ledger_entry", type_="check")
    op.drop_constraint("ck_ledger_entry_company_amount", "ledger_entry", type_="check")
    op.drop_column("ledger_entry", "exchange_rate")
    op.drop_column("ledger_entry", "company_amount")
    op.drop_index("ix_company_currency_source_record_id", table_name="company_currency")
    op.drop_table("company_currency")
    _roles(_OLD_ROLES)
