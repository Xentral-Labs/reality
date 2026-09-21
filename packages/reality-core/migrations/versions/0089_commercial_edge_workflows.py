"""Add manual dunning evidence and dedicated commercial edge account roles.

Revision ID: 0089_commercial_edge_workflows
Revises: 0088_tenant_scoped_keys
"""

import sqlalchemy as sa
from alembic import op

revision = "0089_commercial_edge_workflows"
down_revision = "0088_tenant_scoped_keys"
branch_labels = None
depends_on = None


_OLD_ROLES = (
    "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory',"
    "'customer_reduction','supplier_reduction','opening_counterpart'"
)
_NEW_ROLES = (
    "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory',"
    "'customer_reduction','supplier_reduction','bad_debt_expense',"
    "'dunning_fee_revenue','opening_counterpart'"
)


def upgrade() -> None:
    op.drop_constraint(
        "ck_subledger_account_role", "subledger_account", type_="check"
    )
    op.create_check_constraint(
        "ck_subledger_account_role",
        "subledger_account",
        f"role IN ({_NEW_ROLES})",
    )
    op.create_table(
        "dunning_notice",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=True),
        sa.Column("party_id", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("notice_date", sa.Date(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("fee_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "document_id"),
        sa.CheckConstraint("level BETWEEN 1 AND 3", name="ck_dunning_notice_level"),
        sa.CheckConstraint(
            "fee_amount >= 0", name="ck_dunning_notice_fee_nonnegative"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "document_id"], ["document.tenant_id", "document.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "party_id"], ["party.tenant_id", "party.id"]
        ),
    )
    op.create_index("ix_dunning_notice_tenant_id", "dunning_notice", ["tenant_id"])
    op.create_table(
        "dunning_notice_invoice",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("notice_id", sa.String(), nullable=False),
        sa.Column("invoice_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "notice_id", "invoice_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "notice_id"],
            ["dunning_notice.tenant_id", "dunning_notice.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "invoice_id"], ["document.tenant_id", "document.id"]
        ),
    )
    op.create_index(
        "ix_dunning_notice_invoice_tenant_id",
        "dunning_notice_invoice",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_table("dunning_notice_invoice")
    op.drop_table("dunning_notice")
    op.drop_constraint(
        "ck_subledger_account_role", "subledger_account", type_="check"
    )
    op.create_check_constraint(
        "ck_subledger_account_role",
        "subledger_account",
        f"role IN ({_OLD_ROLES})",
    )
