"""Add company membership invitations and durable delivery intent.

Revision ID: 0030_company_membership_invitations
Revises: 0029_ledger_reversals
"""

import sqlalchemy as sa
from alembic import op

revision = "0030_company_membership_invitations"
down_revision = "0029_ledger_reversals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_tenant_membership_role",
        "tenant_membership",
        "role IN ('owner', 'member')",
    )
    op.create_check_constraint(
        "ck_tenant_membership_status",
        "tenant_membership",
        "status IN ('active', 'removed')",
    )
    op.add_column("security_audit_event", sa.Column("tenant_id", sa.String()))
    op.add_column("security_audit_event", sa.Column("subject_type", sa.String()))
    op.add_column("security_audit_event", sa.Column("subject_id", sa.String()))
    op.add_column("security_audit_event", sa.Column("outcome", sa.String()))
    op.create_foreign_key(
        "fk_security_audit_event_tenant_id",
        "security_audit_event",
        "tenant",
        ["tenant_id"],
        ["id"],
    )
    op.create_index(
        "ix_security_audit_event_tenant_id", "security_audit_event", ["tenant_id"]
    )
    op.create_table(
        "company_invitation",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("normalized_email", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("token_hash", sa.String(64), unique=True),
        sa.Column("token_generation", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "invited_by_user_id",
            sa.String(),
            sa.ForeignKey("app_user.id"),
            nullable=False,
        ),
        sa.Column("accepted_by_user_id", sa.String(), sa.ForeignKey("app_user.id")),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("terminal_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'revoked', 'expired')",
            name="ck_company_invitation_status",
        ),
        sa.CheckConstraint(
            "token_generation >= 1", name="ck_company_invitation_generation"
        ),
    )
    op.create_index(
        "ix_company_invitation_tenant_id", "company_invitation", ["tenant_id"]
    )
    op.create_index(
        "ix_company_invitation_invited_by_user_id",
        "company_invitation",
        ["invited_by_user_id"],
    )
    op.create_index(
        "ix_company_invitation_tenant_status",
        "company_invitation",
        ["tenant_id", "status"],
    )
    op.create_index(
        "uq_company_invitation_pending_email",
        "company_invitation",
        ["tenant_id", "normalized_email"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_table(
        "invitation_delivery",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "invitation_id",
            sa.String(),
            sa.ForeignKey("company_invitation.id"),
            nullable=False,
        ),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column(
            "template_key",
            sa.String(),
            nullable=False,
            server_default="company_invitation",
        ),
        sa.Column("locale", sa.String(), nullable=False, server_default="en"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True)),
        sa.Column("attempted_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("provider_message_id", sa.String()),
        sa.Column("last_error_code", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "invitation_id", "generation"),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'retry', 'delivered', 'failed')",
            name="ck_invitation_delivery_status",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0", name="ck_invitation_delivery_attempts"
        ),
    )
    op.create_index(
        "ix_invitation_delivery_tenant_id", "invitation_delivery", ["tenant_id"]
    )
    op.create_index(
        "ix_invitation_delivery_invitation_id", "invitation_delivery", ["invitation_id"]
    )
    op.create_index(
        "ix_invitation_delivery_due",
        "invitation_delivery",
        ["status", "next_attempt_at", "claimed_at"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    invitation_count = connection.scalar(
        sa.text("SELECT COUNT(*) FROM company_invitation")
    )
    delivery_count = connection.scalar(
        sa.text("SELECT COUNT(*) FROM invitation_delivery")
    )
    access_audit_count = connection.scalar(
        sa.text("SELECT COUNT(*) FROM security_audit_event WHERE tenant_id IS NOT NULL")
    )
    unsupported_membership_count = connection.scalar(
        sa.text(
            "SELECT COUNT(*) FROM tenant_membership "
            "WHERE role <> 'owner' OR status <> 'active'"
        )
    )
    if (
        invitation_count
        or delivery_count
        or access_audit_count
        or unsupported_membership_count
    ):
        raise RuntimeError(
            "Cannot remove company membership invitation evidence or lifecycle state."
        )

    op.drop_table("invitation_delivery")
    op.drop_table("company_invitation")
    op.drop_index(
        "ix_security_audit_event_tenant_id", table_name="security_audit_event"
    )
    op.drop_constraint(
        "fk_security_audit_event_tenant_id", "security_audit_event", type_="foreignkey"
    )
    for column in ("outcome", "subject_id", "subject_type", "tenant_id"):
        op.drop_column("security_audit_event", column)
    op.drop_constraint(
        "ck_tenant_membership_status", "tenant_membership", type_="check"
    )
    op.drop_constraint("ck_tenant_membership_role", "tenant_membership", type_="check")
