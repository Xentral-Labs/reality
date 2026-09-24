"""Align MCP authorization foreign-key indexes with the schema invariant.

Revision ID: 0095_mcp_authorization_indexes
Revises: 0094_mcp_user_authorization
"""

from alembic import op

revision = "0095_mcp_authorization_indexes"
down_revision = "0094_mcp_user_authorization"
branch_labels = None
depends_on = None


INDEX_DROPS = (
    (
        "ix_mcp_authorization_interaction_tenant_id",
        "mcp_authorization_interaction",
        ("tenant_id",),
    ),
    ("ix_mcp_user_credential_tenant_id", "mcp_user_credential", ("tenant_id",)),
)

INDEX_CREATES = (
    (
        "ix_mcp_client_grant_revoked_by_user_id",
        "mcp_client_grant",
        ("revoked_by_user_id",),
    ),
    (
        "ix_mcp_authorization_interaction_user_id",
        "mcp_authorization_interaction",
        ("user_id",),
    ),
    (
        "ix_mcp_authorization_interaction_grant_id",
        "mcp_authorization_interaction",
        ("tenant_id", "grant_id"),
    ),
    (
        "ix_mcp_user_credential_replaced_by_id",
        "mcp_user_credential",
        ("tenant_id", "replaced_by_id"),
    ),
)


def upgrade() -> None:
    for name, table, _columns in INDEX_DROPS:
        op.drop_index(name, table_name=table)
    for name, table, columns in INDEX_CREATES:
        op.create_index(name, table, list(columns))


def downgrade() -> None:
    for name, table, _columns in reversed(INDEX_CREATES):
        op.drop_index(name, table_name=table)
    for name, table, columns in reversed(INDEX_DROPS):
        op.create_index(name, table, list(columns))
