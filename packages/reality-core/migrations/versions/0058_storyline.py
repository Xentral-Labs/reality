"""Storyline mode (spec 182): Fact recording order, run and step markers, trace and library.

Every addition is filtered or joined by a read the specification names. The
downgrade refuses while any run carries a storyline, so history is never dropped
silently; archive or restart those runs first.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0058_storyline"
down_revision = "0057_projection_jobs"
branch_labels = None
depends_on = None


def upgrade():
    # Fact: when it was written down, distinct from when it was true.
    op.add_column(
        "fact",
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE fact SET recorded_at = observed_at WHERE recorded_at IS NULL")
    op.alter_column(
        "fact",
        "recorded_at",
        nullable=False,
        server_default=sa.text("now()"),
    )
    op.create_index("ix_fact_tenant_recorded", "fact", ["tenant_id", "recorded_at"])

    # Run: which storyline, which version, which branches were chosen.
    op.add_column(
        "playground_run", sa.Column("storyline_key", sa.String(80), nullable=True)
    )
    op.add_column(
        "playground_run", sa.Column("storyline_version", sa.Integer(), nullable=True)
    )
    op.add_column(
        "playground_run",
        sa.Column(
            "storyline_state",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
    )
    op.create_check_constraint(
        "ck_playground_run_storyline",
        "playground_run",
        "(storyline_key IS NULL) = (storyline_version IS NULL) "
        "AND (storyline_version IS NULL OR storyline_version > 0)",
    )
    op.create_check_constraint(
        "ck_playground_run_storyline_state",
        "playground_run",
        "jsonb_typeof(storyline_state) = 'object' "
        "AND octet_length(storyline_state::text) <= 8192",
    )
    op.create_index(
        "uq_playground_run_active_storyline",
        "playground_run",
        ["owner_user_id", "storyline_key"],
        unique=True,
        postgresql_where=sa.text("status = 'active' AND storyline_key IS NOT NULL"),
    )

    # Step: read chapters have no proposal; every chapter has a marker.
    op.alter_column("playground_step", "proposal_id", nullable=True)
    op.add_column(
        "playground_step",
        sa.Column("marker_sequence", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "playground_step",
        sa.Column("marker_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_playground_step_owner",
        "playground_step",
        "proposal_id IS NOT NULL OR lesson_step_key IS NOT NULL",
    )
    op.create_unique_constraint(
        "uq_playground_step_tenant_id", "playground_step", ["tenant_id", "id"]
    )

    op.create_table(
        "storyline_trace_entry",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("step_id", sa.String(), nullable=True),
        sa.Column("ordinal", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("access", sa.String(8), nullable=False),
        sa.Column("actor", sa.String(16), nullable=False),
        sa.Column("proposal_id", sa.String(), nullable=True),
        sa.Column("marker_sequence", sa.BigInteger(), nullable=True),
        sa.Column("marker_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("before_exceptions", postgresql.JSONB(), nullable=True),
        sa.Column("input", postgresql.JSONB(), nullable=True),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "run_id"],
            ["playground_run.tenant_id", "playground_run.id"],
            name="fk_storyline_trace_run",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "step_id"],
            ["playground_step.tenant_id", "playground_step.id"],
            name="fk_storyline_trace_step",
        ),
        sa.UniqueConstraint("run_id", "ordinal", name="uq_storyline_trace_ordinal"),
        sa.CheckConstraint(
            "kind IN ('view', 'read', 'propose', 'confirm', 'reject', 'error')",
            name="ck_storyline_trace_kind",
        ),
        sa.CheckConstraint(
            "access IN ('read', 'propose', 'confirm')", name="ck_storyline_trace_access"
        ),
        sa.CheckConstraint(
            "input IS NULL OR octet_length(input::text) <= 16384",
            name="ck_storyline_trace_input",
        ),
        sa.CheckConstraint(
            "result IS NULL OR octet_length(result::text) <= 16384",
            name="ck_storyline_trace_result",
        ),
        sa.CheckConstraint(
            "before_exceptions IS NULL OR octet_length(before_exceptions::text) <= 16384",
            name="ck_storyline_trace_before",
        ),
    )
    op.create_index(
        "ix_storyline_trace_entry_tenant_id", "storyline_trace_entry", ["tenant_id"]
    )
    op.create_index(
        "ix_storyline_trace_run_ordinal",
        "storyline_trace_entry",
        ["tenant_id", "run_id", "ordinal"],
    )
    op.create_index(
        "ix_storyline_trace_step", "storyline_trace_entry", ["tenant_id", "step_id"]
    )

    op.create_table(
        "storyline_package",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "owner_user_id", sa.String(), sa.ForeignKey("app_user.id"), nullable=False
        ),
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("author", sa.String(200), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("document", postgresql.JSONB(), nullable=False),
        sa.Column(
            "validation", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("replaced_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("version > 0", name="ck_storyline_package_version"),
        sa.CheckConstraint(
            "jsonb_typeof(document) = 'object' AND octet_length(document::text) <= 200000",
            name="ck_storyline_package_document",
        ),
    )
    op.create_index(
        "ix_storyline_package_owner_user_id", "storyline_package", ["owner_user_id"]
    )
    op.create_index(
        "uq_storyline_package_owner_key_version",
        "storyline_package",
        ["owner_user_id", "key", "version"],
        unique=True,
        postgresql_where=sa.text("replaced_at IS NULL"),
    )


def downgrade():
    bind = op.get_bind()
    if bind.scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM playground_run WHERE storyline_key IS NOT NULL)"
        )
    ):
        raise RuntimeError(
            "Storyline runs exist; archive or restart them before downgrading, "
            "or retain the additive schema during code rollback."
        )
    if bind.scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM playground_step WHERE proposal_id IS NULL)"
        )
    ):
        raise RuntimeError(
            "Steps without a proposal exist; proposal_id cannot be made required."
        )
    op.drop_index(
        "uq_storyline_package_owner_key_version", table_name="storyline_package"
    )
    op.drop_index("ix_storyline_package_owner_user_id", table_name="storyline_package")
    op.drop_table("storyline_package")
    op.drop_index("ix_storyline_trace_step", table_name="storyline_trace_entry")
    op.drop_index("ix_storyline_trace_run_ordinal", table_name="storyline_trace_entry")
    op.drop_index(
        "ix_storyline_trace_entry_tenant_id", table_name="storyline_trace_entry"
    )
    op.drop_table("storyline_trace_entry")
    op.drop_constraint(
        "uq_playground_step_tenant_id", "playground_step", type_="unique"
    )
    op.drop_constraint("ck_playground_step_owner", "playground_step", type_="check")
    op.drop_column("playground_step", "marker_at")
    op.drop_column("playground_step", "marker_sequence")
    op.alter_column("playground_step", "proposal_id", nullable=False)
    op.drop_index("uq_playground_run_active_storyline", table_name="playground_run")
    op.drop_constraint(
        "ck_playground_run_storyline_state", "playground_run", type_="check"
    )
    op.drop_constraint("ck_playground_run_storyline", "playground_run", type_="check")
    op.drop_column("playground_run", "storyline_state")
    op.drop_column("playground_run", "storyline_version")
    op.drop_column("playground_run", "storyline_key")
    op.drop_index("ix_fact_tenant_recorded", table_name="fact")
    op.drop_column("fact", "recorded_at")
