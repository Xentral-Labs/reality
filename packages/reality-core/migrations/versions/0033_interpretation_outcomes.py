"""Preserve source interpretation attempt outcomes.

Revision ID: 0033_interpretation_outcomes
Revises: 0032_fact_observation_identity
"""

import sqlalchemy as sa
from alembic import op

revision = "0033_interpretation_outcomes"
down_revision = "0032_fact_observation_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interpretation_outcome",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "source_record_id",
            sa.String(),
            sa.ForeignKey("source_record.id"),
            nullable=False,
        ),
        sa.Column(
            "import_job_id", sa.String(), sa.ForeignKey("import_job.id"), nullable=False
        ),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(), nullable=False),
        sa.Column("interpreter_name", sa.String(), nullable=False, server_default=""),
        sa.Column(
            "interpreter_version", sa.String(), nullable=False, server_default="1"
        ),
        sa.Column("reason_code", sa.String(), nullable=False, server_default=""),
        sa.Column("summary", sa.String(), nullable=False, server_default=""),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "import_job_id",
            "attempt",
            name="uq_interpretation_outcome_attempt",
        ),
        sa.CheckConstraint("attempt >= 0", name="ck_interpretation_outcome_attempt"),
    )
    for column in ("tenant_id", "source_record_id", "import_job_id", "classification"):
        op.create_index(
            f"ix_interpretation_outcome_{column}", "interpretation_outcome", [column]
        )
    op.create_table(
        "interpretation_record_reference",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "outcome_id",
            sa.String(),
            sa.ForeignKey("interpretation_outcome.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("record_type", sa.String(), nullable=False),
        sa.Column("record_id", sa.String(), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "outcome_id",
            "record_type",
            "record_id",
            name="uq_interpretation_record_reference",
        ),
    )
    for column in ("tenant_id", "outcome_id"):
        op.create_index(
            f"ix_interpretation_record_reference_{column}",
            "interpretation_record_reference",
            [column],
        )


def downgrade() -> None:
    op.drop_table("interpretation_record_reference")
    op.drop_table("interpretation_outcome")
