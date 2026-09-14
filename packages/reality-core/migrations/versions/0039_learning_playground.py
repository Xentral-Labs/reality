"""Private learning-run metadata; existing tenants remain businesses.

Revision ID: 0039_learning_playground
Revises: 0038_return_resolution
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0039_learning_playground"
down_revision = "0038_return_resolution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenant",
        sa.Column("purpose", sa.String(), nullable=False, server_default="business"),
    )
    op.create_check_constraint(
        "ck_tenant_purpose", "tenant", "purpose IN ('business', 'playground')"
    )
    op.execute("""
        CREATE FUNCTION reality_tenant_purpose_immutable() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN
            IF NEW.purpose IS DISTINCT FROM OLD.purpose THEN
                RAISE EXCEPTION 'Tenant purpose is immutable' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER tenant_purpose_immutable BEFORE UPDATE OF purpose ON tenant
        FOR EACH ROW EXECUTE FUNCTION reality_tenant_purpose_immutable();
    """)
    op.create_unique_constraint("uq_action_tenant_id", "action", ["tenant_id", "id"])
    op.create_table(
        "playground_run",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "owner_user_id", sa.String(), sa.ForeignKey("app_user.id"), nullable=False
        ),
        sa.Column("preset_key", sa.String(80), nullable=False),
        sa.Column("preset_version", sa.Integer(), nullable=False),
        sa.Column("lesson_key", sa.String(80), nullable=False),
        sa.Column("lesson_version", sa.Integer(), nullable=False),
        sa.Column("client_request_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="initializing"),
        sa.Column(
            "initialization_progress",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("initialization_error_code", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", name="uq_playground_run_tenant"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_playground_run_tenant_id"),
        sa.CheckConstraint(
            "jsonb_typeof(initialization_progress) = 'object' AND octet_length(initialization_progress::text) <= 65536",
            name="ck_playground_run_progress",
        ),
        sa.UniqueConstraint(
            "owner_user_id", "client_request_key", name="uq_playground_run_request"
        ),
        sa.CheckConstraint(
            "status IN ('initializing', 'active', 'initialization_failed', 'archived')",
            name="ck_playground_run_status",
        ),
        sa.CheckConstraint(
            "preset_version > 0 AND lesson_version > 0",
            name="ck_playground_run_versions",
        ),
        sa.CheckConstraint(
            "status != 'active' OR ready_at IS NOT NULL", name="ck_playground_run_ready"
        ),
        sa.CheckConstraint(
            "status != 'archived' OR archived_at IS NOT NULL",
            name="ck_playground_run_archived",
        ),
    )
    op.create_index("ix_playground_run_tenant_id", "playground_run", ["tenant_id"])
    op.create_index(
        "ix_playground_run_owner_user_id", "playground_run", ["owner_user_id"]
    )
    op.create_index(
        "uq_playground_run_active_owner",
        "playground_run",
        ["owner_user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "playground_step",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("request_key", sa.String(128), nullable=False),
        sa.Column("proposal_id", sa.String(), nullable=False),
        sa.Column("lesson_step_key", sa.String(80), nullable=True),
        sa.Column("before_observation", postgresql.JSONB(), nullable=True),
        sa.Column("receipt_observation", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id", "run_id"],
            ["playground_run.tenant_id", "playground_run.id"],
            name="fk_playground_step_run",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "proposal_id"],
            ["action.tenant_id", "action.id"],
            name="fk_playground_step_proposal",
        ),
        sa.UniqueConstraint("proposal_id", name="uq_playground_step_proposal"),
        sa.UniqueConstraint("run_id", "sequence", name="uq_playground_step_sequence"),
        sa.UniqueConstraint("run_id", "request_key", name="uq_playground_step_request"),
        sa.CheckConstraint("sequence > 0", name="ck_playground_step_sequence"),
        sa.CheckConstraint(
            "before_observation IS NULL OR (jsonb_typeof(before_observation) = 'object' AND octet_length(before_observation::text) <= 65536)",
            name="ck_playground_step_before",
        ),
        sa.CheckConstraint(
            "receipt_observation IS NULL OR (jsonb_typeof(receipt_observation) = 'object' AND octet_length(receipt_observation::text) <= 65536)",
            name="ck_playground_step_receipt",
        ),
    )
    op.create_index("ix_playground_step_tenant_id", "playground_step", ["tenant_id"])


def downgrade() -> None:
    # Removing purpose while sandbox data survives would remove the isolation boundary.
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM tenant WHERE purpose = 'playground') "
            "OR EXISTS (SELECT 1 FROM playground_run)"
        )
    ):
        raise RuntimeError(
            "Cannot downgrade while Playground tenants exist; disable entry and forward-fix."
        )
    op.drop_table("playground_step")
    op.drop_table("playground_run")
    op.drop_constraint("uq_action_tenant_id", "action", type_="unique")
    op.execute("DROP TRIGGER tenant_purpose_immutable ON tenant")
    op.execute("DROP FUNCTION reality_tenant_purpose_immutable()")
    op.drop_constraint("ck_tenant_purpose", "tenant", type_="check")
    op.drop_column("tenant", "purpose")
