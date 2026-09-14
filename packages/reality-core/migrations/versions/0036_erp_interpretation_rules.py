"""Add ERP-ready conditional interpretation rule fields.

Revision ID: 0036_erp_interpretation_rules
Revises: 0035_reality_gaps
"""

import sqlalchemy as sa
from alembic import op

revision = "0036_erp_interpretation_rules"
down_revision = "0035_reality_gaps"
branch_labels = None
depends_on = None


def _source_outcome_constraint_name() -> str:
    expected_columns = {"tenant_id", "rule_id", "source_record_id"}
    for constraint in sa.inspect(op.get_bind()).get_unique_constraints(
        "rule_interpretation_outcome"
    ):
        if set(constraint.get("column_names") or []) == expected_columns:
            return str(constraint["name"])
    raise RuntimeError("The source-level interpretation outcome constraint is missing.")


def upgrade() -> None:
    op.add_column(
        "interpretation_rule",
        sa.Column("conditions_mode", sa.String(), nullable=False, server_default="all"),
    )
    op.add_column(
        "interpretation_rule",
        sa.Column("conditions", sa.Text(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "interpretation_rule", sa.Column("iteration_path", sa.String(), nullable=True)
    )
    op.add_column(
        "interpretation_rule",
        sa.Column("source_line_id_path", sa.String(), nullable=True),
    )
    op.add_column(
        "interpretation_rule",
        sa.Column("output_mode", sa.String(), nullable=False, server_default="source_path"),
    )
    op.add_column(
        "interpretation_rule", sa.Column("output_path", sa.String(), nullable=True)
    )
    op.add_column(
        "interpretation_rule",
        sa.Column("output_scope", sa.String(), nullable=False, server_default="source"),
    )
    op.add_column(
        "interpretation_rule", sa.Column("constant_value", sa.Text(), nullable=True)
    )
    op.execute("UPDATE interpretation_rule SET output_path = value_path")

    op.drop_constraint(
        _source_outcome_constraint_name(),
        "rule_interpretation_outcome",
        type_="unique",
    )
    op.add_column(
        "rule_interpretation_outcome",
        sa.Column("element_key", sa.String(), nullable=False, server_default=""),
    )
    op.create_unique_constraint(
        "uq_rule_outcome_source_element",
        "rule_interpretation_outcome",
        ["tenant_id", "rule_id", "source_record_id", "element_key"],
    )
    op.create_index(
        "ix_rule_outcome_summary",
        "rule_interpretation_outcome",
        ["tenant_id", "rule_id", "status", "evaluated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_rule_outcome_summary", table_name="rule_interpretation_outcome")
    op.drop_constraint(
        "uq_rule_outcome_source_element",
        "rule_interpretation_outcome",
        type_="unique",
    )
    op.drop_column("rule_interpretation_outcome", "element_key")
    op.create_unique_constraint(
        "uq_rule_outcome_source",
        "rule_interpretation_outcome",
        ["tenant_id", "rule_id", "source_record_id"],
    )
    for column in (
        "constant_value",
        "output_scope",
        "output_path",
        "output_mode",
        "source_line_id_path",
        "iteration_path",
        "conditions",
        "conditions_mode",
    ):
        op.drop_column("interpretation_rule", column)
