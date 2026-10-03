"""External stock statements: stock someone outside states, compared not taken over (spec 344).

Revision ID: 0133_external_stock
Revises: 0132_receipt_deviations
"""

import sqlalchemy as sa
from alembic import op

revision = "0133_external_stock"
down_revision = "0132_receipt_deviations"
branch_labels = None
depends_on = None

TABLE = "external_stock_statement"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("location_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("stated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reporter_party_id", sa.String(), nullable=True),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "item_id"], ["item.tenant_id", "item.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "location_id"], ["location.tenant_id", "location.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reporter_party_id"], ["party.tenant_id", "party.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.CheckConstraint(
            "quantity >= 0", name="ck_external_stock_statement_quantity"
        ),
    )
    op.create_index(f"ix_{TABLE}_tenant_id", TABLE, ["tenant_id"])
    op.create_index(
        f"ix_{TABLE}_item_location",
        TABLE,
        ["tenant_id", "item_id", "location_id", "stated_at"],
    )
    op.create_index(f"ix_{TABLE}_location_id", TABLE, ["tenant_id", "location_id"])
    op.create_index(
        f"ix_{TABLE}_reporter_party_id", TABLE, ["tenant_id", "reporter_party_id"]
    )
    op.create_index(
        f"ix_{TABLE}_source_record_id", TABLE, ["tenant_id", "source_record_id"]
    )


def downgrade() -> None:
    held = op.get_bind().execute(sa.text(f"SELECT count(*) FROM {TABLE}")).scalar()
    if held:
        raise RuntimeError(f"{held} {TABLE} rows are recorded; they cannot be removed.")
    op.drop_table(TABLE)
