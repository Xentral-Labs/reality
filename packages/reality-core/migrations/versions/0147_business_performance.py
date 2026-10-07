"""Disposable indexed Business detail cohorts (spec 380)."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0147_business_performance"
down_revision = "0146_shipping_plan_inputs"
branch_labels = None
depends_on = None


def upgrade():
    # Freeze this revision: later cache changes must not rewrite old upgrades.
    op.create_table(
        "business_order_row",
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("generation", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("received_sort", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_transition_at", sa.DateTime(timezone=True)),
        sa.Column("flags", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("contribution", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "generation", "document_id"),
    )
    page = ["tenant_id", "generation", "received_sort", "document_id"]
    op.create_index("ix_business_order_page", "business_order_row", page)
    op.create_index(
        "ix_business_order_clock",
        "business_order_row",
        ["tenant_id", "generation", "next_transition_at", "document_id"],
    )
    for flag in (
        "ready",
        "blocked",
        "reservation_blocked",
        "held",
        "overdue",
        "at_risk",
        "complete",
        "partial",
        "unshipped",
        "cancelled",
        "eligible",
        "received_last_hour",
        "completed_last_hour",
        "first_dispatch_sample",
        "complete_dispatch_sample",
    ):
        op.create_index(
            f"ix_business_order_{flag}",
            "business_order_row",
            page,
            postgresql_where=sa.text(f"flags @> ARRAY['{flag}']::varchar[]"),
        )
    op.create_table(
        "business_mail_row",
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("generation", sa.String(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("waiting", sa.Boolean(), nullable=False),
        sa.Column("unread", sa.Boolean(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "generation", "source_record_id"),
    )
    op.create_index(
        "ix_business_mail_page",
        "business_mail_row",
        ["tenant_id", "generation", sa.text("recorded_at DESC"), "source_record_id"],
    )
    op.create_index(
        "ix_business_mail_direction",
        "business_mail_row",
        [
            "tenant_id",
            "generation",
            "direction",
            sa.text("recorded_at DESC"),
            "source_record_id",
        ],
    )
    op.create_index(
        "ix_business_mail_waiting",
        "business_mail_row",
        ["tenant_id", "generation", sa.text("recorded_at DESC"), "source_record_id"],
        postgresql_where=sa.text("waiting"),
    )
    # Exact retained reply identity lookup; no payload scan for every message.
    for field in ("message_id", "in_reply_to"):
        op.execute(
            sa.text(
                f"CREATE INDEX ix_source_business_{field} ON source_record "
                f"(tenant_id, source_system, source_type, md5((payload::jsonb)->>'{field}'))"
            )
        )
    op.create_index(
        "ix_source_business_scan",
        "source_record",
        ["tenant_id", "id"],
        postgresql_where=sa.text(
            "(source_type = 'email_message' AND (payload::jsonb)->>'direction' IN ('incoming','outgoing','inbound','outbound')) OR (source_system LIKE 'company/_simulator:%' ESCAPE '/' AND (source_type = 'incoming' OR (source_type = 'outgoing' AND (payload::jsonb)->>'direction' IN ('incoming','outgoing','inbound','outbound'))))"
        ),
    )
    op.create_index(
        "ix_document_business_scan",
        "document",
        ["tenant_id", "id"],
        postgresql_where=sa.text("type = 'sales_order'"),
    )


def downgrade():
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM scheduled_job_run WHERE job_type = 'projections.refresh' "
            "AND status IN ('pending','running','retrying','unresolved') "
            "AND configuration->'arguments'->'names' @> '[\"business_performance\"]'::jsonb)"
        )
    ):
        raise RuntimeError("Drain Business projection jobs before removing caches.")
    op.execute(
        "DELETE FROM projection_row WHERE projection_name = 'business_performance'"
    )
    op.execute(
        "DELETE FROM projection_checkpoint WHERE projection_name = 'business_performance'"
    )
    op.drop_index("ix_document_business_scan", table_name="document")
    op.drop_index("ix_source_business_scan", table_name="source_record")
    for field in ("message_id", "in_reply_to"):
        op.drop_index(f"ix_source_business_{field}", table_name="source_record")
    op.drop_table("business_mail_row")
    op.drop_table("business_order_row")
