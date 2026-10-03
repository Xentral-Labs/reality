"""Retain explicit scoped owner mandates for named review agents (spec 355)."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0141_intake_review_mandates"
down_revision = "0140_unstated_document_totals"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "intake_review_mandate",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("grant_decision_id", sa.String(), nullable=False),
        sa.Column("agent_token_id", sa.String(), nullable=False),
        sa.Column("scope", postgresql.JSONB(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "grant_decision_id"], ["action.tenant_id", "action.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "agent_token_id"],
            ["mcp_access_token.tenant_id", "mcp_access_token.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id", "grant_decision_id", name="uq_intake_mandate_grant_decision"
        ),
        sa.CheckConstraint("revision >= 1", name="ck_intake_mandate_revision"),
        sa.CheckConstraint("expires_at > created_at", name="ck_intake_mandate_expiry"),
        sa.CheckConstraint(
            "jsonb_typeof(scope) = 'object'", name="ck_intake_mandate_scope"
        ),
    )
    for name, columns in (
        ("ix_intake_review_mandate_tenant_id", ["tenant_id"]),
        (
            "ix_intake_review_mandate_grant_decision_id",
            ["tenant_id", "grant_decision_id"],
        ),
        ("ix_intake_review_mandate_agent_token_id", ["tenant_id", "agent_token_id"]),
    ):
        op.create_index(name, "intake_review_mandate", columns)


def downgrade():
    if (
        op.get_bind()
        .execute(sa.text("SELECT 1 FROM intake_review_mandate LIMIT 1"))
        .first()
    ):
        raise RuntimeError(
            "Cannot remove retained intake review mandates; preserve actual delegation history."
        )
    op.drop_table("intake_review_mandate")
