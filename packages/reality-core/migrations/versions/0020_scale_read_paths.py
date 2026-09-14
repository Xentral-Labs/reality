"""Index tenant-scoped operational read paths.

Revision ID: 0020_scale_read_paths
Revises: 0019_mcp_access_tokens
"""

from alembic import op

revision = "0020_scale_read_paths"
down_revision = "0019_mcp_access_tokens"
branch_labels = None
depends_on = None


INDEXES = (
    ("ix_commitment_tenant_status_due", "commitment", ["tenant_id", "status", "due_at", "id"]),
    ("ix_document_tenant_date", "document", ["tenant_id", "document_date", "id"]),
    ("ix_business_event_tenant_occurred", "business_event", ["tenant_id", "occurred_at", "sequence"]),
    ("ix_movement_tenant_occurred", "movement", ["tenant_id", "occurred_at", "id"]),
    ("ix_reservation_tenant_status_reserved", "reservation", ["tenant_id", "status", "reserved_at", "id"]),
    ("ix_ledger_entry_tenant_effective", "ledger_entry", ["tenant_id", "effective_at", "id"]),
    ("ix_ledger_entry_tenant_account", "ledger_entry", ["tenant_id", "account", "currency", "effective_at"]),
    ("ix_source_record_tenant_received", "source_record", ["tenant_id", "received_at", "id"]),
    ("ix_party_tenant_name", "party", ["tenant_id", "name", "id"]),
    ("ix_item_tenant_name", "item", ["tenant_id", "name", "id"]),
    ("ix_item_tenant_sku", "item", ["tenant_id", "sku", "id"]),
)


def upgrade() -> None:
    for name, table, columns in INDEXES:
        op.create_index(name, table, columns)


def downgrade() -> None:
    for name, table, _columns in reversed(INDEXES):
        op.drop_index(name, table_name=table)
