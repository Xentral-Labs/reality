"""Explicit object membership for email evidence (spec 351 FR-013–016)."""

import sqlalchemy as sa
from alembic import op

revision = "0139_email_business_links"
down_revision = "0134_agent_email_handoffs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_business_link",
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("record_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "source_record_id", "kind", "record_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
    )
    op.create_index(
        "ix_email_business_link_object",
        "email_business_link",
        ["tenant_id", "kind", "record_id", "source_record_id"],
    )


def downgrade():
    if (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM email_business_link"))
        .scalar()
    ):
        raise RuntimeError("Recorded email business links cannot be discarded.")
    op.drop_table("email_business_link")
