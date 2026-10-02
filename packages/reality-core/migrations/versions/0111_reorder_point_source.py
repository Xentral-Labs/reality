"""Every reorder point names the statement it came from (spec 320).

Revision ID: 0111_reorder_point_source
Revises: 0110_payment_return_links
"""

import hashlib
import json
import uuid
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision = "0111_reorder_point_source"
down_revision = "0110_payment_return_links"
branch_labels = None
depends_on = None

SOURCE_SYSTEM = "internal_reorder_point"
# Marks a statement this migration wrote down for a point stated before the
# source was kept; the values are the row's, nothing else is claimed.
BEFORE = "recorded before spec 320"


def _plain(value) -> str:
    return f"{Decimal(value).normalize():f}"


def _evidence(bind, row) -> str:
    """The stream's statement for this point: reused if it exists, else the next version."""
    external_id = f"{row.item_id}@{row.location_id}"
    payload = {
        "item_id": row.item_id,
        "location_id": row.location_id,
        "reorder_point": _plain(row.reorder_point),
        "reorder_quantity": _plain(row.reorder_quantity),
        "statement_id": BEFORE,
    }
    digest = hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode()
    ).hexdigest()
    identity = {
        "tenant": row.tenant_id,
        "system": SOURCE_SYSTEM,
        "type": "reorder_point",
        "external": external_id,
    }
    where = (
        "tenant_id = :tenant AND source_system = :system "
        "AND source_type = :type AND external_id = :external"
    )
    existing = bind.execute(
        sa.text(f"SELECT id FROM source_record WHERE {where} AND payload_hash = :hash"),
        {**identity, "hash": digest},
    ).scalar()
    if existing:
        return existing
    stream = bind.execute(
        sa.text(
            f"SELECT id, current_source_record_id FROM source_stream WHERE {where}"
        ),
        identity,
    ).one_or_none()
    if stream is None:
        stream_id = f"sst_{uuid.uuid4().hex[:10]}"
        bind.execute(
            sa.text(
                "INSERT INTO source_stream (id, tenant_id, source_system, source_type, "
                "external_id) VALUES (:id, :tenant, :system, :type, :external)"
            ),
            {**identity, "id": stream_id},
        )
        current = None
    else:
        stream_id, current = stream
    version = bind.execute(
        sa.text(
            f"SELECT coalesce(max(version), 0) + 1 FROM source_record WHERE {where}"
        ),
        identity,
    ).scalar()
    source_id = f"src_{uuid.uuid4().hex[:10]}"
    bind.execute(
        sa.text(
            "INSERT INTO source_record (id, tenant_id, source_system, source_type, "
            "external_id, payload, payload_hash, version, supersedes_source_record_id, "
            "received_at) VALUES (:id, :tenant, :system, :type, :external, :payload, "
            ":hash, :version, :supersedes, :received_at)"
        ),
        {
            **identity,
            "id": source_id,
            "payload": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            "hash": digest,
            "version": version,
            "supersedes": current,
            "received_at": row.updated_at,
        },
    )
    bind.execute(
        sa.text(
            "UPDATE source_stream SET current_source_record_id = :source "
            "WHERE tenant_id = :tenant AND id = :stream"
        ),
        {"source": source_id, "tenant": row.tenant_id, "stream": stream_id},
    )
    return source_id


def upgrade() -> None:
    op.add_column(
        "item_reorder_point", sa.Column("source_record_id", sa.String(), nullable=True)
    )
    bind = op.get_bind()
    for row in bind.execute(
        sa.text(
            "SELECT tenant_id, id, item_id, location_id, reorder_point, "
            "reorder_quantity, updated_at FROM item_reorder_point"
        )
    ).all():
        bind.execute(
            sa.text(
                "UPDATE item_reorder_point SET source_record_id = :source "
                "WHERE tenant_id = :tenant AND id = :id"
            ),
            {"source": _evidence(bind, row), "tenant": row.tenant_id, "id": row.id},
        )
    op.alter_column("item_reorder_point", "source_record_id", nullable=False)
    op.create_foreign_key(
        None,
        "item_reorder_point",
        "source_record",
        ["tenant_id", "source_record_id"],
        ["tenant_id", "id"],
    )
    op.create_index(
        "ix_item_reorder_point_source_record_id",
        "item_reorder_point",
        ["tenant_id", "source_record_id"],
    )


def downgrade() -> None:
    # The statements stay: source records are immutable evidence.
    op.drop_index(
        "ix_item_reorder_point_source_record_id", table_name="item_reorder_point"
    )
    op.drop_column("item_reorder_point", "source_record_id")
