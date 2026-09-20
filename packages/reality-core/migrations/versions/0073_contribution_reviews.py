"""Retained commercial revenue and reviewed DB1 scope (spec 242)."""

from alembic import op
from sqlalchemy import inspect, text

revision = "0073_contribution_reviews"
down_revision = "0072_inventory_costing"
branch_labels = None
depends_on = None
TABLES = ["cost_revenue_match_basis", "cost_contribution_review"]
DDL = [
    """
CREATE TABLE cost_revenue_match_basis (
	document_line_id VARCHAR NOT NULL,
	order_line_id VARCHAR NOT NULL,
	movement_basis_id VARCHAR NOT NULL,
	item_id VARCHAR NOT NULL,
	customer_id VARCHAR NOT NULL,
	stated_net NUMERIC(18, 4) NOT NULL,
	quantity NUMERIC(18, 4) NOT NULL,
	currency VARCHAR NOT NULL,
	base_unit VARCHAR NOT NULL,
	invoice_date DATE,
	sales_channel VARCHAR NOT NULL,
	evidence_hash VARCHAR(64) NOT NULL,
	input_schema_version INTEGER NOT NULL,
	introduced_event_id VARCHAR NOT NULL,
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (tenant_id, id),
	UNIQUE (tenant_id, document_line_id),
	UNIQUE (tenant_id, movement_basis_id),
	FOREIGN KEY(tenant_id, document_line_id) REFERENCES document_line (tenant_id, id),
	FOREIGN KEY(tenant_id, order_line_id) REFERENCES document_line (tenant_id, id),
	FOREIGN KEY(tenant_id, movement_basis_id) REFERENCES cost_movement_basis (tenant_id, id),
	FOREIGN KEY(tenant_id, item_id) REFERENCES item (tenant_id, id),
	FOREIGN KEY(tenant_id, customer_id) REFERENCES party (tenant_id, id),
	FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id),
	CONSTRAINT ck_revenue_match_basis CHECK (quantity>0 AND stated_net>=0 AND input_schema_version=1),
	FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE INDEX ix_cost_revenue_match_basis_tenant_id ON cost_revenue_match_basis (tenant_id)
""",
    """
CREATE TABLE cost_contribution_review (
	revenue_basis_id VARCHAR NOT NULL,
	inventory_member_id VARCHAR NOT NULL,
	revision INTEGER NOT NULL,
	supersedes_id VARCHAR,
	profile VARCHAR NOT NULL,
	economic_at TIMESTAMP WITH TIME ZONE NOT NULL,
	knowledge_at TIMESTAMP WITH TIME ZONE NOT NULL,
	introduced_event_id VARCHAR NOT NULL,
	event_sequence INTEGER NOT NULL,
	action_id VARCHAR NOT NULL,
	reason TEXT NOT NULL,
	content_hash VARCHAR(64) NOT NULL,
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (tenant_id, id),
	UNIQUE (tenant_id, revenue_basis_id, revision),
	UNIQUE (tenant_id, supersedes_id),
	FOREIGN KEY(tenant_id, revenue_basis_id) REFERENCES cost_revenue_match_basis (tenant_id, id),
	FOREIGN KEY(tenant_id, inventory_member_id) REFERENCES cost_inventory_member (tenant_id, id),
	FOREIGN KEY(tenant_id, supersedes_id) REFERENCES cost_contribution_review (tenant_id, id),
	FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id),
	FOREIGN KEY(tenant_id, action_id) REFERENCES action (tenant_id, id),
	CONSTRAINT ck_contribution_review CHECK (revision>0 AND profile='commercial_v1' AND event_sequence>=0),
	FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE INDEX ix_cost_contribution_review_revenue_basis_id ON cost_contribution_review (revenue_basis_id)
""",
    """
CREATE INDEX ix_cost_contribution_review_tenant_id ON cost_contribution_review (tenant_id)
""",
]


def upgrade():
    for statement in DDL:
        op.execute(statement)


def downgrade():
    connection = op.get_bind()
    tables = set(inspect(connection).get_table_names())
    for name in TABLES:
        if (
            name in tables
            and connection.execute(text(f"SELECT 1 FROM {name} LIMIT 1")).first()
        ):
            raise RuntimeError("Cannot downgrade retained contribution authority.")
    for name in reversed(TABLES):
        op.drop_table(name)
