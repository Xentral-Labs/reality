"""Add auditable Movement correction relationships.

Revision ID: 0028_movement_corrections
Revises: 0027_access_admission_counter
"""

import sqlalchemy as sa
from alembic import op

revision = "0028_movement_corrections"
down_revision = "0027_access_admission_counter"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "movement_correction",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "original_movement_id",
            sa.String(),
            sa.ForeignKey("movement.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "compensating_movement_id",
            sa.String(),
            sa.ForeignKey("movement.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "replacement_movement_id",
            sa.String(),
            sa.ForeignKey("movement.id"),
            nullable=True,
            unique=True,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_context", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("request_fingerprint", sa.String(), nullable=False),
        sa.UniqueConstraint("tenant_id", "request_fingerprint"),
        sa.CheckConstraint(
            "original_movement_id <> compensating_movement_id",
            name="ck_movement_correction_original_compensation_distinct",
        ),
        sa.CheckConstraint(
            "replacement_movement_id IS NULL OR "
            "replacement_movement_id <> original_movement_id",
            name="ck_movement_correction_original_replacement_distinct",
        ),
        sa.CheckConstraint(
            "replacement_movement_id IS NULL OR "
            "replacement_movement_id <> compensating_movement_id",
            name="ck_movement_correction_compensation_replacement_distinct",
        ),
    )
    op.create_index(
        "ix_movement_correction_tenant_id", "movement_correction", ["tenant_id"]
    )
    op.create_index(
        "ix_movement_correction_original_movement_id",
        "movement_correction",
        ["original_movement_id"],
    )
    op.create_index(
        "ix_movement_correction_compensating_movement_id",
        "movement_correction",
        ["compensating_movement_id"],
    )
    op.create_index(
        "ix_movement_correction_replacement_movement_id",
        "movement_correction",
        ["replacement_movement_id"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    count = connection.scalar(sa.text("SELECT COUNT(*) FROM movement_correction"))
    if count:
        raise RuntimeError(
            "Cannot remove Movement correction semantics after corrections exist."
        )
    op.drop_table("movement_correction")
