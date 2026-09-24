"""Attribute decisions settled through MCP to their token and its issuer.

Revision ID: 0093_decision_trail
Revises: 0092_party_email_addresses
"""

import sqlalchemy as sa
from alembic import op

revision = "0093_decision_trail"
down_revision = "0092_party_email_addresses"
branch_labels = None
depends_on = None

#: The foreign-key index `index_foreign_keys` derives for the new reference, so the
#: schema-index check can account for every derived index by the revision that owns it.
INDEXES = [
    (
        "ix_action_decided_via_token_id",
        "action",
        ("tenant_id", "decided_via_token_id"),
    )
]


def upgrade() -> None:
    op.add_column(
        "mcp_access_token",
        sa.Column("created_by_user_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_mcp_access_token_created_by_user",
        "mcp_access_token",
        "app_user",
        ["created_by_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_mcp_access_token_created_by_user_id",
        "mcp_access_token",
        ["created_by_user_id"],
    )
    op.add_column(
        "action", sa.Column("decided_via_token_id", sa.String(), nullable=True)
    )
    op.create_foreign_key(
        "fk_action_decided_via_token",
        "action",
        "mcp_access_token",
        ["tenant_id", "decided_via_token_id"],
        ["tenant_id", "id"],
    )
    # Named and shaped as `index_foreign_keys` derives it: the company leads the key.
    for name, table, columns in INDEXES:
        op.create_index(name, table, list(columns))


def downgrade() -> None:
    for name, table, _ in INDEXES:
        op.drop_index(name, table_name=table)
    op.drop_constraint("fk_action_decided_via_token", "action", type_="foreignkey")
    op.drop_column("action", "decided_via_token_id")
    op.drop_index(
        "ix_mcp_access_token_created_by_user_id", table_name="mcp_access_token"
    )
    op.drop_constraint(
        "fk_mcp_access_token_created_by_user", "mcp_access_token", type_="foreignkey"
    )
    op.drop_column("mcp_access_token", "created_by_user_id")
