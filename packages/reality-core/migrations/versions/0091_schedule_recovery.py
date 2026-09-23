"""Suspend a schedule with a recovery moment and retain a bounded failure detail.

Revision ID: 0091_schedule_recovery
Revises: 0090_supply_assignments
"""

import sqlalchemy as sa
from alembic import op

revision = "0091_schedule_recovery"
down_revision = "0090_supply_assignments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scheduled_job",
        sa.Column("resume_after", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_scheduled_job_recovery",
        "scheduled_job",
        ["tenant_id", "resume_after"],
        postgresql_where=sa.text("resume_after IS NOT NULL"),
    )
    op.add_column(
        "scheduled_job_run",
        sa.Column("failure_detail", sa.String(length=400), nullable=True),
    )
    op.create_check_constraint(
        "ck_scheduled_run_failure_detail",
        "scheduled_job_run",
        "failure_detail IS NULL OR length(failure_detail) <= 400",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_scheduled_run_failure_detail", "scheduled_job_run", type_="check"
    )
    op.drop_column("scheduled_job_run", "failure_detail")
    op.drop_index("ix_scheduled_job_recovery", table_name="scheduled_job")
    op.drop_column("scheduled_job", "resume_after")
