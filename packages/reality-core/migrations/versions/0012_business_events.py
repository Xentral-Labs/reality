"""Add the transactional business-event outbox.

Revision ID: 0012_business_events
Revises: 0011_source_import_idempotency
"""

import sqlalchemy as sa
from alembic import op

revision = "0012_business_events"
down_revision = "0011_source_import_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_event",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("subject_type", sa.String(), nullable=False),
        sa.Column("subject_id", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("source_record_id", sa.String(), nullable=True),
        sa.Column("action_id", sa.String(), nullable=True),
        sa.Column("causation_id", sa.String(), nullable=True),
        sa.Column("correlation_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_record.id"]),
        sa.ForeignKeyConstraint(["action_id"], ["action.id"]),
        sa.ForeignKeyConstraint(["causation_id"], ["business_event.id"]),
        sa.UniqueConstraint("tenant_id", "sequence"),
    )
    for column in ("tenant_id", "event_type", "subject_id"):
        op.create_index(f"ix_business_event_{column}", "business_event", [column])


def downgrade() -> None:
    op.drop_table("business_event")
