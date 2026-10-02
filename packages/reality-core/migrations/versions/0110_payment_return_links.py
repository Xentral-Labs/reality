"""A payment return no longer stores what it caused; those records point back (spec 322).

Revision ID: 0110_payment_return_links
Revises: 0109_stock_block_resolution
"""

import sqlalchemy as sa
from alembic import op

revision = "0110_payment_return_links"
down_revision = "0109_stock_block_resolution"
branch_labels = None
depends_on = None

# What each return caused, read from the records that hold the link: the
# reversal of the payment's posting group, which can be reversed once, and the
# fee documents that carry the return's source record.
_DERIVED = """
SELECT r.tenant_id, r.id,
       (SELECT v.id FROM ledger_reversal v
         WHERE v.tenant_id = r.tenant_id
           AND v.original_posting_group_id = (
               SELECT e.posting_group_id FROM ledger_entry e
                 JOIN subledger_account a
                   ON a.tenant_id = e.tenant_id AND a.id = e.account_id
                WHERE e.tenant_id = r.tenant_id
                  AND e.document_id = r.payment_document_id
                  AND a.role = 'accounts_receivable'
                  AND e.debit_credit = 'credit'
                LIMIT 1)) AS ledger_reversal_id,
       (SELECT d.id FROM document d
         WHERE d.tenant_id = r.tenant_id AND d.source_record_id = r.source_record_id
           AND d.type = 'payment_return_fee') AS fee_document_id,
       (SELECT d.id FROM document d
         WHERE d.tenant_id = r.tenant_id AND d.source_record_id = r.source_record_id
           AND d.type = 'payment_return_fee_charge') AS fee_charge_document_id
  FROM payment_return r
"""

_LINKS = ("ledger_reversal_id", "fee_document_id", "fee_charge_document_id")


def upgrade() -> None:
    bind = op.get_bind()
    differing = bind.execute(
        sa.text(
            f"SELECT count(*) FROM payment_return r JOIN ({_DERIVED}) d "
            "ON d.tenant_id = r.tenant_id AND d.id = r.id WHERE "
            + " OR ".join(f"r.{link} IS DISTINCT FROM d.{link}" for link in _LINKS)
        )
    ).scalar()
    if differing:
        raise RuntimeError(
            f"{differing} payment returns name links their records do not confirm; "
            "they cannot be dropped."
        )
    for link in _LINKS:
        op.drop_column("payment_return", link)


def downgrade() -> None:
    for link in _LINKS:
        op.add_column("payment_return", sa.Column(link, sa.String(), nullable=True))
    op.get_bind().execute(
        sa.text(
            "UPDATE payment_return r SET "
            + ", ".join(f"{link} = d.{link}" for link in _LINKS)
            + f" FROM ({_DERIVED}) d WHERE d.tenant_id = r.tenant_id AND d.id = r.id"
        )
    )
    op.create_foreign_key(
        None,
        "payment_return",
        "ledger_reversal",
        ["tenant_id", "ledger_reversal_id"],
        ["tenant_id", "id"],
    )
    for link in ("fee_document_id", "fee_charge_document_id"):
        op.create_foreign_key(
            None, "payment_return", "document", ["tenant_id", link], ["tenant_id", "id"]
        )
        op.create_index(
            f"ix_payment_return_{link}", "payment_return", ["tenant_id", link]
        )
    op.create_unique_constraint(
        "uq_payment_return_reversal",
        "payment_return",
        ["tenant_id", "ledger_reversal_id"],
    )
