"""Store business timestamps with explicit UTC timezone semantics.

Revision ID: 0008_utc_timestamps
Revises: 0007_party_delivery_holds
"""

import sqlalchemy as sa
from alembic import op

revision = "0008_utc_timestamps"
down_revision = "0007_party_delivery_holds"
branch_labels = None
depends_on = None


TIMESTAMP_COLUMNS = {
    "tenant": ("created_at",),
    "party_hold": ("created_at", "released_at"),
    "source_record": ("received_at",),
    "document": ("ordered_at", "requested_delivery_at"),
    "document_line": ("requested_at",),
    "commitment": ("due_at", "created_at", "cancelled_at"),
    "commitment_hold": ("created_at", "released_at"),
    "reservation": ("reserved_at",),
    "movement": ("occurred_at",),
    "ledger_entry": ("effective_at",),
    "settlement_allocation": ("allocated_at",),
    "fact": ("observed_at",),
    "action": ("created_at",),
    "chat_session": ("created_at", "updated_at"),
    "chat_message": ("created_at",),
}


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for table, columns in TIMESTAMP_COLUMNS.items():
        for column in columns:
            op.alter_column(
                table,
                column,
                existing_type=sa.DateTime(timezone=False),
                type_=sa.DateTime(timezone=True),
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for table, columns in reversed(TIMESTAMP_COLUMNS.items()):
        for column in columns:
            op.alter_column(
                table,
                column,
                existing_type=sa.DateTime(timezone=True),
                type_=sa.DateTime(timezone=False),
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )
