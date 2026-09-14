"""Add managed internal references without changing existing financial evidence."""

import sqlalchemy as sa
from alembic import op

revision = "0051_finance_references"
down_revision = "0050_opening_subledger"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "finance_reference",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.UniqueConstraint(
            "tenant_id", "kind", "code", name="uq_finance_reference_code"
        ),
        sa.UniqueConstraint(
            "tenant_id", "id", "kind", name="uq_finance_reference_kind_id"
        ),
        sa.CheckConstraint(
            "kind IN ('cost_center','case_code','coding_group')",
            name="ck_finance_reference_kind",
        ),
        sa.CheckConstraint(
            "state IN ('active','blocked')", name="ck_finance_reference_state"
        ),
        sa.CheckConstraint("revision > 0", name="ck_finance_reference_revision"),
        sa.CheckConstraint(
            "length(trim(code)) > 0 AND length(trim(name)) > 0",
            name="ck_finance_reference_labels",
        ),
    )
    op.create_index(
        "ix_finance_reference_tenant_id", "finance_reference", ["tenant_id"]
    )


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM finance_reference)")):
        raise RuntimeError(
            "Reference history exists; downgrade would discard its identity."
        )
    op.drop_table("finance_reference")
