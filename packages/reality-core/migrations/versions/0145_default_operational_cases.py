"""Version-owned resumable coordination, preserving all prior control history."""

import sqlalchemy as sa
from alembic import op

revision = "0145_default_operational_cases"
down_revision = "0144_operational_cases"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "case_rollout",
        sa.Column(
            "tenant_id", sa.String(), sa.ForeignKey("tenant.id"), primary_key=True
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("commitment_after", sa.String(), nullable=True),
        sa.Column("return_after", sa.String(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version = 377", name="ck_case_rollout_version"),
        sa.CheckConstraint(
            "completed_at IS NULL OR (commitment_after IS NULL AND return_after IS NULL)",
            name="ck_case_rollout_completion",
        ),
    )
    op.drop_constraint("ck_scheduled_run_actor", "scheduled_job_run", type_="check")
    op.create_check_constraint(
        "ck_scheduled_run_actor",
        "scheduled_job_run",
        "(job_type IN ('projections.refresh', 'operational_cases.reconcile') AND actor_id IS NULL AND schedule_id IS NULL) OR (job_type <> 'projections.refresh' AND actor_id IS NOT NULL)",
    )
    op.create_index(
        "ix_scheduled_run_claim_history", "scheduled_job_run",
        ["tenant_id", "started_at", "id"],
        postgresql_where=sa.text("started_at IS NOT NULL"),
    )


def downgrade():
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM operational_case) OR EXISTS (SELECT 1 FROM case_rollout) OR EXISTS "
            "(SELECT 1 FROM scheduled_job_run WHERE job_type = 'operational_cases.reconcile' AND actor_id IS NULL)"
        )
    ):
        raise RuntimeError(
            "Preserve version rollout and actual operational case control history before downgrade."
        )
    op.drop_index("ix_scheduled_run_claim_history", table_name="scheduled_job_run")
    op.drop_constraint("ck_scheduled_run_actor", "scheduled_job_run", type_="check")
    op.create_check_constraint(
        "ck_scheduled_run_actor",
        "scheduled_job_run",
        "(job_type = 'projections.refresh' AND actor_id IS NULL AND schedule_id IS NULL) OR (job_type <> 'projections.refresh' AND actor_id IS NOT NULL)",
    )
    op.drop_table("case_rollout")
