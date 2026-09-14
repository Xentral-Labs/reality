"""Add reversible tenant archival.

Revision ID: 0014_tenant_lifecycle
Revises: 0013_integration_registry
"""

import sqlalchemy as sa
from alembic import op

revision = "0014_tenant_lifecycle"
down_revision = "0013_integration_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenant", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("tenant", "archived_at")
