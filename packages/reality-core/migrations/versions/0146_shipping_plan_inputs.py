"""Add approved source-backed shipping planning inputs (spec 378)."""

import sqlalchemy as sa
from alembic import op

revision = "0146_shipping_plan_inputs"
down_revision = "0145_default_operational_cases"
branch_labels = None
depends_on = None

# Frozen DDL: do not import changing runtime models into a migration.
DDL = (
    """CREATE TABLE shipping_plan_statement (
    tenant_id VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    source_record_id VARCHAR NOT NULL,
    statement_kind VARCHAR NOT NULL,
    dispatch_location_id VARCHAR NOT NULL,
    business_day DATE NOT NULL,
    business_time_zone VARCHAR NOT NULL,
    site_time_zone VARCHAR NOT NULL,
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY(tenant_id, source_record_id) REFERENCES source_record (tenant_id, id),
    FOREIGN KEY(tenant_id, dispatch_location_id) REFERENCES location (tenant_id, id),
    CONSTRAINT uq_shipping_plan_source UNIQUE (tenant_id, source_record_id),
    CONSTRAINT ck_shipping_plan_kind CHECK (statement_kind IN ('plan', 'withdrawal')),
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)""",
    "CREATE INDEX ix_shipping_plan_scope ON shipping_plan_statement (tenant_id, business_day, dispatch_location_id)",
    "CREATE INDEX ix_shipping_plan_statement_dispatch_location_id ON shipping_plan_statement (tenant_id, dispatch_location_id)",
    """CREATE TABLE shipping_dispatch_requirement (
    tenant_id VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    statement_id VARCHAR NOT NULL,
    commitment_id VARCHAR NOT NULL,
    quantity NUMERIC(18, 4) NOT NULL,
    dispatch_due_at TIMESTAMP WITH TIME ZONE NOT NULL,
    planned_handover_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY(tenant_id, statement_id) REFERENCES shipping_plan_statement (tenant_id, id),
    FOREIGN KEY(tenant_id, commitment_id) REFERENCES commitment (tenant_id, id),
    CONSTRAINT uq_shipping_requirement_commitment UNIQUE (tenant_id, statement_id, commitment_id),
    CONSTRAINT ck_shipping_requirement_quantity CHECK (quantity > 0),
    CONSTRAINT ck_shipping_requirement_plan_time CHECK (planned_handover_at IS NULL OR planned_handover_at <= dispatch_due_at),
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)""",
    "CREATE INDEX ix_shipping_requirement_commitment ON shipping_dispatch_requirement (tenant_id, commitment_id)",
    """CREATE TABLE shipping_capacity_window (
    tenant_id VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    statement_id VARCHAR NOT NULL,
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
    collection_cutoff_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completion_slots INTEGER NOT NULL,
    confirmation_state VARCHAR NOT NULL,
    confirmation_source_record_id VARCHAR,
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY(tenant_id, statement_id) REFERENCES shipping_plan_statement (tenant_id, id),
    FOREIGN KEY(tenant_id, confirmation_source_record_id) REFERENCES source_record (tenant_id, id),
    CONSTRAINT ck_shipping_capacity_slots CHECK (completion_slots >= 0),
    CONSTRAINT ck_shipping_capacity_interval CHECK (starts_at < collection_cutoff_at AND collection_cutoff_at <= ends_at),
    CONSTRAINT ck_shipping_capacity_confirmation CHECK (confirmation_state IN ('requested', 'confirmed') AND (confirmation_state <> 'confirmed' OR confirmation_source_record_id IS NOT NULL)),
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)""",
    "CREATE INDEX ix_shipping_capacity_statement ON shipping_capacity_window (tenant_id, statement_id)",
    "CREATE INDEX ix_shipping_capacity_window_confirmation_source_record_id ON shipping_capacity_window (tenant_id, confirmation_source_record_id)",
)


def upgrade() -> None:
    for statement in DDL:
        op.execute(statement)


def downgrade() -> None:
    if (
        op.get_bind()
        .execute(sa.text("SELECT EXISTS (SELECT 1 FROM shipping_plan_statement)"))
        .scalar()
    ):
        raise RuntimeError(
            "Preserve accepted shipping-planning evidence; disable the cockpit instead of dropping historical inputs."
        )
    op.drop_table("shipping_capacity_window")
    op.drop_table("shipping_dispatch_requirement")
    op.drop_table("shipping_plan_statement")
