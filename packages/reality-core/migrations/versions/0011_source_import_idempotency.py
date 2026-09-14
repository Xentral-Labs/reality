"""Add durable source idempotency and retryable import jobs.

Revision ID: 0011_source_import_idempotency
Revises: 0010_pricing
"""

import hashlib
import json
import uuid

import sqlalchemy as sa
from alembic import op

revision = "0011_source_import_idempotency"
down_revision = "0010_pricing"
branch_labels = None
depends_on = None


def _payload_hash(payload: str) -> str:
    try:
        canonical = json.dumps(
            json.loads(payload),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError):
        canonical = payload
    return hashlib.sha256(canonical.encode()).hexdigest()


def upgrade() -> None:
    op.add_column("source_record", sa.Column("payload_hash", sa.String(64)))
    op.add_column("source_record", sa.Column("version", sa.Integer()))
    op.add_column(
        "source_record", sa.Column("source_version_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "source_record", sa.Column("supersedes_source_record_id", sa.String())
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT id, tenant_id, source_system, source_type, external_id, payload "
            "FROM source_record ORDER BY tenant_id, source_system, source_type, "
            "external_id, received_at, id"
        )
    ).mappings()
    versions: dict[tuple[str, str, str, str], tuple[int, str | None]] = {}
    for row in rows:
        identity = (
            row["tenant_id"],
            row["source_system"],
            row["source_type"],
            row["external_id"],
        )
        previous_version, previous_id = versions.get(identity, (0, None))
        version = previous_version + 1
        connection.execute(
            sa.text(
                "UPDATE source_record SET payload_hash=:payload_hash, version=:version, "
                "supersedes_source_record_id=:previous_id WHERE id=:id"
            ),
            {
                "payload_hash": _payload_hash(row["payload"]),
                "version": version,
                "previous_id": previous_id,
                "id": row["id"],
            },
        )
        versions[identity] = (version, row["id"])

    with op.batch_alter_table("source_record") as batch:
        batch.alter_column("payload_hash", existing_type=sa.String(64), nullable=False)
        batch.alter_column("version", existing_type=sa.Integer(), nullable=False)
        batch.create_foreign_key(
            "fk_source_record_supersedes",
            "source_record",
            ["supersedes_source_record_id"],
            ["id"],
        )
        batch.create_unique_constraint(
            "uq_source_record_identity_payload",
            [
                "tenant_id",
                "source_system",
                "source_type",
                "external_id",
                "payload_hash",
            ],
        )
        batch.create_unique_constraint(
            "uq_source_record_identity_version",
            ["tenant_id", "source_system", "source_type", "external_id", "version"],
        )

    op.create_table(
        "source_stream",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("source_system", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("current_source_record_id", sa.String()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["current_source_record_id"], ["source_record.id"]),
        sa.UniqueConstraint(
            "tenant_id",
            "source_system",
            "source_type",
            "external_id",
            name="uq_source_stream_identity",
        ),
    )
    op.create_index("ix_source_stream_tenant_id", "source_stream", ["tenant_id"])
    for identity, (_, current_id) in versions.items():
        tenant_id, source_system, source_type, external_id = identity
        connection.execute(
            sa.text(
                "INSERT INTO source_stream "
                "(id, tenant_id, source_system, source_type, external_id, "
                "current_source_record_id) VALUES "
                "(:id, :tenant_id, :source_system, :source_type, :external_id, :current_id)"
            ),
            {
                "id": f"sst_{uuid.uuid4().hex[:10]}",
                "tenant_id": tenant_id,
                "source_system": source_system,
                "source_type": source_type,
                "external_id": external_id,
                "current_id": current_id,
            },
        )
    op.create_table(
        "import_job",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_record.id"]),
        sa.UniqueConstraint(
            "tenant_id", "source_record_id", name="uq_import_job_source_record"
        ),
    )
    op.create_index("ix_import_job_tenant_id", "import_job", ["tenant_id"])
    op.create_index("ix_import_job_source_record_id", "import_job", ["source_record_id"])
    op.create_index("ix_import_job_status", "import_job", ["status"])

    with op.batch_alter_table("document") as batch:
        batch.create_unique_constraint(
            "uq_document_source_type", ["tenant_id", "source_record_id", "type"]
        )
    with op.batch_alter_table("document_line") as batch:
        batch.create_unique_constraint(
            "uq_document_line_source_line",
            ["tenant_id", "document_id", "source_line_id"],
        )
    with op.batch_alter_table("commitment") as batch:
        batch.create_unique_constraint(
            "uq_commitment_document_line_type",
            ["tenant_id", "document_line_id", "type"],
        )


def downgrade() -> None:
    with op.batch_alter_table("commitment") as batch:
        batch.drop_constraint("uq_commitment_document_line_type", type_="unique")
    with op.batch_alter_table("document_line") as batch:
        batch.drop_constraint("uq_document_line_source_line", type_="unique")
    with op.batch_alter_table("document") as batch:
        batch.drop_constraint("uq_document_source_type", type_="unique")
    op.drop_table("import_job")
    op.drop_table("source_stream")
    with op.batch_alter_table("source_record") as batch:
        batch.drop_constraint("uq_source_record_identity_version", type_="unique")
        batch.drop_constraint("uq_source_record_identity_payload", type_="unique")
        batch.drop_constraint("fk_source_record_supersedes", type_="foreignkey")
        batch.drop_column("supersedes_source_record_id")
        batch.drop_column("source_version_at")
        batch.drop_column("version")
        batch.drop_column("payload_hash")
