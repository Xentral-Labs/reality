"""Give the Demo Data connection its settlement schedule (feature 168)."""

import sqlalchemy as sa
from alembic import op

revision = "0055_demo_settlement_schedule"
down_revision = "0054_target_mappings"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "demo_data_connection",
        sa.Column("settlement_schedule_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_demo_connection_settlement_schedule_scope",
        "demo_data_connection",
        "scheduled_job",
        ["tenant_id", "settlement_schedule_id"],
        ["tenant_id", "id"],
    )


def downgrade():
    op.drop_constraint(
        "fk_demo_connection_settlement_schedule_scope",
        "demo_data_connection",
        type_="foreignkey",
    )
    op.drop_column("demo_data_connection", "settlement_schedule_id")
