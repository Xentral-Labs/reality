"""Add the tenant-scoped encrypted secret vault.

Revision ID: 0026_secret_vault
Revises: 0025_user_language
"""

import sqlalchemy as sa
from alembic import op

revision = "0026_secret_vault"
down_revision = "0025_user_language"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "secret",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False, server_default=""),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("nonce", sa.Text(), nullable=False),
        sa.Column("encrypted_data_key", sa.Text(), nullable=False),
        sa.Column("key_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("fingerprint", sa.String(), nullable=False, server_default=""),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("rotated_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_secret_tenant_id", "secret", ["tenant_id"])
    op.create_index("ix_secret_purpose", "secret", ["purpose"])
    op.create_index("ix_secret_status", "secret", ["status"])
    op.create_table(
        "secret_audit_event",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("secret_id", sa.String(), sa.ForeignKey("secret.id"), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_secret_audit_event_tenant_id", "secret_audit_event", ["tenant_id"])
    op.create_index("ix_secret_audit_event_secret_id", "secret_audit_event", ["secret_id"])
    op.create_index("ix_secret_audit_event_event_type", "secret_audit_event", ["event_type"])
    op.add_column("ai_settings", sa.Column("api_key_secret_id", sa.String()))
    op.create_foreign_key(
        "fk_ai_settings_api_key_secret_id_secret",
        "ai_settings",
        "secret",
        ["api_key_secret_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_ai_settings_api_key_secret_id_secret", "ai_settings", type_="foreignkey"
    )
    op.drop_column("ai_settings", "api_key_secret_id")
    op.drop_table("secret_audit_event")
    op.drop_table("secret")
