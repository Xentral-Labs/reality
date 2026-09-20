"""One unfinished refresh run per projection of a company, not per company.

Spec 181 FR-004 asks that each projection of each company be its own unit of work
with its own budget, checkpoint and failure state. The checkpoint, the status and
the error were already its own; the *run* was not. Twelve projections shared one
row, so a builder that exceeded the budget failed a run that had covered several,
the others' work was recorded as failed with it, and recovery could not name one
of them.

The guard that made that so lives here: a partial unique index over
`(tenant_id, job_type)` for unfinished refresh runs. It is replaced by one that
also takes the projection the run carries, so the protection it gives — a company
whose refresh is already waiting is not queued again — is kept per projection
instead of per company.

The projection is read out of the run's own configuration
(`configuration #>> '{arguments,names,0}'`) rather than copied into a column: the
queue stays the single place that says what is already promised, and a run that
carried two projections could not be told apart by a column either.

Revision ID: 0069_projection_run_per_projection
Revises: 0068_tenant_event_progress
"""

import sqlalchemy as sa
from alembic import op

revision = "0069_projection_run_per_projection"
down_revision = "0068_tenant_event_progress"
branch_labels = None
depends_on = None

UNFINISHED = "status IN ('pending','running','retry','unresolved')"
PROJECTION = "job_type = 'projections.refresh'"
NAME = "(configuration #>> '{arguments,names,0}')"


def upgrade():
    op.drop_index("uq_projection_run_unfinished", table_name="scheduled_job_run")
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_projection_run_unfinished "
            f"ON scheduled_job_run (tenant_id, job_type, {NAME}) "
            f"WHERE {PROJECTION} AND {UNFINISHED}"
        )
    )


def downgrade():
    duplicates = op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM scheduled_job_run "
            f"WHERE {PROJECTION} AND {UNFINISHED} "
            "GROUP BY tenant_id HAVING count(*) > 1)"
        )
    )
    if duplicates:
        raise RuntimeError(
            "A company has more than one unfinished refresh run; the per-company "
            "index cannot be restored until the queue has drained."
        )
    op.drop_index("uq_projection_run_unfinished", table_name="scheduled_job_run")
    op.create_index(
        "uq_projection_run_unfinished",
        "scheduled_job_run",
        ["tenant_id", "job_type"],
        unique=True,
        postgresql_where=sa.text(f"{PROJECTION} AND {UNFINISHED}"),
    )
