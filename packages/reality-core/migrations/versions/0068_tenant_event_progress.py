"""Carry each company's event progress on a row of its own.

`max(business_event.sequence)` answers the same question, but only one company at a
time. Spec 181 FR-004 needs it asked of every company at once — which projections of
which companies have fallen behind — and that has to be an indexed read, not ten
thousand round trips per sweep.

It is a table rather than a column on `tenant` for a reason the test suite found: every
table that references a company takes `FOR KEY SHARE` on its row for the foreign key
check, so writing that row on every business event makes any concurrent REPEATABLE READ
transaction that inserts anything fail to serialise. Nothing references this table.

Revision ID: 0068_tenant_event_progress
Revises: 0067_desktop_identity
"""

import sqlalchemy as sa
from alembic import op

revision = "0068_tenant_event_progress"
down_revision = "0067_desktop_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_event_progress",
        sa.Column(
            "tenant_id", sa.String(), sa.ForeignKey("tenant.id"), primary_key=True
        ),
        sa.Column("last_event_sequence", sa.BigInteger(), nullable=False),
    )
    # Existing companies start from where their events actually are, so no projection
    # is told that nothing has happened when something has.
    op.execute(
        """
        INSERT INTO tenant_event_progress (tenant_id, last_event_sequence)
        SELECT tenant.id,
               COALESCE((SELECT MAX(sequence) FROM business_event
                          WHERE business_event.tenant_id = tenant.id), 0)
          FROM tenant
        """
    )
    # Where the company had got to when each projection last looked. A projection's own
    # sequence counts only the events it depends on, so it sits below the company's on
    # purpose and cannot be compared against it.
    op.add_column(
        "projection_checkpoint",
        sa.Column(
            "observed_event_sequence",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
    )
    op.execute(
        """
        UPDATE projection_checkpoint
           SET observed_event_sequence = COALESCE(
                 (SELECT last_event_sequence FROM tenant_event_progress
                   WHERE tenant_event_progress.tenant_id = projection_checkpoint.tenant_id),
                 0)
        """
    )
    op.alter_column(
        "projection_checkpoint", "observed_event_sequence", server_default=None
    )
    op.create_index(
        "ix_projection_checkpoint_observed",
        "projection_checkpoint",
        ["tenant_id", "observed_event_sequence"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_projection_checkpoint_observed",
        table_name="projection_checkpoint",
        if_exists=True,
    )
    op.drop_column("projection_checkpoint", "observed_event_sequence")
    op.drop_table("tenant_event_progress")
