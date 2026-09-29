"""Add the dunning schedule and collection handovers for dunning runs.

Revision ID: 0102_dunning_run
Revises: 0101_customer_exchanges
"""

import sqlalchemy as sa
from alembic import op

revision = "0102_dunning_run"
down_revision = "0101_customer_exchanges"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dunning_schedule_level",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("wait_days", sa.Integer(), nullable=False),
        sa.Column("fee_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id", "level", name="uq_dunning_schedule_level_level"
        ),
        sa.CheckConstraint(
            "level BETWEEN 1 AND 3", name="ck_dunning_schedule_level_level"
        ),
        sa.CheckConstraint(
            "wait_days >= 0", name="ck_dunning_schedule_level_wait_days"
        ),
        sa.CheckConstraint("fee_amount >= 0", name="ck_dunning_schedule_level_fee"),
    )
    op.create_index(
        "ix_dunning_schedule_level_tenant_id", "dunning_schedule_level", ["tenant_id"]
    )
    op.create_index(
        "ix_dunning_schedule_level_source_record_id",
        "dunning_schedule_level",
        ["tenant_id", "source_record_id"],
    )
    op.create_table(
        "collection_handover",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("party_id", sa.String(), nullable=False),
        sa.Column("handover_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "party_id"], ["party.tenant_id", "party.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id", "source_record_id", name="uq_collection_handover_source"
        ),
        sa.CheckConstraint("btrim(reason) <> ''", name="ck_collection_handover_reason"),
    )
    op.create_index(
        "ix_collection_handover_tenant_id", "collection_handover", ["tenant_id"]
    )
    op.create_index(
        "ix_collection_handover_party_id",
        "collection_handover",
        ["tenant_id", "party_id"],
    )
    op.create_table(
        "collection_handover_invoice",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("handover_id", sa.String(), nullable=False),
        sa.Column("invoice_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "handover_id"],
            ["collection_handover.tenant_id", "collection_handover.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "invoice_id"], ["document.tenant_id", "document.id"]
        ),
        sa.UniqueConstraint(
            "tenant_id", "invoice_id", name="uq_collection_handover_invoice_invoice"
        ),
    )
    op.create_index(
        "ix_collection_handover_invoice_tenant_id",
        "collection_handover_invoice",
        ["tenant_id"],
    )
    op.create_index(
        "ix_collection_handover_invoice_handover_id",
        "collection_handover_invoice",
        ["tenant_id", "handover_id"],
    )


def downgrade() -> None:
    op.drop_table("collection_handover_invoice")
    op.drop_table("collection_handover")
    op.drop_table("dunning_schedule_level")
