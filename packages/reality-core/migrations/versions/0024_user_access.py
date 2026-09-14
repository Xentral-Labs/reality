"""Add human identities, access applications and tenant memberships.

Revision ID: 0024_user_access
Revises: 0023_exception_terminology
"""

import sqlalchemy as sa
from alembic import op

revision = "0024_user_access"
down_revision = "0023_exception_terminology"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("app_user", sa.Column("id", sa.String(), primary_key=True), sa.Column("email", sa.String(), nullable=False), sa.Column("password_hash", sa.Text(), nullable=False), sa.Column("display_name", sa.String(), nullable=False, server_default=""), sa.Column("status", sa.String(), nullable=False, server_default="email_unverified"), sa.Column("locale", sa.String(), nullable=False, server_default="en-GB"), sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"), sa.Column("is_platform_admin", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("email_verified_at", sa.DateTime(timezone=True)), sa.Column("last_login_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("email"))
    op.create_index("ix_app_user_email", "app_user", ["email"], unique=True)
    op.create_index("ix_app_user_status", "app_user", ["status"])
    op.create_table("email_verification_code", sa.Column("id", sa.String(), primary_key=True), sa.Column("user_id", sa.String(), sa.ForeignKey("app_user.id"), nullable=False), sa.Column("code_hash", sa.String(64), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"), sa.Column("consumed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_email_verification_code_user_id", "email_verification_code", ["user_id"])
    op.create_table("user_session", sa.Column("id", sa.String(), primary_key=True), sa.Column("user_id", sa.String(), sa.ForeignKey("app_user.id"), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("token_hash"))
    op.create_index("ix_user_session_user_id", "user_session", ["user_id"])
    op.create_index("ix_user_session_token_hash", "user_session", ["token_hash"], unique=True)
    op.create_table("access_application", sa.Column("id", sa.String(), primary_key=True), sa.Column("user_id", sa.String(), sa.ForeignKey("app_user.id"), nullable=False), sa.Column("company_name", sa.String(), nullable=False, server_default=""), sa.Column("company_website", sa.String(), nullable=False, server_default=""), sa.Column("orders_per_day", sa.String(), nullable=False, server_default=""), sa.Column("role_title", sa.String(), nullable=False, server_default=""), sa.Column("status", sa.String(), nullable=False, server_default="pending"), sa.Column("review_note", sa.Text(), nullable=False, server_default=""), sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False), sa.Column("reviewed_at", sa.DateTime(timezone=True)), sa.Column("reviewed_by_user_id", sa.String(), sa.ForeignKey("app_user.id")), sa.UniqueConstraint("user_id"))
    op.create_index("ix_access_application_user_id", "access_application", ["user_id"])
    op.create_index("ix_access_application_status", "access_application", ["status"])
    op.create_table("tenant_membership", sa.Column("id", sa.String(), primary_key=True), sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False), sa.Column("user_id", sa.String(), sa.ForeignKey("app_user.id"), nullable=False), sa.Column("role", sa.String(), nullable=False, server_default="owner"), sa.Column("status", sa.String(), nullable=False, server_default="active"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("tenant_id", "user_id"))
    op.create_index("ix_tenant_membership_tenant_id", "tenant_membership", ["tenant_id"])
    op.create_index("ix_tenant_membership_user_id", "tenant_membership", ["user_id"])
    op.create_table("security_audit_event", sa.Column("id", sa.String(), primary_key=True), sa.Column("user_id", sa.String(), sa.ForeignKey("app_user.id")), sa.Column("actor_user_id", sa.String(), sa.ForeignKey("app_user.id")), sa.Column("event_type", sa.String(), nullable=False), sa.Column("detail", sa.Text(), nullable=False, server_default="{}"), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_security_audit_event_user_id", "security_audit_event", ["user_id"])
    op.create_index("ix_security_audit_event_actor_user_id", "security_audit_event", ["actor_user_id"])
    op.create_index("ix_security_audit_event_event_type", "security_audit_event", ["event_type"])


def downgrade() -> None:
    for table in ("security_audit_event", "tenant_membership", "access_application", "user_session", "email_verification_code", "app_user"):
        op.drop_table(table)
