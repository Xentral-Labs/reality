"""Add immutable streamed source artifacts.

Revision ID: 0021_source_artifacts
Revises: 0020_scale_read_paths
"""

import sqlalchemy as sa
from alembic import op

revision = "0021_source_artifacts"
down_revision = "0020_scale_read_paths"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_artifact",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attached_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "sha256", name="uq_source_artifact_content"),
    )
    op.create_index("ix_source_artifact_tenant_id", "source_artifact", ["tenant_id"])
    op.create_index("ix_source_artifact_status", "source_artifact", ["status"])
    with op.batch_alter_table("source_record") as batch:
        batch.add_column(sa.Column("source_artifact_id", sa.String(), nullable=True))
        batch.create_foreign_key(
            "fk_source_record_source_artifact_id",
            "source_artifact",
            ["source_artifact_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("source_record") as batch:
        batch.drop_constraint("fk_source_record_source_artifact_id", type_="foreignkey")
        batch.drop_column("source_artifact_id")
    op.drop_index("ix_source_artifact_status", table_name="source_artifact")
    op.drop_index("ix_source_artifact_tenant_id", table_name="source_artifact")
    op.drop_table("source_artifact")
