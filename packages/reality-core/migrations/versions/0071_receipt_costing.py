"""Retained receipt acquisition-cost decisions (spec 242)."""

from alembic import op
from sqlalchemy import inspect, text

revision = "0071_receipt_costing"
down_revision = "0070_projection_clock_due"
branch_labels = None
depends_on = None
TABLES = [
    "cost_input_manifest",
    "cost_component_basis",
    "cost_attribution_revision",
    "cost_component_replacement",
    "cost_manifest_component",
    "cost_manifest_attribution",
    "cost_manifest_replacement",
    "cost_receipt_basis",
    "cost_attribution_part",
    "cost_correction_basis",
    "cost_manifest_receipt",
    "cost_scope_review",
    "cost_manifest_correction",
    "cost_scope_review_category",
]
PREREQUISITES = [
    "movement",
    "movement_correction",
    "business_event",
    "interpretation_outcome",
]
DDL = [
    """
CREATE TABLE cost_input_manifest (
    target_event_sequence INTEGER NOT NULL, 
    effective_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    knowledge_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    input_schema_version INTEGER NOT NULL, 
    algorithm_version VARCHAR NOT NULL, 
    state VARCHAR NOT NULL, 
    content_hash VARCHAR(64) NOT NULL, 
    sealed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, id), 
    CONSTRAINT ck_cost_manifest_state CHECK (state IN ('sealed') AND target_event_sequence>=0), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_component_basis (
    component_id VARCHAR NOT NULL, 
    introduced_event_id VARCHAR NOT NULL, 
    interpretation_outcome_id VARCHAR, 
    evidence_fingerprint VARCHAR(64) NOT NULL, 
    input_schema_version INTEGER NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, id), 
    UNIQUE (tenant_id, component_id), 
    FOREIGN KEY(tenant_id, component_id) REFERENCES financial_component (tenant_id, id), 
    FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id), 
    FOREIGN KEY(tenant_id, interpretation_outcome_id) REFERENCES interpretation_outcome (tenant_id, id), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_attribution_revision (
    component_basis_id VARCHAR NOT NULL, 
    revision INTEGER NOT NULL, 
    supersedes_id VARCHAR, 
    introduced_event_id VARCHAR NOT NULL, 
    action_id VARCHAR NOT NULL, 
    effective_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    reason TEXT NOT NULL, 
    state VARCHAR NOT NULL, 
    basis VARCHAR NOT NULL, 
    tax_treatment VARCHAR NOT NULL, 
    selected_basis_tax_inclusion VARCHAR NOT NULL, 
    nonrecoverable_tax_amount NUMERIC(18, 4) NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, id), 
    UNIQUE (tenant_id, component_basis_id, revision), 
    UNIQUE (tenant_id, supersedes_id), 
    FOREIGN KEY(tenant_id, component_basis_id) REFERENCES cost_component_basis (tenant_id, id), 
    FOREIGN KEY(tenant_id, supersedes_id) REFERENCES cost_attribution_revision (tenant_id, id), 
    FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id), 
    FOREIGN KEY(tenant_id, action_id) REFERENCES action (tenant_id, id), 
    CONSTRAINT ck_cost_attribution_state CHECK (revision>0 AND state IN ('assigned','withdrawn') AND basis IN ('net','gross','base')), 
    CONSTRAINT ck_cost_attribution_tax CHECK (tax_treatment IN ('recoverable','nonrecoverable','mixed','not_applicable','unknown') AND selected_basis_tax_inclusion IN ('included','excluded','unknown')), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_component_replacement (
    previous_basis_id VARCHAR NOT NULL, 
    replacement_basis_id VARCHAR NOT NULL, 
    introduced_event_id VARCHAR NOT NULL, 
    action_id VARCHAR NOT NULL, 
    reason TEXT NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, id), 
    UNIQUE (tenant_id, previous_basis_id), 
    UNIQUE (tenant_id, replacement_basis_id), 
    FOREIGN KEY(tenant_id, previous_basis_id) REFERENCES cost_component_basis (tenant_id, id), 
    FOREIGN KEY(tenant_id, replacement_basis_id) REFERENCES cost_component_basis (tenant_id, id), 
    FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id), 
    FOREIGN KEY(tenant_id, action_id) REFERENCES action (tenant_id, id), 
    CONSTRAINT ck_cost_replacement_distinct CHECK (previous_basis_id<>replacement_basis_id), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_manifest_component (
    manifest_id VARCHAR NOT NULL, 
    component_basis_id VARCHAR NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, manifest_id, component_basis_id), 
    FOREIGN KEY(tenant_id, manifest_id) REFERENCES cost_input_manifest (tenant_id, id), 
    FOREIGN KEY(tenant_id, component_basis_id) REFERENCES cost_component_basis (tenant_id, id), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_manifest_attribution (
    manifest_id VARCHAR NOT NULL, 
    attribution_revision_id VARCHAR NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, manifest_id, attribution_revision_id), 
    FOREIGN KEY(tenant_id, manifest_id) REFERENCES cost_input_manifest (tenant_id, id), 
    FOREIGN KEY(tenant_id, attribution_revision_id) REFERENCES cost_attribution_revision (tenant_id, id), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_manifest_replacement (
    manifest_id VARCHAR NOT NULL, 
    replacement_id VARCHAR NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, manifest_id, replacement_id), 
    FOREIGN KEY(tenant_id, manifest_id) REFERENCES cost_input_manifest (tenant_id, id), 
    FOREIGN KEY(tenant_id, replacement_id) REFERENCES cost_component_replacement (tenant_id, id), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_receipt_basis (
    movement_id VARCHAR NOT NULL, 
    introduced_event_id VARCHAR NOT NULL, 
    base_quantity NUMERIC(18, 4) NOT NULL, 
    base_unit VARCHAR NOT NULL, 
    input_schema_version INTEGER NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, id), 
    UNIQUE (tenant_id, movement_id), 
    FOREIGN KEY(tenant_id, movement_id) REFERENCES movement (tenant_id, id), 
    FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id), 
    CONSTRAINT ck_cost_receipt_quantity CHECK (base_quantity>0), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_attribution_part (
    attribution_revision_id VARCHAR NOT NULL, 
    receipt_basis_id VARCHAR NOT NULL, 
    amount_bucket VARCHAR NOT NULL, 
    category VARCHAR NOT NULL, 
    source_share NUMERIC(18, 4) NOT NULL, 
    cost_effect INTEGER NOT NULL, 
    assignment_kind VARCHAR NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, id), 
    UNIQUE (tenant_id, attribution_revision_id, receipt_basis_id, amount_bucket, category), 
    FOREIGN KEY(tenant_id, attribution_revision_id) REFERENCES cost_attribution_revision (tenant_id, id), 
    FOREIGN KEY(tenant_id, receipt_basis_id) REFERENCES cost_receipt_basis (tenant_id, id), 
    CONSTRAINT ck_cost_part_amount CHECK (source_share<>0 AND cost_effect IN (-1,1)), 
    CONSTRAINT ck_cost_part_kind CHECK (amount_bucket IN ('selected_basis','nonrecoverable_tax') AND assignment_kind IN ('direct','allocated')), 
    CONSTRAINT ck_cost_part_category CHECK (category IN ('goods','inbound_freight','duty','other_acquisition','purchase_reduction','nonrecoverable_tax')), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_correction_basis (
    movement_correction_id VARCHAR NOT NULL, 
    introduced_event_id VARCHAR NOT NULL, 
    input_schema_version INTEGER NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, id), 
    UNIQUE (tenant_id, movement_correction_id), 
    FOREIGN KEY(tenant_id, movement_correction_id) REFERENCES movement_correction (tenant_id, id), 
    FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_manifest_receipt (
    manifest_id VARCHAR NOT NULL, 
    receipt_basis_id VARCHAR NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, manifest_id, receipt_basis_id), 
    FOREIGN KEY(tenant_id, manifest_id) REFERENCES cost_input_manifest (tenant_id, id), 
    FOREIGN KEY(tenant_id, receipt_basis_id) REFERENCES cost_receipt_basis (tenant_id, id), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_scope_review (
    receipt_basis_id VARCHAR NOT NULL, 
    revision INTEGER NOT NULL, 
    supersedes_id VARCHAR, 
    manifest_id VARCHAR NOT NULL, 
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
    FOREIGN KEY(tenant_id, manifest_id) REFERENCES cost_input_manifest (tenant_id, id), 
    FOREIGN KEY(tenant_id, supersedes_id) REFERENCES cost_scope_review (tenant_id, id), 
    FOREIGN KEY(tenant_id, introduced_event_id) REFERENCES business_event (tenant_id, id), 
    FOREIGN KEY(tenant_id, action_id) REFERENCES action (tenant_id, id), 
    CONSTRAINT ck_cost_review_revision CHECK (revision>0), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_manifest_correction (
    manifest_id VARCHAR NOT NULL, 
    correction_basis_id VARCHAR NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, manifest_id, correction_basis_id), 
    FOREIGN KEY(tenant_id, manifest_id) REFERENCES cost_input_manifest (tenant_id, id), 
    FOREIGN KEY(tenant_id, correction_basis_id) REFERENCES cost_correction_basis (tenant_id, id), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE TABLE cost_scope_review_category (
    review_id VARCHAR NOT NULL, 
    category VARCHAR NOT NULL, 
    disposition VARCHAR NOT NULL, 
    reason TEXT NOT NULL, 
    id VARCHAR NOT NULL, 
    tenant_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (tenant_id, id), 
    UNIQUE (tenant_id, review_id, category), 
    FOREIGN KEY(tenant_id, review_id) REFERENCES cost_scope_review (tenant_id, id), 
    CONSTRAINT ck_cost_review_disposition CHECK (disposition IN ('evidenced','confirmed_zero','not_applicable','unresolved')), 
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""",
    """
CREATE INDEX ix_cost_input_manifest_tenant_id ON cost_input_manifest (tenant_id)
""",
    """
CREATE INDEX ix_cost_component_basis_tenant_id ON cost_component_basis (tenant_id)
""",
    """
CREATE INDEX ix_cost_attribution_revision_component_basis_id ON cost_attribution_revision (component_basis_id)
""",
    """
CREATE INDEX ix_cost_attribution_revision_tenant_id ON cost_attribution_revision (tenant_id)
""",
    """
CREATE INDEX ix_cost_component_replacement_tenant_id ON cost_component_replacement (tenant_id)
""",
    """
CREATE INDEX ix_cost_manifest_component_manifest_id ON cost_manifest_component (manifest_id)
""",
    """
CREATE INDEX ix_cost_manifest_component_tenant_id ON cost_manifest_component (tenant_id)
""",
    """
CREATE INDEX ix_cost_manifest_attribution_manifest_id ON cost_manifest_attribution (manifest_id)
""",
    """
CREATE INDEX ix_cost_manifest_attribution_tenant_id ON cost_manifest_attribution (tenant_id)
""",
    """
CREATE INDEX ix_cost_manifest_replacement_manifest_id ON cost_manifest_replacement (manifest_id)
""",
    """
CREATE INDEX ix_cost_manifest_replacement_tenant_id ON cost_manifest_replacement (tenant_id)
""",
    """
CREATE INDEX ix_cost_receipt_basis_tenant_id ON cost_receipt_basis (tenant_id)
""",
    """
CREATE INDEX ix_cost_attribution_part_attribution_revision_id ON cost_attribution_part (attribution_revision_id)
""",
    """
CREATE INDEX ix_cost_attribution_part_receipt_basis_id ON cost_attribution_part (receipt_basis_id)
""",
    """
CREATE INDEX ix_cost_attribution_part_tenant_id ON cost_attribution_part (tenant_id)
""",
    """
CREATE INDEX ix_cost_correction_basis_tenant_id ON cost_correction_basis (tenant_id)
""",
    """
CREATE INDEX ix_cost_manifest_receipt_manifest_id ON cost_manifest_receipt (manifest_id)
""",
    """
CREATE INDEX ix_cost_manifest_receipt_tenant_id ON cost_manifest_receipt (tenant_id)
""",
    """
CREATE INDEX ix_cost_scope_review_receipt_basis_id ON cost_scope_review (receipt_basis_id)
""",
    """
CREATE INDEX ix_cost_scope_review_tenant_id ON cost_scope_review (tenant_id)
""",
    """
CREATE INDEX ix_cost_manifest_correction_manifest_id ON cost_manifest_correction (manifest_id)
""",
    """
CREATE INDEX ix_cost_manifest_correction_tenant_id ON cost_manifest_correction (tenant_id)
""",
    """
CREATE INDEX ix_cost_scope_review_category_review_id ON cost_scope_review_category (review_id)
""",
    """
CREATE INDEX ix_cost_scope_review_category_tenant_id ON cost_scope_review_category (tenant_id)
""",
]


def upgrade():
    bind = op.get_bind()
    for table in PREREQUISITES:
        if not any(
            c["column_names"] == ["tenant_id", "id"]
            for c in inspect(bind).get_unique_constraints(table)
        ):
            op.create_unique_constraint(
                f"uq_cost_{table}_tenant", table, ["tenant_id", "id"]
            )
    for statement in DDL:
        op.execute(statement)


def downgrade():
    bind = op.get_bind()
    for table in TABLES:
        if bind.scalar(text(f'SELECT EXISTS(SELECT 1 FROM "{table}" LIMIT 1)')):
            raise RuntimeError(
                "Cannot delete retained costing history; use a reviewed forward migration."
            )
    for table in reversed(TABLES):
        op.drop_table(table)
    for table in reversed(PREREQUISITES):
        name = f"uq_cost_{table}_tenant"
        if any(c["name"] == name for c in inspect(bind).get_unique_constraints(table)):
            op.drop_constraint(name, table, type_="unique")
