"""Exact email dispatch authorization and actor-bound claims (spec 351)."""

import sqlalchemy as sa
from alembic import op

revision = "0134_agent_email_handoffs"
down_revision = "0133_external_stock"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_dispatch",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("proposal_id", sa.String(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("executor", sa.String(), nullable=True),
        sa.Column("claim_key", sa.String(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.UniqueConstraint(
            "tenant_id", "proposal_id", name="uq_email_dispatch_proposal"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "proposal_id"], ["action.tenant_id", "action.id"]
        ),
    )
    op.create_index("ix_email_dispatch_tenant_id", "email_dispatch", ["tenant_id"])

    op.create_table(
        "email_dispatch_receipt",
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("dispatch_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "source_record_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "dispatch_id"],
            ["email_dispatch.tenant_id", "email_dispatch.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
    )
    op.create_index(
        "ix_email_dispatch_receipt_dispatch",
        "email_dispatch_receipt",
        ["tenant_id", "dispatch_id"],
    )


def downgrade():
    if op.get_bind().execute(sa.text("SELECT count(*) FROM email_dispatch")).scalar():
        raise RuntimeError(
            "Recorded email dispatch authorizations cannot be discarded."
        )
    op.drop_table("email_dispatch_receipt")
    op.drop_table("email_dispatch")
