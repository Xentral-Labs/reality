"""Add approved ordinary creation receipts and demo connection lifecycle."""

from alembic import op

revision = "0046_company_setup_demo"
down_revision = "0045_scheduled_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_source_system_tenant_id", "source_system", ["tenant_id", "id"]
    )
    op.execute("""
CREATE TABLE ordinary_company_creation (
    id VARCHAR NOT NULL,
    tenant_id VARCHAR NOT NULL,
    actor_id VARCHAR NOT NULL,
    request_key VARCHAR(128) NOT NULL,
    request_fingerprint VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_company_creation_request UNIQUE (actor_id, request_key),
    UNIQUE (tenant_id),
    FOREIGN KEY(tenant_id) REFERENCES tenant (id),
    FOREIGN KEY(actor_id) REFERENCES app_user (id)
)
""")
    op.execute("""
CREATE TABLE demo_data_connection (
    id VARCHAR NOT NULL,
    tenant_id VARCHAR NOT NULL,
    source_system_id VARCHAR NOT NULL,
    current_schedule_id VARCHAR,
    state VARCHAR(16) NOT NULL,
    revision INTEGER NOT NULL,
    last_request_key VARCHAR(128),
    last_request_fingerprint VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_demo_connection_source_scope FOREIGN KEY(tenant_id, source_system_id) REFERENCES source_system (tenant_id, id),
    CONSTRAINT fk_demo_connection_schedule_scope FOREIGN KEY(tenant_id, current_schedule_id) REFERENCES scheduled_job (tenant_id, id),
    CONSTRAINT ck_demo_connection_state CHECK (state IN ('stopped','running','paused','disconnected')),
    CONSTRAINT ck_demo_connection_revision CHECK (revision >= 1),
    CONSTRAINT ck_demo_connection_active_schedule CHECK (state NOT IN ('running','paused') OR current_schedule_id IS NOT NULL),
    CONSTRAINT ck_demo_connection_request_pair CHECK ((last_request_key IS NULL) = (last_request_fingerprint IS NULL)),
    UNIQUE (tenant_id),
    FOREIGN KEY(tenant_id) REFERENCES tenant (id)
)
""")


def downgrade() -> None:
    op.drop_table("demo_data_connection")
    op.drop_table("ordinary_company_creation")
    op.drop_constraint("uq_source_system_tenant_id", "source_system", type_="unique")
