"""The company time zone: the zone business days are counted in (spec 349).

Revision ID: 0138_company_time_zone
Revises: 0137_supplier_item_number
"""

import sqlalchemy as sa
from alembic import op

revision = "0138_company_time_zone"
down_revision = "0137_supplier_item_number"
branch_labels = None
depends_on = None

TABLE = "company_time_zone"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("time_zone", sa.String(64), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
    )
    op.create_index(
        "ix_company_time_zone_source_record_id",
        TABLE,
        ["tenant_id", "source_record_id"],
    )


def downgrade() -> None:
    # A stated zone is a business statement: rolling back would silently move every
    # derived business day of the companies that stated one back to UTC.
    bind = op.get_bind()
    if bind.execute(sa.text(f"SELECT 1 FROM {TABLE} LIMIT 1")).first():
        raise RuntimeError(
            "company_time_zone holds stated time zones; remove them deliberately first"
        )
    op.drop_index("ix_company_time_zone_source_record_id", table_name=TABLE)
    op.drop_table(TABLE)
