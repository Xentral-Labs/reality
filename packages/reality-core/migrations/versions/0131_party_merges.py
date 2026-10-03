"""Party merges: a business partner stated to be a duplicate of another (spec 339).

Revision ID: 0131_party_merges
Revises: 0128_outbound_deliveries
"""

import sqlalchemy as sa
from alembic import op

revision = "0131_party_merges"
down_revision = "0128_outbound_deliveries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "party_merge",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("duplicate_party_id", sa.String(), nullable=False),
        sa.Column("surviving_party_id", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "duplicate_party_id"], ["party.tenant_id", "party.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "surviving_party_id"], ["party.tenant_id", "party.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id", "duplicate_party_id", name="uq_party_merge_duplicate"
        ),
        sa.CheckConstraint(
            "duplicate_party_id <> surviving_party_id",
            name="ck_party_merge_distinct",
        ),
    )
    op.create_index("ix_party_merge_tenant_id", "party_merge", ["tenant_id"])
    op.create_index(
        "ix_party_merge_surviving_party_id",
        "party_merge",
        ["tenant_id", "surviving_party_id"],
    )
    op.create_index(
        "ix_party_merge_source_record_id",
        "party_merge",
        ["tenant_id", "source_record_id"],
    )


def downgrade() -> None:
    stated = op.get_bind().execute(sa.text("SELECT count(*) FROM party_merge")).scalar()
    if stated:
        raise RuntimeError(f"{stated} party merges are stated; they cannot be removed.")
    op.drop_table("party_merge")
