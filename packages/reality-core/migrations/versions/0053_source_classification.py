"""Add exact source classification revisions without rewriting evidence."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0053_source_classification"
down_revision = "0052_component_assignments"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "source_classification_mapping_revision",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("source_system_id", sa.String(), nullable=False),
        sa.Column("namespace", sa.String(200), nullable=False),
        sa.Column("field_kind", sa.String(), nullable=False),
        sa.Column("source_code", sa.String(200), nullable=False),
        sa.Column("reference_id", sa.String(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("replaces_id", sa.String()),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("reference_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.String()),
        sa.Column("action_id", sa.String(), sa.ForeignKey("action.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_source_mapping_tenant"),
        sa.UniqueConstraint(
            "tenant_id",
            "source_system_id",
            "namespace",
            "field_kind",
            "source_code",
            "revision",
            name="uq_source_mapping_revision",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_system_id"],
            ["source_system.tenant_id", "source_system.id"],
            name="fk_source_mapping_system",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reference_id", "field_kind"],
            [
                "finance_reference.tenant_id",
                "finance_reference.id",
                "finance_reference.kind",
            ],
            name="fk_source_mapping_reference",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "replaces_id"],
            [
                "source_classification_mapping_revision.tenant_id",
                "source_classification_mapping_revision.id",
            ],
            name="fk_source_mapping_predecessor",
        ),
        sa.CheckConstraint(
            "field_kind IN ('case_code','coding_group')", name="ck_source_mapping_kind"
        ),
        sa.CheckConstraint(
            "state IN ('active','blocked')", name="ck_source_mapping_state"
        ),
        sa.CheckConstraint(
            "revision > 0 AND length(trim(namespace)) > 0 AND length(trim(source_code)) > 0 AND length(trim(reason)) > 0",
            name="ck_source_mapping_values",
        ),
    )
    op.create_index(
        "ix_source_classification_mapping_revision_tenant_id",
        "source_classification_mapping_revision",
        ["tenant_id"],
    )
    op.create_index(
        "uq_source_mapping_current",
        "source_classification_mapping_revision",
        ["tenant_id", "source_system_id", "namespace", "field_kind", "source_code"],
        unique=True,
        postgresql_where=sa.text("is_current"),
    )


def downgrade():
    if op.get_bind().scalar(
        sa.text("SELECT EXISTS (SELECT 1 FROM source_classification_mapping_revision)")
    ):
        raise RuntimeError(
            "Source mapping history exists; downgrade would discard decisions."
        )
    op.drop_table("source_classification_mapping_revision")
