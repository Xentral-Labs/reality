"""Record which model interpreted a saved report (spec 224).

A saved report holds the question, not its answer, so reopening it re-executes
the traversal. What a measure meant can move between model versions — a grain
corrected, an additivity rule tightened — and a report that cannot say which
meaning produced it silently changes what it reports.

`model_version` is nullable because reports saved by the configured generation
have no such version: their meaning lives in the definition itself. A graph
report always carries one, and the service refuses to save one without it.
"""

import sqlalchemy as sa
from alembic import op

revision = "0062_graph_report_model_version"
down_revision = "0061_source_system_addressing"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "analytics_report", sa.Column("model_version", sa.String(), nullable=True)
    )
    op.add_column("analytics_report", sa.Column("kind", sa.String(), nullable=True))


def downgrade():
    op.drop_column("analytics_report", "kind")
    op.drop_column("analytics_report", "model_version")
