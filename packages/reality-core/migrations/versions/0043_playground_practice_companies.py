"""Keep named practice companies active independently of quick experiments."""

import sqlalchemy as sa
from alembic import op

revision = "0043_practice_companies"
down_revision = "0041_playground_main_merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "playground_run",
        sa.Column(
            "sandbox_kind", sa.String(16), nullable=False, server_default="temporary"
        ),
    )
    op.create_check_constraint(
        "ck_playground_run_kind",
        "playground_run",
        "sandbox_kind IN ('temporary', 'practice')",
    )
    op.drop_index("uq_playground_run_active_owner", table_name="playground_run")
    op.create_index(
        "uq_playground_run_active_owner",
        "playground_run",
        ["owner_user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active' AND sandbox_kind = 'temporary'"),
    )


def downgrade() -> None:
    if (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT 1 FROM playground_run WHERE sandbox_kind = 'practice' LIMIT 1"
            )
        )
        .first()
    ):
        raise RuntimeError(
            "Practice companies exist; refuse loss of their lifecycle semantics."
        )
    op.drop_index("uq_playground_run_active_owner", table_name="playground_run")
    op.create_index(
        "uq_playground_run_active_owner",
        "playground_run",
        ["owner_user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_constraint("ck_playground_run_kind", "playground_run", type_="check")
    op.drop_column("playground_run", "sandbox_kind")
