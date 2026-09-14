"""Permit explicit settlement reduction counterparts without rewriting history."""

import sqlalchemy as sa
from alembic import op

revision = "0049_settlement_reduction_roles"
down_revision = "0048_finance_accounts"
branch_labels = None
depends_on = None

BASE_ROLES = (
    "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory'"
)


def upgrade():
    for constraint in sa.inspect(op.get_bind()).get_check_constraints(
        "subledger_account"
    ):
        if "role" in constraint["sqltext"]:
            op.drop_constraint(constraint["name"], "subledger_account", type_="check")
    op.create_check_constraint(
        "ck_subledger_account_role",
        "subledger_account",
        f"role IN ({BASE_ROLES},'customer_reduction','supplier_reduction')",
    )


def downgrade():
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM subledger_account WHERE role IN ('customer_reduction','supplier_reduction'))"
        )
    ):
        raise RuntimeError(
            "Reduction accounts exist; downgrade would invalidate finance history."
        )
    op.drop_constraint("ck_subledger_account_role", "subledger_account", type_="check")
    op.create_check_constraint(
        "ck_subledger_account_role", "subledger_account", f"role IN ({BASE_ROLES})"
    )
