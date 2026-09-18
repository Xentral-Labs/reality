"""A question asked now and answered later (spec 236).

Analysis answers inside one request, which is why nine of its objects refuse above
their input caps. The owner's position is that an analysis may take minutes; this
table is where such a question waits and where its answer is kept.

It is not `analytics_report`. That table holds a saved question, re-asked on every
read and therefore always current. This holds a saved answer, true of one moment
and of no other, which is why every row carries `answered_at` and `model_version`
and why `expires_at` is not optional: an answer nobody collected must stop looking
like a current figure.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0065_requested_analysis"
down_revision = "0064_analysis_document_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analysis_request",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "requested_by_user_id",
            sa.String(),
            sa.ForeignKey("app_user.id"),
            nullable=False,
        ),
        sa.Column("question", postgresql.JSONB(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.Column("deferred_reason", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False, server_default="accepted"),
        sa.Column(
            "run_id", sa.String(), sa.ForeignKey("scheduled_job_run.id"), nullable=True
        ),
        sa.Column("rows", postgresql.JSONB(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("statements", sa.Integer(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(), nullable=True),
        sa.Column("failure_message", sa.String(), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_analysis_request_tenant"),
        sa.UniqueConstraint(
            "tenant_id",
            "requested_by_user_id",
            "request_id",
            name="uq_analysis_request_idempotent",
        ),
        sa.CheckConstraint(
            "state IN ('accepted', 'running', 'ready', 'failed')",
            name="ck_analysis_request_state",
        ),
    )
    op.create_index(
        "ix_analysis_request_requester",
        "analysis_request",
        ["tenant_id", "requested_by_user_id", "id"],
    )
    op.create_index("ix_analysis_request_expiry", "analysis_request", ["expires_at"])
    op.create_index("ix_analysis_request_run_id", "analysis_request", ["run_id"])
    # Every foreign key leads an index (spec 181 FR-001). The requester index above
    # leads with the tenant, so the requester's own key needs its own.
    op.create_index(
        "ix_analysis_request_requested_by_user_id",
        "analysis_request",
        ["requested_by_user_id"],
    )


def downgrade():
    op.drop_index(
        "ix_analysis_request_requested_by_user_id", table_name="analysis_request"
    )
    op.drop_index("ix_analysis_request_run_id", table_name="analysis_request")
    op.drop_index("ix_analysis_request_expiry", table_name="analysis_request")
    op.drop_index("ix_analysis_request_requester", table_name="analysis_request")
    op.drop_table("analysis_request")
