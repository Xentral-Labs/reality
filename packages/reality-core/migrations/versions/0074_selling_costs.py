"""Source-backed selling decisions and frozen DB2 membership (spec 242)."""

from alembic import op
from sqlalchemy import inspect, text

revision = "0074_selling_costs"
down_revision = "0073_contribution_reviews"
branch_labels = None
depends_on = None
TABLES = [
    "cost_selling_attribution_part",
    "cost_selling_review_category",
    "cost_selling_review_member",
]
DDL = [
    """
CREATE TABLE cost_selling_attribution_part (
	attribution_revision_id VARCHAR NOT NULL, 
	document_line_id VARCHAR NOT NULL, 
	category VARCHAR NOT NULL, 
	source_share NUMERIC(18, 4) NOT NULL, 
	cost_effect INTEGER NOT NULL, 
	assignment_kind VARCHAR NOT NULL, 
	id VARCHAR NOT NULL, 
	tenant_id VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, id), 
	UNIQUE (tenant_id, attribution_revision_id, document_line_id, category), 
	FOREIGN KEY(tenant_id, attribution_revision_id) REFERENCES cost_attribution_revision (tenant_id, id), 
	FOREIGN KEY(tenant_id, document_line_id) REFERENCES document_line (tenant_id, id), 
	CONSTRAINT ck_selling_part_amount CHECK (source_share<>0 AND cost_effect IN (-1,1)), 
	CONSTRAINT ck_selling_part_kind CHECK (assignment_kind IN ('direct','allocated')), 
	CONSTRAINT ck_selling_part_category CHECK (category IN ('outbound_freight','fulfilment','packaging','payment_fee','marketplace_commission','sales_commission','other_selling')), 
	FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)

""",
    """CREATE INDEX ix_cost_selling_attribution_part_attribution_revision_id ON cost_selling_attribution_part (attribution_revision_id)""",
    """CREATE INDEX ix_cost_selling_attribution_part_document_line_id ON cost_selling_attribution_part (document_line_id)""",
    """CREATE INDEX ix_cost_selling_attribution_part_tenant_id ON cost_selling_attribution_part (tenant_id)""",
    """
CREATE TABLE cost_selling_review_category (
	review_id VARCHAR NOT NULL, 
	category VARCHAR NOT NULL, 
	disposition VARCHAR NOT NULL, 
	reason TEXT NOT NULL, 
	id VARCHAR NOT NULL, 
	tenant_id VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, id), 
	UNIQUE (tenant_id, review_id, category), 
	FOREIGN KEY(tenant_id, review_id) REFERENCES cost_contribution_review (tenant_id, id), 
	CONSTRAINT ck_selling_review_disposition CHECK (disposition IN ('evidenced','confirmed_zero','not_applicable','unresolved')), 
	CONSTRAINT ck_selling_review_category CHECK (category IN ('outbound_freight','fulfilment','packaging','payment_fee','marketplace_commission','sales_commission','other_selling')), 
	FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)

""",
    """CREATE INDEX ix_cost_selling_review_category_review_id ON cost_selling_review_category (review_id)""",
    """CREATE INDEX ix_cost_selling_review_category_tenant_id ON cost_selling_review_category (tenant_id)""",
    """
CREATE TABLE cost_selling_review_member (
	review_id VARCHAR NOT NULL, 
	part_id VARCHAR NOT NULL, 
	id VARCHAR NOT NULL, 
	tenant_id VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, id), 
	UNIQUE (tenant_id, review_id, part_id), 
	FOREIGN KEY(tenant_id, review_id) REFERENCES cost_contribution_review (tenant_id, id), 
	FOREIGN KEY(tenant_id, part_id) REFERENCES cost_selling_attribution_part (tenant_id, id), 
	FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)

""",
    """CREATE INDEX ix_cost_selling_review_member_review_id ON cost_selling_review_member (review_id)""",
    """CREATE INDEX ix_cost_selling_review_member_tenant_id ON cost_selling_review_member (tenant_id)""",
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
            raise RuntimeError("Cannot downgrade retained selling authority.")
    for name in reversed(TABLES):
        op.drop_table(name)
