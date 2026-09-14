"""Let a lot carry the best-before date somebody stated.

Revision ID: 0045_lot_expiry
Revises: 0044_playground_returns_merge
"""

import sqlalchemy as sa
from alembic import op

revision = "0045_lot_expiry"
down_revision = "0044_playground_returns_merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A calendar date, not an instant. A best-before is a day, and storing it as
    # a timestamp would invent a time of day nobody stated. The first Date column
    # in this schema, which is a novelty worth naming and still the honest type.
    #
    # Nullable is a statement, and an ambiguous one on purpose: a lot with no
    # date says nothing about expiry, because there is no way to tell an item
    # with no shelf life from one whose label nobody read. Inventing that
    # distinction would be worse than the silence.
    #
    # No backfill. No lot states a date before this ships, so the class that
    # reads it reports nothing and every existing behaviour is untouched.
    op.add_column("lot", sa.Column("expires_at", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("lot", "expires_at")
