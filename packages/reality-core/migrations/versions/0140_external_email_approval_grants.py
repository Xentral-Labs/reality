"""Recognize external email grant attribution without adding another authority."""

import sqlalchemy as sa
from alembic import op

revision = "0140_external_email_grants"
down_revision = "0139_email_business_links"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_action_decided_via_channel", "action", type_="check")
    op.create_check_constraint(
        "ck_action_decided_via_channel",
        "action",
        "decided_via_channel IS NULL OR decided_via_channel IN ('chat', 'external_grant')",
    )


def downgrade():
    if (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT count(*) FROM action WHERE decided_via_channel = 'external_grant'"
            )
        )
        .scalar()
    ):
        raise RuntimeError(
            "Recorded external approval attribution cannot be discarded."
        )
    op.drop_constraint("ck_action_decided_via_channel", "action", type_="check")
    op.create_check_constraint(
        "ck_action_decided_via_channel",
        "action",
        "decided_via_channel IS NULL OR decided_via_channel = 'chat'",
    )
