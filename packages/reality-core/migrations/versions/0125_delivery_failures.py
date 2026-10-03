"""Failed customer deliveries and the carrier-claim account role (spec 335).

Revision ID: 0125_delivery_failures
Revises: 0122_purchasing_depth
"""

import sqlalchemy as sa
from alembic import op

revision = "0125_delivery_failures"
down_revision = "0122_purchasing_depth"
branch_labels = None
depends_on = None

_OLD_ROLES = (
    "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory',"
    "'customer_reduction','supplier_reduction','bad_debt_expense',"
    "'dunning_fee_revenue','payment_fee_expense','customer_down_payments',"
    "'exchange_difference','opening_counterpart'"
)
_NEW_ROLES = (
    "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory',"
    "'customer_reduction','supplier_reduction','bad_debt_expense',"
    "'dunning_fee_revenue','payment_fee_expense','customer_down_payments',"
    "'exchange_difference','carrier_claim_income','opening_counterpart'"
)


def _roles(roles: str) -> None:
    op.drop_constraint("ck_subledger_account_role", "subledger_account", type_="check")
    op.create_check_constraint(
        "ck_subledger_account_role", "subledger_account", f"role IN ({roles})"
    )


def upgrade() -> None:
    _roles(_NEW_ROLES)
    op.create_table(
        "delivery_failure",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("shipment_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "shipment_id"], ["shipment.tenant_id", "shipment.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id", "shipment_id", name="uq_delivery_failure_shipment"
        ),
        sa.CheckConstraint(
            "kind IN ('undeliverable', 'refused', 'lost')",
            name="ck_delivery_failure_kind",
        ),
        sa.CheckConstraint("btrim(reason) <> ''", name="ck_delivery_failure_reason"),
    )
    # Companies whose accounts were set up have a default for every role; they
    # get the carrier-claim account as their default too, as setting up would.
    op.execute(
        """
        INSERT INTO subledger_account
            (id, tenant_id, code, name, role, state, revision, default_destination_id)
        SELECT 'acc_' || substr(md5(d.tenant_id || '/carrier_claim_income'), 1, 10),
               d.tenant_id, 'carrier_claim_income', 'Carrier and insurance claims',
               'carrier_claim_income', 'active', 1,
               'dest_' || substr(md5(d.tenant_id || '/carrier_claim_income'), 1, 10)
        FROM subledger_account d
        WHERE d.role = 'customer_reduction'
          AND d.default_destination_id IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM subledger_account a
            WHERE a.tenant_id = d.tenant_id
              AND (a.role = 'carrier_claim_income' OR a.code = 'carrier_claim_income')
          )
        """
    )
    op.create_index("ix_delivery_failure_tenant_id", "delivery_failure", ["tenant_id"])
    op.create_index(
        "ix_delivery_failure_source_record",
        "delivery_failure",
        ["tenant_id", "source_record_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    failures = bind.execute(sa.text("SELECT count(*) FROM delivery_failure")).scalar()
    claimed = bind.execute(
        sa.text(
            "SELECT count(*) FROM ledger_entry e JOIN subledger_account a "
            "ON a.tenant_id = e.tenant_id AND a.id = e.account_id "
            "WHERE a.role = 'carrier_claim_income'"
        )
    ).scalar()
    if failures or claimed:
        raise RuntimeError(
            f"{failures} failed deliveries and {claimed} carrier-claim postings "
            "exist; they cannot be removed."
        )
    # Carrier-claim accounts nothing was posted to go with their role.
    op.execute("DELETE FROM subledger_account WHERE role = 'carrier_claim_income'")
    op.drop_table("delivery_failure")
    _roles(_OLD_ROLES)
