"""Payment authorizations and captures (spec 336).

Revision ID: 0126_payment_authorizations
Revises: 0125_delivery_failures
"""

import sqlalchemy as sa
from alembic import op

revision = "0126_payment_authorizations"
down_revision = "0125_delivery_failures"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_authorization",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("order_document_id", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reference", sa.String(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "order_document_id"],
            ["document.tenant_id", "document.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "order_document_id",
            "reference",
            name="uq_payment_authorization_reference",
        ),
        sa.CheckConstraint("amount > 0", name="ck_payment_authorization_amount"),
        sa.CheckConstraint(
            "expires_at > authorized_at", name="ck_payment_authorization_expiry"
        ),
        sa.CheckConstraint(
            "btrim(reference) <> ''", name="ck_payment_authorization_reference"
        ),
    )
    op.create_index(
        "ix_payment_authorization_tenant_id", "payment_authorization", ["tenant_id"]
    )
    op.create_index(
        "ix_payment_authorization_order_document_id",
        "payment_authorization",
        ["tenant_id", "order_document_id"],
    )
    op.create_index(
        "ix_payment_authorization_source_record_id",
        "payment_authorization",
        ["tenant_id", "source_record_id"],
    )
    op.create_table(
        "payment_capture",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("authorization_id", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reference", sa.String(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "authorization_id"],
            ["payment_authorization.tenant_id", "payment_authorization.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.CheckConstraint("amount > 0", name="ck_payment_capture_amount"),
    )
    op.create_index("ix_payment_capture_tenant_id", "payment_capture", ["tenant_id"])
    op.create_index(
        "ix_payment_capture_authorization_id",
        "payment_capture",
        ["tenant_id", "authorization_id"],
    )
    op.create_index(
        "ix_payment_capture_source_record_id",
        "payment_capture",
        ["tenant_id", "source_record_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    held = bind.execute(sa.text("SELECT count(*) FROM payment_authorization")).scalar()
    if held:
        raise RuntimeError(
            f"{held} payment authorizations are stated; they cannot be removed."
        )
    op.drop_table("payment_capture")
    op.drop_table("payment_authorization")
