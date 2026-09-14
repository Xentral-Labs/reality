"""Let an invoice line name the order line it bills.

Revision ID: 0037_invoice_order_link
Revises: 0036_erp_interpretation_rules
"""

import sqlalchemy as sa
from alembic import op

revision = "0037_invoice_order_link"
down_revision = "0036_erp_interpretation_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable by design: a line may bill something no order promised, and the
    # absence of a reference says exactly that.
    op.add_column(
        "document_line",
        sa.Column("billed_document_line_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_document_line_billed_document_line",
        "document_line",
        "document_line",
        ["billed_document_line_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_document_line_billed_document_line", "document_line", type_="foreignkey"
    )
    op.drop_column("document_line", "billed_document_line_id")
