"""Add Reality Gap workflow and safe interpretation rules.

Revision ID: 0035_reality_gaps
Revises: 0034_decision_attribution
"""

import sqlalchemy as sa
from alembic import op

revision = "0035_reality_gaps"
down_revision = "0034_decision_attribution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reality_gap",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("intended_use", sa.Text(), nullable=False),
        sa.Column("origin", sa.String(), nullable=False),
        sa.Column("origin_reference", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("destination", sa.String(), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("request_fingerprint", sa.String(), nullable=False),
        sa.Column(
            "created_by_user_id",
            sa.String(),
            sa.ForeignKey("app_user.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "request_fingerprint"),
        sa.CheckConstraint("revision >= 1", name="ck_reality_gap_revision"),
    )
    op.create_index("ix_reality_gap_tenant_id", "reality_gap", ["tenant_id"])
    op.create_index("ix_reality_gap_status", "reality_gap", ["status"])
    op.create_index("ix_reality_gap_destination", "reality_gap", ["destination"])
    op.create_index("ix_reality_gap_origin", "reality_gap", ["origin"])
    op.create_table(
        "reality_gap_entry",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "gap_id", sa.String(), sa.ForeignKey("reality_gap.id"), nullable=False
        ),
        sa.Column("entry_type", sa.String(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("actor_type", sa.String(), nullable=False),
        sa.Column(
            "actor_user_id", sa.String(), sa.ForeignKey("app_user.id"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_reality_gap_entry_tenant_id", "reality_gap_entry", ["tenant_id"]
    )
    op.create_index("ix_reality_gap_entry_gap_id", "reality_gap_entry", ["gap_id"])
    op.create_index(
        "ix_reality_gap_entry_entry_type", "reality_gap_entry", ["entry_type"]
    )
    op.create_table(
        "interpretation_rule",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "gap_id", sa.String(), sa.ForeignKey("reality_gap.id"), nullable=False
        ),
        sa.Column("logical_name", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_system", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("value_path", sa.String(), nullable=False),
        sa.Column("predicate", sa.String(), nullable=False),
        sa.Column("subject_type", sa.String(), nullable=False),
        sa.Column("subject_resolver", sa.String(), nullable=False),
        sa.Column("value_type", sa.String(), nullable=False),
        sa.Column("allowed_values", sa.Text(), nullable=False),
        sa.Column("value_mapping", sa.Text(), nullable=False),
        sa.Column("normalization", sa.Text(), nullable=False),
        sa.Column("observed_at_mode", sa.String(), nullable=False),
        sa.Column("observed_at_path", sa.String(), nullable=True),
        sa.Column(
            "created_by_user_id",
            sa.String(),
            sa.ForeignKey("app_user.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "logical_name", "version"),
        sa.CheckConstraint("version >= 1", name="ck_interpretation_rule_version"),
    )
    op.create_index(
        "ix_interpretation_rule_tenant_id", "interpretation_rule", ["tenant_id"]
    )
    op.create_index("ix_interpretation_rule_gap_id", "interpretation_rule", ["gap_id"])
    op.create_index("ix_interpretation_rule_status", "interpretation_rule", ["status"])
    op.add_column(
        "fact",
        sa.Column(
            "interpretation_rule_id",
            sa.String(),
            sa.ForeignKey("interpretation_rule.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_fact_interpretation_rule_id", "fact", ["interpretation_rule_id"]
    )
    op.create_table(
        "rule_interpretation_outcome",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "rule_id",
            sa.String(),
            sa.ForeignKey("interpretation_rule.id"),
            nullable=False,
        ),
        sa.Column(
            "source_record_id",
            sa.String(),
            sa.ForeignKey("source_record.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("fact_id", sa.String(), sa.ForeignKey("fact.id"), nullable=True),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "rule_id",
            "source_record_id",
            name="uq_rule_outcome_source",
        ),
    )
    for name, column in (
        ("tenant_id", "tenant_id"),
        ("rule_id", "rule_id"),
        ("source_record_id", "source_record_id"),
        ("status", "status"),
    ):
        op.create_index(
            f"ix_rule_interpretation_outcome_{name}",
            "rule_interpretation_outcome",
            [column],
        )


def downgrade() -> None:
    op.drop_table("rule_interpretation_outcome")
    op.drop_index("ix_fact_interpretation_rule_id", table_name="fact")
    op.drop_column("fact", "interpretation_rule_id")
    op.drop_table("interpretation_rule")
    op.drop_table("reality_gap_entry")
    op.drop_table("reality_gap")
