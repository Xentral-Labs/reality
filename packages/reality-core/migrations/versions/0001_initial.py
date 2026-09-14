"""Initial Source, Evidence, and Reality schema.

Revision ID: 0001_initial
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def tenant_columns():
    return [
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "tenant",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "party",
        *tenant_columns(),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_index("ix_party_tenant_id", "party", ["tenant_id"])
    op.create_table(
        "item",
        *tenant_columns(),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
    )
    op.create_index("ix_item_tenant_id", "item", ["tenant_id"])
    op.create_table(
        "location",
        *tenant_columns(),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
    )
    op.create_index("ix_location_tenant_id", "location", ["tenant_id"])
    op.create_table(
        "source_record",
        *tenant_columns(),
        sa.Column("source_system", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_source_record_tenant_id", "source_record", ["tenant_id"])
    op.create_table(
        "document",
        *tenant_columns(),
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id")),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("number", sa.String(), nullable=False),
        sa.Column("party_id", sa.String(), sa.ForeignKey("party.id")),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("gross_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("document_date", sa.String(), nullable=False),
    )
    op.create_index("ix_document_tenant_id", "document", ["tenant_id"])
    op.create_table(
        "document_line",
        *tenant_columns(),
        sa.Column(
            "document_id", sa.String(), sa.ForeignKey("document.id"), nullable=False
        ),
        sa.Column("source_line_id", sa.String()),
        sa.Column("item_id", sa.String(), sa.ForeignKey("item.id")),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("gross_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("promised_at", sa.String(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_index("ix_document_line_tenant_id", "document_line", ["tenant_id"])
    op.create_table(
        "commitment",
        *tenant_columns(),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("from_party_id", sa.String(), sa.ForeignKey("party.id")),
        sa.Column("to_party_id", sa.String(), sa.ForeignKey("party.id")),
        sa.Column("item_id", sa.String(), sa.ForeignKey("item.id")),
        sa.Column("location_id", sa.String(), sa.ForeignKey("location.id")),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("due_at", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), sa.ForeignKey("document.id")),
        sa.Column("document_line_id", sa.String(), sa.ForeignKey("document_line.id")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_commitment_tenant_id", "commitment", ["tenant_id"])
    op.create_table(
        "reservation",
        *tenant_columns(),
        sa.Column(
            "commitment_id", sa.String(), sa.ForeignKey("commitment.id"), nullable=False
        ),
        sa.Column("item_id", sa.String(), sa.ForeignKey("item.id"), nullable=False),
        sa.Column(
            "location_id", sa.String(), sa.ForeignKey("location.id"), nullable=False
        ),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reserved_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_reservation_tenant_id", "reservation", ["tenant_id"])
    op.create_table(
        "movement",
        *tenant_columns(),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), sa.ForeignKey("item.id"), nullable=False),
        sa.Column("from_location_id", sa.String(), sa.ForeignKey("location.id")),
        sa.Column("to_location_id", sa.String(), sa.ForeignKey("location.id")),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("commitment_id", sa.String(), sa.ForeignKey("commitment.id")),
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id")),
    )
    op.create_index("ix_movement_tenant_id", "movement", ["tenant_id"])
    op.create_table(
        "ledger_entry",
        *tenant_columns(),
        sa.Column("posting_group_id", sa.String(), nullable=False),
        sa.Column("account", sa.String(), nullable=False),
        sa.Column("party_id", sa.String(), sa.ForeignKey("party.id")),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("debit_credit", sa.String(), nullable=False),
        sa.Column("effective_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.String(), sa.ForeignKey("document.id")),
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id")),
    )
    op.create_index("ix_ledger_entry_tenant_id", "ledger_entry", ["tenant_id"])
    op.create_index(
        "ix_ledger_entry_posting_group_id", "ledger_entry", ["posting_group_id"]
    )
    op.create_table(
        "fact",
        *tenant_columns(),
        sa.Column("subject_type", sa.String(), nullable=False),
        sa.Column("subject_id", sa.String(), nullable=False),
        sa.Column("predicate", sa.String(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id")),
    )
    op.create_index("ix_fact_tenant_id", "fact", ["tenant_id"])
    op.create_table(
        "action",
        *tenant_columns(),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("actor_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("output", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_action_tenant_id", "action", ["tenant_id"])
    op.create_table(
        "chat_session",
        *tenant_columns(),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_chat_session_tenant_id", "chat_session", ["tenant_id"])
    op.create_table(
        "chat_message",
        *tenant_columns(),
        sa.Column(
            "session_id", sa.String(), sa.ForeignKey("chat_session.id"), nullable=False
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_chat_message_tenant_id", "chat_message", ["tenant_id"])


def downgrade() -> None:
    for table in [
        "chat_message",
        "chat_session",
        "action",
        "fact",
        "ledger_entry",
        "movement",
        "reservation",
        "commitment",
        "document_line",
        "document",
        "source_record",
        "location",
        "item",
        "party",
        "tenant",
    ]:
        op.drop_table(table)
