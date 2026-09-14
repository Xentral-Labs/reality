"""Add tenant-scoped Fact observation retry identity.

Revision ID: 0032_fact_observation_identity
Revises: 0031_chat_session_archiving
"""

import sqlalchemy as sa
from alembic import op

revision = "0032_fact_observation_identity"
down_revision = "0031_chat_session_archiving"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fact", sa.Column("request_fingerprint", sa.String()))
    op.create_unique_constraint(
        "uq_fact_tenant_request_fingerprint",
        "fact",
        ["tenant_id", "request_fingerprint"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_fact_tenant_request_fingerprint", "fact", type_="unique"
    )
    op.drop_column("fact", "request_fingerprint")
