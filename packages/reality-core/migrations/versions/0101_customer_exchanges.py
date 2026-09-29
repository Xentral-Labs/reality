"""Add customer exchanges: a replacement that settles a return instead of a credit.

Revision ID: 0101_customer_exchanges
Revises: 0100_business_journey_proposals
"""

import sqlalchemy as sa
from alembic import op

revision = "0101_customer_exchanges"
down_revision = "0100_business_journey_proposals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_exchange",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("return_movement_id", sa.String(), nullable=True),
        sa.Column("return_announcement_id", sa.String(), nullable=True),
        sa.Column("replacement_commitment_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "return_movement_id"],
            ["movement.tenant_id", "movement.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "return_announcement_id"],
            ["return_announcement.tenant_id", "return_announcement.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "replacement_commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.CheckConstraint(
            "(return_movement_id IS NULL) <> (return_announcement_id IS NULL)",
            name="ck_customer_exchange_one_return",
        ),
        sa.CheckConstraint(
            "quantity > 0", name="ck_customer_exchange_quantity_positive"
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "replacement_commitment_id",
            name="uq_customer_exchange_replacement",
        ),
        sa.UniqueConstraint(
            "tenant_id", "source_record_id", name="uq_customer_exchange_source"
        ),
    )
    op.create_index(
        "ix_customer_exchange_tenant_id", "customer_exchange", ["tenant_id"]
    )
    op.create_index(
        "ix_customer_exchange_return_movement_id",
        "customer_exchange",
        ["tenant_id", "return_movement_id"],
    )
    op.create_index(
        "ix_customer_exchange_return_announcement_id",
        "customer_exchange",
        ["tenant_id", "return_announcement_id"],
    )


def downgrade() -> None:
    op.drop_table("customer_exchange")
