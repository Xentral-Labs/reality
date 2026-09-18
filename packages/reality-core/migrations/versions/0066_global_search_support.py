"""Read-only global search support over existing held fields (spec 235)."""

from alembic import op

from reality.db.search_sql import drop_search_support, install_search_support

revision = "0066_global_search_support"
down_revision = "0065_requested_analysis"
branch_labels = None
depends_on = None

def upgrade():
    from reality.db.search_indexes import install_search_indexes
    install_search_support(op.get_bind())
    install_search_indexes(op.get_bind())


def downgrade():
    from reality.db.search_indexes import drop_search_indexes
    drop_search_indexes(op.get_bind())
    drop_search_support(op.get_bind())
