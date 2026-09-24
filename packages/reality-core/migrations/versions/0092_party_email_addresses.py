"""Add tenant-scoped Party email addresses.

Revision ID: 0092_party_email_addresses
Revises: 0091_schedule_recovery
"""

import sqlalchemy as sa
from alembic import op

revision = "0092_party_email_addresses"
down_revision = "0091_schedule_recovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "party_email_address",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("party_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("normalized_email", sa.String(length=320), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "party_id",
            "normalized_email",
            name="uq_party_email_address_party_email",
        ),
        sa.CheckConstraint(
            "length(label) <= 80", name="ck_party_email_address_label"
        ),
    )
    op.create_index(
        "ix_party_email_address_tenant_id",
        "party_email_address",
        ["tenant_id"],
    )
    op.create_index(
        "ix_party_email_address_normalized_email",
        "party_email_address",
        ["normalized_email"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_party_email_address_normalized_email", table_name="party_email_address"
    )
    op.drop_index("ix_party_email_address_tenant_id", table_name="party_email_address")
    op.drop_table("party_email_address")
