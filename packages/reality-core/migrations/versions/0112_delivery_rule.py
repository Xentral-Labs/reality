"""How a customer or one order wants to be delivered (spec 306).

Revision ID: 0112_delivery_rule
Revises: 0111_reorder_point_source
"""

import sqlalchemy as sa
from alembic import op

revision = "0112_delivery_rule"
down_revision = "0111_reorder_point_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "delivery_rule",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("party_id", sa.String(), nullable=True),
        sa.Column("document_id", sa.String(), nullable=True),
        sa.Column("rule", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "party_id"], ["party.tenant_id", "party.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "document_id"], ["document.tenant_id", "document.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.CheckConstraint(
            "(party_id IS NULL) <> (document_id IS NULL)",
            name="ck_delivery_rule_one_subject",
        ),
        sa.CheckConstraint(
            "rule IN ('partial_allowed', 'ship_complete', 'no_backorders')",
            name="ck_delivery_rule_rule",
        ),
        sa.CheckConstraint("btrim(reason) <> ''", name="ck_delivery_rule_reason"),
    )
    op.create_index("ix_delivery_rule_tenant_id", "delivery_rule", ["tenant_id"])
    op.create_index(
        "uq_delivery_rule_party",
        "delivery_rule",
        ["tenant_id", "party_id"],
        unique=True,
        postgresql_where=sa.text("party_id IS NOT NULL"),
    )
    op.create_index(
        "uq_delivery_rule_document",
        "delivery_rule",
        ["tenant_id", "document_id"],
        unique=True,
        postgresql_where=sa.text("document_id IS NOT NULL"),
    )
    op.create_index(
        "ix_delivery_rule_source_record_id",
        "delivery_rule",
        ["tenant_id", "source_record_id"],
    )


def downgrade() -> None:
    stated = (
        op.get_bind().execute(sa.text("SELECT count(*) FROM delivery_rule")).scalar()
    )
    if stated:
        raise RuntimeError(
            f"{stated} delivery rules are stated; they cannot be removed."
        )
    op.drop_table("delivery_rule")
