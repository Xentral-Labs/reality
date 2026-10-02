"""Store default account selections on their existing accounts (spec 332)."""

import sqlalchemy as sa
from alembic import op

revision = "0118_account_defaults"
down_revision = "0117_cost_projections"
branch_labels = None
depends_on = None

# Frozen original revision-0109 storage, including exact constraint/index names.
LEGACY_DDL = [
    "\nCREATE TABLE finance_role_destination (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\trole VARCHAR NOT NULL, \n\taccount_id VARCHAR NOT NULL, \n\tCONSTRAINT finance_role_destination_pkey PRIMARY KEY (tenant_id, id), \n\tCONSTRAINT finance_role_destination_tenant_id_account_id_fkey FOREIGN KEY(tenant_id, account_id) REFERENCES subledger_account (tenant_id, id), \n\tCONSTRAINT finance_role_destination_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT finance_role_destination_tenant_id_role_key UNIQUE NULLS DISTINCT (tenant_id, role)\n)\n\n",
    "CREATE INDEX ix_finance_role_destination_account_id ON finance_role_destination (tenant_id, account_id)",
    "CREATE INDEX ix_finance_role_destination_tenant_id ON finance_role_destination (tenant_id)",
]
VIEW_DDL = "CREATE VIEW finance_role_destination AS SELECT DISTINCT default_destination_id AS id, tenant_id, role, id AS account_id FROM subledger_account WHERE default_destination_id IS NOT NULL"


def _verify(bind):
    legacy = "SELECT tenant_id,id,role,account_id FROM finance_role_destination"
    held = "SELECT tenant_id,default_destination_id,role,id FROM subledger_account WHERE default_destination_id IS NOT NULL"
    if bind.scalar(
        sa.text(
            f"SELECT EXISTS (({legacy} EXCEPT {held}) UNION ALL ({held} EXCEPT {legacy}))"
        )
    ):
        raise RuntimeError("Default account parity failed; original storage retained.")


def upgrade():
    bind = op.get_bind()
    # Match the service's account-before-destination access order before copying.
    op.execute(
        "LOCK TABLE subledger_account,finance_role_destination IN ACCESS EXCLUSIVE MODE"
    )
    if bind.scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM finance_role_destination d LEFT JOIN subledger_account a ON a.tenant_id=d.tenant_id AND a.id=d.account_id WHERE a.id IS NULL OR a.role<>d.role)"
        )
    ):
        raise RuntimeError(
            "Cannot consolidate default accounts: legacy role mismatch; original storage retained."
        )
    op.add_column(
        "subledger_account",
        sa.Column("default_destination_id", sa.String(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_account_default_destination",
        "subledger_account",
        ["tenant_id", "default_destination_id"],
    )
    op.create_index(
        "uq_account_default_role",
        "subledger_account",
        ["tenant_id", "role"],
        unique=True,
        postgresql_where=sa.text("default_destination_id IS NOT NULL"),
    )
    op.execute(
        "UPDATE subledger_account a SET default_destination_id=d.id FROM finance_role_destination d WHERE a.tenant_id=d.tenant_id AND a.id=d.account_id"
    )
    _verify(bind)
    op.drop_table("finance_role_destination")
    op.execute(VIEW_DDL)


def downgrade():
    bind = op.get_bind()
    op.execute(
        "LOCK TABLE subledger_account,finance_role_destination IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("DROP VIEW finance_role_destination")
    for sql in LEGACY_DDL:
        op.execute(sql)
    op.execute(
        "INSERT INTO finance_role_destination (tenant_id,id,role,account_id) SELECT tenant_id,default_destination_id,role,id FROM subledger_account WHERE default_destination_id IS NOT NULL"
    )
    _verify(bind)
    op.drop_index("uq_account_default_role", table_name="subledger_account")
    op.drop_constraint(
        "uq_account_default_destination", "subledger_account", type_="unique"
    )
    op.drop_column("subledger_account", "default_destination_id")
