"""Let a movement say which return it settles.

Revision ID: 0038_return_resolution
Revises: 0037_invoice_order_link
"""

import sqlalchemy as sa
from alembic import op

revision = "0038_return_resolution"
down_revision = "0037_invoice_order_link"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable by design: almost every movement settles no return, and the
    # absence of a reference says exactly that.
    op.add_column(
        "movement",
        sa.Column("resolves_movement_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_movement_resolves_movement",
        "movement",
        "movement",
        ["resolves_movement_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_movement_resolves_movement", "movement", type_="foreignkey"
    )
    op.drop_column("movement", "resolves_movement_id")
