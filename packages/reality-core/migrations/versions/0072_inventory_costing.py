"""Confirmed bounded inventory authority and retained inputs (spec 242)."""

from alembic import op
from sqlalchemy import inspect, text

revision = "0072_inventory_costing"
down_revision = "0071_receipt_costing"
branch_labels = None
depends_on = None
TABLES = [
    "cost_policy_revision",
    "cost_inventory_review",
    "cost_movement_basis",
    "cost_ownership_revision",
    "cost_inventory_member",
]
PREREQUISITES = [
    ("item", "uq_inventory_item_tenant"),
    ("source_record", "uq_inventory_source_record_tenant"),
]
DDL = [
    """
CREATE TABLE cost_policy_revision (
	item_id VARCHAR NOT NULL,
	owner_party_id VARCHAR NOT NULL,
	revision INTEGER NOT NULL,
	supersedes_id VARCHAR,
	method VARCHAR NOT NULL,
	currency VARCHAR NOT NULL,
	base_unit VARCHAR NOT NULL,
	history_start TIMESTAMP WITH TIME ZONE NOT NULL,
	introduced_event_id VARCHAR NOT NULL,
	action_id VARCHAR NOT NULL,
	reason TEXT NOT NULL,
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (tenant_id, id),
	UNIQUE (tenant_id, item_id, revision),
	UNIQUE (tenant_id, supersedes_id),
	FOREIGN KEY(tenant_id, item_id) REFERENCES item (tenant_id, id),
	FOREIGN KEY(tenant_id, owner_party_id) REFERENCES party (tenant_id, id),
	FOREIGN KEY(tenant_id, supersedes_id) REFERENCES cost_policy_revision (tenant_id, id),
	FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id),
	FOREIGN KEY(tenant_id, action_id) REFERENCES action (tenant_id, id),
	CONSTRAINT ck_inventory_policy CHECK (revision>0 AND method='fifo'),
	FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)

""",
    """
CREATE TABLE cost_inventory_review (
	policy_id VARCHAR NOT NULL,
	effective_at TIMESTAMP WITH TIME ZONE NOT NULL,
	target_event_sequence INTEGER NOT NULL,
	knowledge_at TIMESTAMP WITH TIME ZONE NOT NULL,
	algorithm_version VARCHAR NOT NULL,
	input_schema_version INTEGER NOT NULL,
	content_hash VARCHAR(64) NOT NULL,
	introduced_event_id VARCHAR NOT NULL,
	action_id VARCHAR NOT NULL,
	reason TEXT NOT NULL,
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (tenant_id, id),
	UNIQUE (tenant_id, policy_id),
	FOREIGN KEY(tenant_id, policy_id) REFERENCES cost_policy_revision (tenant_id, id),
	FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id),
	FOREIGN KEY(tenant_id, action_id) REFERENCES action (tenant_id, id),
	CONSTRAINT ck_inventory_review CHECK (target_event_sequence>=0 AND input_schema_version=1 AND algorithm_version='inventory-v1'),
	FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)

""",
    """
CREATE TABLE cost_movement_basis (
	movement_id VARCHAR NOT NULL,
	movement_event_id VARCHAR NOT NULL,
	introduced_event_id VARCHAR NOT NULL,
	movement_type VARCHAR NOT NULL,
	base_quantity NUMERIC(18, 4) NOT NULL,
	base_unit VARCHAR NOT NULL,
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
	input_schema_version INTEGER NOT NULL,
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (tenant_id, id),
	UNIQUE (tenant_id, movement_id),
	FOREIGN KEY(tenant_id, movement_id) REFERENCES movement (tenant_id, id),
	FOREIGN KEY(tenant_id, movement_event_id) REFERENCES business_event (tenant_id, id),
	FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id),
	CONSTRAINT ck_inventory_movement CHECK (base_quantity>0 AND movement_type IN ('receipt','shipment','transfer') AND input_schema_version=1),
	FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)

""",
    """
CREATE TABLE cost_ownership_revision (
	receipt_basis_id VARCHAR NOT NULL,
	owner_party_id VARCHAR NOT NULL,
	evidence_source_record_id VARCHAR NOT NULL,
	covered_quantity NUMERIC(18, 4) NOT NULL,
	revision INTEGER NOT NULL,
	supersedes_id VARCHAR,
	introduced_event_id VARCHAR NOT NULL,
	action_id VARCHAR NOT NULL,
	reason TEXT NOT NULL,
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (tenant_id, id),
	UNIQUE (tenant_id, receipt_basis_id, revision),
	UNIQUE (tenant_id, supersedes_id),
	FOREIGN KEY(tenant_id, receipt_basis_id) REFERENCES cost_receipt_basis (tenant_id, id),
	FOREIGN KEY(tenant_id, owner_party_id) REFERENCES party (tenant_id, id),
	FOREIGN KEY(tenant_id, evidence_source_record_id) REFERENCES source_record (tenant_id, id),
	FOREIGN KEY(tenant_id, supersedes_id) REFERENCES cost_ownership_revision (tenant_id, id),
	FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id),
	FOREIGN KEY(tenant_id, action_id) REFERENCES action (tenant_id, id),
	CONSTRAINT ck_inventory_ownership CHECK (revision>0 AND covered_quantity>0),
	FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)

""",
    """
CREATE TABLE cost_inventory_member (
	review_id VARCHAR NOT NULL,
	movement_basis_id VARCHAR NOT NULL,
	kind VARCHAR NOT NULL,
	receipt_manifest_id VARCHAR,
	ownership_revision_id VARCHAR,
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (tenant_id, id),
	UNIQUE (tenant_id, review_id, movement_basis_id),
	FOREIGN KEY(tenant_id, review_id) REFERENCES cost_inventory_review (tenant_id, id),
	FOREIGN KEY(tenant_id, movement_basis_id) REFERENCES cost_movement_basis (tenant_id, id),
	FOREIGN KEY(tenant_id, receipt_manifest_id) REFERENCES cost_input_manifest (tenant_id, id),
	FOREIGN KEY(tenant_id, ownership_revision_id) REFERENCES cost_ownership_revision (tenant_id, id),
	CONSTRAINT ck_inventory_member CHECK ((kind='receipt' AND receipt_manifest_id IS NOT NULL AND ownership_revision_id IS NOT NULL) OR (kind IN ('issue','transfer') AND receipt_manifest_id IS NULL AND ownership_revision_id IS NULL)),
	FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)

""",
    """CREATE INDEX ix_cost_policy_revision_item_id ON cost_policy_revision (item_id)""",
    """CREATE INDEX ix_cost_policy_revision_tenant_id ON cost_policy_revision (tenant_id)""",
    """CREATE INDEX ix_cost_inventory_review_tenant_id ON cost_inventory_review (tenant_id)""",
    """CREATE INDEX ix_cost_movement_basis_tenant_id ON cost_movement_basis (tenant_id)""",
    """CREATE INDEX ix_cost_ownership_revision_receipt_basis_id ON cost_ownership_revision (receipt_basis_id)""",
    """CREATE INDEX ix_cost_ownership_revision_tenant_id ON cost_ownership_revision (tenant_id)""",
    """CREATE INDEX ix_cost_inventory_member_review_id ON cost_inventory_member (review_id)""",
    """CREATE INDEX ix_cost_inventory_member_tenant_id ON cost_inventory_member (tenant_id)""",
]


def upgrade():
    op.create_index(
        "ix_cost_movement_pool_cutoff",
        "movement",
        ["tenant_id", "item_id", "occurred_at", "id"],
    )
    for table, name in PREREQUISITES:
        op.create_unique_constraint(name, table, ["tenant_id", "id"])
    for statement in DDL:
        op.execute(statement)


def downgrade():
    bind = op.get_bind()
    names = set(inspect(bind).get_table_names())
    for table in TABLES:
        if (
            table in names
            and bind.execute(text(f'SELECT 1 FROM "{table}" LIMIT 1')).first()
        ):
            raise RuntimeError(
                "Cannot delete retained inventory authority; use a reviewed forward migration."
            )
    for table in reversed(TABLES):
        op.drop_table(table)
    op.drop_index("ix_cost_movement_pool_cutoff", table_name="movement")
    for table, name in reversed(PREREQUISITES):
        op.drop_constraint(name, table, type_="unique")
