"""Address a configured source system, and name the connector it came from (spec 211).

`base_url` is the external system's own interface for one configured instance. It is
configuration, never a credential and never called; it exists so a record can be opened
where it is owned.

`connector_code` replaces the association `connector_shells` reconstructs today by
testing whether an instance description starts with a connector's display name. With
the present catalog that test is ambiguous: an instance installed from
`shopify_payments` carries the description "Shopify Payments Payments source definition
· no connection", which also starts with "Shopify ", so one instance is listed under two
shells. The backfill below applies only the rules already in force — exact code, then
the longest matching display name, accepted on a single match — and leaves everything
else null, which is the state hand-created systems already have.
"""

from pathlib import Path

import sqlalchemy as sa
import yaml
from alembic import op

revision = "0061_source_system_addressing"
down_revision = "0060_analytics_reports"
branch_labels = None
depends_on = None


def _connectors() -> list[dict]:
    """Read the catalog from the package the migration ships with."""
    catalog = Path(__file__).resolve().parents[2] / "config" / "connector_catalog.yaml"
    return yaml.safe_load(catalog.read_text(encoding="utf-8"))["connectors"]


def upgrade():
    op.add_column("source_system", sa.Column("base_url", sa.Text(), nullable=True))
    op.add_column(
        "source_system", sa.Column("connector_code", sa.String(), nullable=True)
    )
    connection = op.get_bind()
    connectors = _connectors()
    codes = {connector["code"] for connector in connectors}
    rows = connection.execute(
        sa.text("SELECT id, code, description FROM source_system")
    ).all()
    # Longest display name first, so "Shopify Payments" is tested before "Shopify".
    by_name = sorted(connectors, key=lambda entry: -len(entry["name"]))
    for row in rows:
        if row.code in codes:
            resolved = row.code
        else:
            matches = [
                connector["code"]
                for connector in by_name
                if (row.description or "").startswith(f"{connector['name']} ")
            ]
            resolved = matches[0] if matches else None
        if resolved:
            connection.execute(
                sa.text(
                    "UPDATE source_system SET connector_code = :connector_code "
                    "WHERE id = :id"
                ),
                {"connector_code": resolved, "id": row.id},
            )


def downgrade():
    op.drop_column("source_system", "connector_code")
    op.drop_column("source_system", "base_url")
