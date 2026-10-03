"""Prepayment releases: an owner ships a prepayment order before it is paid (spec 347).

Revision ID: 0136_prepayment_releases
Revises: 0133_external_stock
"""

import sqlalchemy as sa
from alembic import op

revision = "0136_prepayment_releases"
down_revision = "0133_external_stock"
branch_labels = None
depends_on = None

TABLE = "prepayment_release"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("covered_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("action_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "document_id"], ["document.tenant_id", "document.id"]
        ),
        sa.CheckConstraint(
            "covered_amount >= 0", name="ck_prepayment_release_covered_amount"
        ),
        sa.CheckConstraint("btrim(reason) <> ''", name="ck_prepayment_release_reason"),
    )
    op.create_index(f"ix_{TABLE}_tenant_id", TABLE, ["tenant_id"])
    op.create_index(f"ix_{TABLE}_document_id", TABLE, ["tenant_id", "document_id"])


def downgrade() -> None:
    held = op.get_bind().execute(sa.text(f"SELECT count(*) FROM {TABLE}")).scalar()
    if held:
        raise RuntimeError(f"{held} {TABLE} rows are recorded; they cannot be removed.")
    op.drop_table(TABLE)
