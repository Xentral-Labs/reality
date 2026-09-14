"""Introduce required account identities for a clean local finance cutover."""

import sqlalchemy as sa
from alembic import op

revision = "0048_finance_accounts"
down_revision = "0047_merge_demo_lot_expiry"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM ledger_entry)")):
        raise RuntimeError(
            "Finance cutover requires an empty ledger. Recreate the explicitly selected disposable local database; no automatic deletion is performed."
        )
    op.create_table(
        "subledger_account",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "code"),
        sa.CheckConstraint("state IN ('active', 'blocked')"),
        sa.CheckConstraint(
            "role IN ('accounts_receivable','accounts_payable','cash','sales_revenue','inventory')"
        ),
    )
    op.create_index(
        "ix_subledger_account_tenant_id", "subledger_account", ["tenant_id"]
    )
    op.create_table(
        "finance_role_destination",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=False),
        sa.UniqueConstraint("tenant_id", "role"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "account_id"],
            ["subledger_account.tenant_id", "subledger_account.id"],
        ),
    )
    op.create_index(
        "ix_finance_role_destination_tenant_id",
        "finance_role_destination",
        ["tenant_id"],
    )
    op.create_table(
        "finance_state",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(),
            sa.ForeignKey("tenant.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("revision", sa.Integer(), nullable=False),
    )
    op.add_column("ledger_entry", sa.Column("account_id", sa.String(), nullable=False))
    op.create_foreign_key(
        "fk_ledger_account_tenant",
        "ledger_entry",
        "subledger_account",
        ["tenant_id", "account_id"],
        ["tenant_id", "id"],
    )
    op.create_index("ix_ledger_entry_account_id", "ledger_entry", ["account_id"])
    op.drop_column("ledger_entry", "account")


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM ledger_entry)")):
        raise RuntimeError(
            "Cannot downgrade populated finance history; use the explicit disposable rebuild workflow."
        )
    op.add_column("ledger_entry", sa.Column("account", sa.String(), nullable=False))
    op.create_index(
        "ix_ledger_entry_tenant_account",
        "ledger_entry",
        ["tenant_id", "account", "currency", "effective_at"],
    )
    op.drop_constraint("fk_ledger_account_tenant", "ledger_entry", type_="foreignkey")
    op.drop_index("ix_ledger_entry_account_id", table_name="ledger_entry")
    op.drop_column("ledger_entry", "account_id")
    op.drop_table("finance_role_destination")
    op.drop_table("finance_state")
    op.drop_table("subledger_account")
