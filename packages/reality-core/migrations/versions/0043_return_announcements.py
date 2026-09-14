"""Let a customer say goods are coming back before they arrive.

Revision ID: 0043_return_announcements
Revises: 0042_commitment_revision_quantity
"""

import sqlalchemy as sa
from alembic import op

revision = "0043_return_announcements"
down_revision = "0042_commitment_revision_quantity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A table rather than a third Commitment.type. The commitment vocabulary is
    # read in seventeen two-way branches whose `else` means supplier delivery,
    # and a third value would make every one of them wrong while most kept
    # passing their tests.
    op.create_table(
        "return_announcement",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), index=True),
        sa.Column(
            "commitment_id", sa.String(), sa.ForeignKey("commitment.id"), index=True
        ),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("reference", sa.String(), nullable=False, server_default=""),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("announced_at", sa.DateTime(timezone=True), nullable=False),
        # Nullable is a statement: the customer did not say when, which the queue
        # judges differently from a day they did state.
        sa.Column("expected_by", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    # Nullable by design, exactly as resolves_movement_id: almost every movement
    # fulfils no announcement, and goods arriving unannounced are ordinary. No
    # backfill, because no announcement exists before this ships.
    op.add_column(
        "movement",
        sa.Column("return_announcement_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_movement_return_announcement",
        "movement",
        "return_announcement",
        ["return_announcement_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_movement_return_announcement", "movement", type_="foreignkey"
    )
    op.drop_column("movement", "return_announcement_id")
    op.drop_table("return_announcement")
