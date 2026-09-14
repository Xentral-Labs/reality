"""Normalize received finance components and preserve internal assignment revisions."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0052_component_assignments"
down_revision = "0051_finance_references"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_document_line_tenant_id", "document_line", ["tenant_id", "id"]
    )
    op.create_table(
        "financial_component",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("document_id", sa.String()),
        sa.Column("document_line_id", sa.String()),
        *[
            sa.Column("stated_" + name, sa.Numeric(18, 4))
            for name in ("net", "tax", "gross", "base")
        ],
        sa.Column("currency", sa.String(), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_financial_component_tenant"),
        sa.UniqueConstraint(
            "tenant_id", "document_id", name="uq_financial_component_document"
        ),
        sa.UniqueConstraint(
            "tenant_id", "document_line_id", name="uq_financial_component_line"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["document.tenant_id", "document.id"],
            name="fk_component_document",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "document_line_id"],
            ["document_line.tenant_id", "document_line.id"],
            name="fk_component_line",
        ),
        sa.CheckConstraint(
            "(document_id IS NULL) <> (document_line_id IS NULL)",
            name="ck_component_owner",
        ),
    )
    op.create_table(
        "component_assignment_revision",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("component_id", sa.String(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("basis", sa.String(), nullable=False),
        sa.Column("case_reference_id", sa.String()),
        sa.Column("case_kind", sa.String(), nullable=False),
        sa.Column("group_reference_id", sa.String()),
        sa.Column("group_kind", sa.String(), nullable=False),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("app_user.id")),
        sa.Column("action_id", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reference_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_component_assignment_tenant"),
        sa.UniqueConstraint(
            "tenant_id",
            "component_id",
            "revision",
            name="uq_component_assignment_revision",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "component_id"],
            ["financial_component.tenant_id", "financial_component.id"],
            name="fk_assignment_component",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "action_id"],
            ["action.tenant_id", "action.id"],
            name="fk_assignment_action",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "case_reference_id", "case_kind"],
            [
                "finance_reference.tenant_id",
                "finance_reference.id",
                "finance_reference.kind",
            ],
            name="fk_assignment_case",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "group_reference_id", "group_kind"],
            [
                "finance_reference.tenant_id",
                "finance_reference.id",
                "finance_reference.kind",
            ],
            name="fk_assignment_group",
        ),
        sa.CheckConstraint(
            "case_kind='case_code' AND group_kind='coding_group'",
            name="ck_assignment_kinds",
        ),
        sa.CheckConstraint(
            "basis IN ('net','gross','base') AND revision>0",
            name="ck_assignment_basis_revision",
        ),
    )
    op.create_table(
        "component_assignment_part",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("assignment_revision_id", sa.String(), nullable=False),
        sa.Column("cost_center_reference_id", sa.String(), nullable=False),
        sa.Column("reference_kind", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "assignment_revision_id",
            "cost_center_reference_id",
            name="uq_assignment_center",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assignment_revision_id"],
            [
                "component_assignment_revision.tenant_id",
                "component_assignment_revision.id",
            ],
            name="fk_assignment_part_revision",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "cost_center_reference_id", "reference_kind"],
            [
                "finance_reference.tenant_id",
                "finance_reference.id",
                "finance_reference.kind",
            ],
            name="fk_assignment_part_center",
        ),
        sa.CheckConstraint(
            "reference_kind='cost_center' AND amount>0",
            name="ck_assignment_part_amount_kind",
        ),
    )
    for table, fields in [
        ("financial_component", ["tenant_id"]),
        ("component_assignment_revision", ["tenant_id", "component_id"]),
        ("component_assignment_part", ["tenant_id", "assignment_revision_id"]),
    ]:
        for field in fields:
            op.create_index(f"ix_{table}_{field}", table, [field])


def downgrade():
    if op.get_bind().scalar(
        sa.text("SELECT EXISTS (SELECT 1 FROM financial_component)")
    ):
        raise RuntimeError(
            "Component evidence exists; downgrade would discard assignment history."
        )
    op.drop_table("component_assignment_part")
    op.drop_table("component_assignment_revision")
    op.drop_table("financial_component")
    op.drop_constraint("uq_document_line_tenant_id", "document_line", type_="unique")
