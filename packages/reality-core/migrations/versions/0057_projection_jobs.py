"""Allow narrowly scoped internal projection jobs without false user attribution."""

import sqlalchemy as sa
from alembic import op

revision = "0057_projection_jobs"
down_revision = "0056_physical_shipments"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("scheduled_job_run", "actor_id", nullable=True)
    op.create_check_constraint(
        "ck_scheduled_run_actor",
        "scheduled_job_run",
        "(job_type = 'projections.refresh' AND actor_id IS NULL AND schedule_id IS NULL) OR (job_type <> 'projections.refresh' AND actor_id IS NOT NULL)",
    )
    op.create_index(
        "uq_projection_run_unfinished",
        "scheduled_job_run",
        ["tenant_id", "job_type"],
        unique=True,
        postgresql_where=sa.text(
            "job_type = 'projections.refresh' AND status IN ('pending','running','retry','unresolved')"
        ),
    )


def downgrade():
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM scheduled_job_run WHERE actor_id IS NULL)"
        )
    ):
        raise RuntimeError(
            "Internal job history exists; retain additive schema during code rollback."
        )
    op.drop_index("uq_projection_run_unfinished", table_name="scheduled_job_run")
    op.drop_constraint("ck_scheduled_run_actor", "scheduled_job_run", type_="check")
    op.alter_column("scheduled_job_run", "actor_id", nullable=False)
