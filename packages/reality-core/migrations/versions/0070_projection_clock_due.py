"""When a clock-driven projection could next answer differently.

`exceptions` is the one projection whose classes are judged against the moment they
are read, and it was rebuilt for every company every sixty seconds in case something
had aged. Spec 181 FR-004 asks for that selection to be made by date instead, and this
is the column it is made by: the earliest moment at which a verdict could change with
no event at all.

The cadence it replaces exists only for companies where nothing happens but time
passes — any business event re-derives the projection through its change set — so a
company with nothing dated is now looked at once a day rather than 1,440 times.

Revision ID: 0070_projection_clock_due
Revises: 0069_projection_run_per_projection
"""

import sqlalchemy as sa
from alembic import op

revision = "0070_projection_clock_due"
down_revision = "0069_projection_run_per_projection"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "projection_checkpoint",
        sa.Column("clock_due_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("projection_checkpoint", "clock_due_at")
