"""Add declared opening coverage and residual-item evidence without rewriting history."""

import sqlalchemy as sa
from alembic import op

revision = "0050_opening_subledger"
down_revision = "0049_settlement_reduction_roles"
branch_labels = None
depends_on = None

ROLES = "'accounts_receivable','accounts_payable','cash','sales_revenue','inventory','customer_reduction','supplier_reduction'"


def upgrade():
    op.create_unique_constraint("uq_party_tenant_id", "party", ["tenant_id", "id"])
    op.create_unique_constraint(
        "uq_document_tenant_id", "document", ["tenant_id", "id"]
    )
    op.drop_constraint("ck_subledger_account_role", "subledger_account", type_="check")
    op.create_check_constraint(
        "ck_subledger_account_role",
        "subledger_account",
        f"role IN ({ROLES},'opening_counterpart')",
    )
    op.create_table(
        "opening_scope",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("source_namespace", sa.String(), nullable=False),
        sa.Column("snapshot_key", sa.String(), nullable=False),
        sa.Column("cutover_date", sa.Date(), nullable=False),
        sa.Column("coverage_kind", sa.String(), nullable=False),
        sa.Column("party_id", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_opening_scope_tenant_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "source_namespace",
            "party_id",
            "direction",
            "currency",
            name="uq_opening_scope_coverage",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
            name="fk_opening_scope_party_tenant",
        ),
        sa.CheckConstraint(
            "direction IN ('customer_debt','customer_credit','supplier_debt','supplier_credit')",
            name="ck_opening_scope_direction",
        ),
        sa.CheckConstraint(
            "coverage_kind IN ('individual','summary')", name="ck_opening_scope_kind"
        ),
    )
    op.create_index("ix_opening_scope_tenant_id", "opening_scope", ["tenant_id"])
    op.create_index("ix_opening_scope_party_id", "opening_scope", ["party_id"])
    op.create_table(
        "opening_item_detail",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("scope_id", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("external_item_key", sa.String(), nullable=False),
        sa.Column("original_due_date", sa.Date(), nullable=True),
        sa.UniqueConstraint(
            "tenant_id",
            "scope_id",
            "external_item_key",
            name="uq_opening_item_identity",
        ),
        sa.UniqueConstraint("document_id", name="uq_opening_item_document"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "scope_id"],
            ["opening_scope.tenant_id", "opening_scope.id"],
            name="fk_opening_item_scope_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["document.tenant_id", "document.id"],
            name="fk_opening_item_document_tenant",
        ),
    )
    op.create_index(
        "ix_opening_item_detail_tenant_id", "opening_item_detail", ["tenant_id"]
    )
    op.create_index(
        "ix_opening_item_detail_scope_id", "opening_item_detail", ["scope_id"]
    )


def downgrade():
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM opening_scope) OR EXISTS (SELECT 1 FROM subledger_account WHERE role='opening_counterpart')"
        )
    ):
        raise RuntimeError(
            "Opening evidence or accounts exist; downgrade would invalidate history."
        )
    op.drop_table("opening_item_detail")
    op.drop_table("opening_scope")
    op.drop_constraint("ck_subledger_account_role", "subledger_account", type_="check")
    op.create_check_constraint(
        "ck_subledger_account_role", "subledger_account", f"role IN ({ROLES})"
    )
    op.drop_constraint("uq_document_tenant_id", "document", type_="unique")
    op.drop_constraint("uq_party_tenant_id", "party", type_="unique")
