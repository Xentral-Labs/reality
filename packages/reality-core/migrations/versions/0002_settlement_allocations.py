"""Add explicit payment-to-invoice settlement allocations.

Revision ID: 0002_settlement_allocations
Revises: 0001_initial
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_settlement_allocations"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "settlement_allocation",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "payment_ledger_entry_id",
            sa.String(),
            sa.ForeignKey("ledger_entry.id"),
            nullable=False,
        ),
        sa.Column(
            "invoice_ledger_entry_id",
            sa.String(),
            sa.ForeignKey("ledger_entry.id"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("allocated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_settlement_allocation_tenant_id", "settlement_allocation", ["tenant_id"]
    )
    op.create_index(
        "ix_settlement_allocation_payment_ledger_entry_id",
        "settlement_allocation",
        ["payment_ledger_entry_id"],
    )
    op.create_index(
        "ix_settlement_allocation_invoice_ledger_entry_id",
        "settlement_allocation",
        ["invoice_ledger_entry_id"],
    )
    # Backfill the early prototype: payment postings reused the invoice's
    # document_id. A cash sibling distinguishes payments from credits, while the
    # opposite control-account side in the invoice posting group is the target.
    op.execute(
        """
        INSERT INTO settlement_allocation
            (id, tenant_id, payment_ledger_entry_id, invoice_ledger_entry_id,
             amount, currency, allocated_at)
        SELECT 'set_legacy_' || payment.id, payment.tenant_id, payment.id,
               invoice.id, payment.amount, payment.currency, payment.effective_at
        FROM ledger_entry payment
        JOIN document document
          ON document.id = payment.document_id
         AND document.tenant_id = payment.tenant_id
        JOIN ledger_entry invoice
          ON invoice.document_id = document.id
         AND invoice.tenant_id = payment.tenant_id
         AND invoice.account = payment.account
         AND invoice.debit_credit <> payment.debit_credit
        WHERE document.type IN ('sales_invoice', 'supplier_invoice')
          AND payment.account IN ('accounts_receivable', 'accounts_payable')
          AND EXISTS (
              SELECT 1 FROM ledger_entry cash
              WHERE cash.tenant_id = payment.tenant_id
                AND cash.posting_group_id = payment.posting_group_id
                AND cash.account = 'cash'
          )
        """
    )


def downgrade() -> None:
    op.drop_table("settlement_allocation")
