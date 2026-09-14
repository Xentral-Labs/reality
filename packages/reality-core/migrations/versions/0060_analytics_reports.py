"""Private analytics definitions; no computed business results are stored."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0060_analytics_reports"
down_revision = "0059_foreign_key_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analytics_report",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "owner_user_id", sa.String(), sa.ForeignKey("app_user.id"), nullable=False
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("definition", JSONB(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("create_request_id", sa.String(128), nullable=False),
        sa.Column("create_payload_hash", sa.String(64), nullable=False),
        sa.Column("last_request_id", sa.String(128), nullable=False),
        sa.Column("last_payload_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "id", name="uq_analytics_report_tenant"),
        sa.UniqueConstraint(
            "tenant_id",
            "owner_user_id",
            "create_request_id",
            name="uq_analytics_report_create",
        ),
        sa.CheckConstraint("revision > 0", name="ck_analytics_report_revision"),
        sa.CheckConstraint(
            "length(trim(name)) BETWEEN 1 AND 120", name="ck_analytics_report_name"
        ),
    )
    op.create_index(
        "ix_analytics_report_owner",
        "analytics_report",
        ["tenant_id", "owner_user_id", "id"],
    )
    op.create_index(
        "ix_analytics_report_owner_user_id",
        "analytics_report",
        ["owner_user_id"],
    )


def downgrade():
    count = op.get_bind().scalar(sa.text("SELECT count(*) FROM analytics_report"))
    if count:
        raise RuntimeError(
            "Retain saved reports when rolling back application code; do not drop their data."
        )
    op.drop_table("analytics_report")
