"""Record every interaction with a company's model for the engine room (spec 266).

Revision ID: 0094_engine_room_interaction
Revises: 0093_decision_trail
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0094_engine_room_interaction"
down_revision = "0093_decision_trail"
branch_labels = None
depends_on = None

INDEXES = [
    ("ix_interaction_tenant_id", ("tenant_id",)),
    ("ix_interaction_actor_user_id", ("actor_user_id",)),
    ("ix_interaction_cursor", ("tenant_id", "cursor")),
    ("ix_interaction_recorded", ("tenant_id", "recorded_at")),
    ("ix_interaction_correlation", ("tenant_id", "correlation_id")),
    (
        "ix_interaction_events",
        ("tenant_id", "event_first_sequence", "event_last_sequence"),
    ),
    ("ix_interaction_mcp_token_id", ("tenant_id", "mcp_token_id")),
    ("ix_interaction_proposal_id", ("tenant_id", "proposal_id")),
]


def upgrade() -> None:
    op.create_table(
        "interaction",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("cursor", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("operation", sa.String(200), nullable=False),
        sa.Column("outcome", sa.String(24), nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("actor_user_id", sa.String(), nullable=True),
        sa.Column("mcp_token_id", sa.String(), nullable=True),
        sa.Column("job_id", sa.String(), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("proposal_id", sa.String(), nullable=True),
        sa.Column("event_first_sequence", sa.BigInteger(), nullable=True),
        sa.Column("event_last_sequence", sa.BigInteger(), nullable=True),
        sa.Column("event_ranges", postgresql.JSONB(none_as_null=True), nullable=True),
        sa.Column("refresh", sa.Boolean(), nullable=False),
        sa.Column("summary", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["actor_user_id"], ["app_user.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "mcp_token_id"],
            ["mcp_access_token.tenant_id", "mcp_access_token.id"],
            name="fk_interaction_mcp_token",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "proposal_id"],
            ["action.tenant_id", "action.id"],
            name="fk_interaction_proposal",
        ),
        sa.UniqueConstraint("cursor", name="uq_interaction_cursor"),
        sa.CheckConstraint(
            "channel IN ('web', 'mcp', 'chat', 'cli', 'worker')",
            name="ck_interaction_channel",
        ),
        sa.CheckConstraint(
            "kind IN ('read', 'propose', 'decide', 'job')",
            name="ck_interaction_kind",
        ),
        sa.CheckConstraint(
            "outcome IN ('ok', 'refused', 'failed', 'awaiting_decision')",
            name="ck_interaction_outcome",
        ),
        sa.CheckConstraint(
            "octet_length(summary::text) <= 1024", name="ck_interaction_summary"
        ),
    )
    for name, columns in INDEXES:
        op.create_index(name, "interaction", list(columns))


def downgrade() -> None:
    for name, _ in INDEXES:
        op.drop_index(name, table_name="interaction")
    op.drop_table("interaction")
