"""Distinguish local OS identity from email admission (spec 239)."""

import sqlalchemy as sa
from alembic import op

revision = "0063_desktop_identity"
down_revision = "0062_graph_report_model_version"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "app_user",
        sa.Column(
            "authentication_method", sa.String(), nullable=False, server_default="email"
        ),
    )
    op.create_check_constraint(
        "ck_app_user_authentication_method",
        "app_user",
        "authentication_method IN ('email', 'local_os')",
    )


def downgrade():
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM app_user WHERE authentication_method = 'local_os')"
        )
    ):
        raise RuntimeError(
            "Cannot downgrade while local OS accounts exist; restore a matched checkpoint."
        )
    op.drop_constraint("ck_app_user_authentication_method", "app_user", type_="check")
    op.drop_column("app_user", "authentication_method")
