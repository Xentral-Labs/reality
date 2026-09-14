"""Add tenant-scoped schedules and durable logical job runs."""

from alembic import op

revision = "0045_scheduled_jobs"
down_revision = "0044_playground_returns_merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
CREATE TABLE scheduled_job (
    id VARCHAR NOT NULL,
    tenant_id VARCHAR NOT NULL,
    actor_id VARCHAR NOT NULL,
    job_type VARCHAR NOT NULL,
    configuration JSONB NOT NULL,
    interval_seconds INTEGER,
    cron_expression VARCHAR,
    enabled BOOLEAN NOT NULL,
    next_run_at TIMESTAMP WITH TIME ZONE,
    revision INTEGER NOT NULL,
    create_request_id VARCHAR(128) NOT NULL,
    create_fingerprint VARCHAR(64) NOT NULL,
    last_control_request_id VARCHAR(128),
    last_control_fingerprint VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_scheduled_job_tenant_id UNIQUE (tenant_id, id),
    CONSTRAINT uq_scheduled_job_request UNIQUE (tenant_id, create_request_id),
    CONSTRAINT ck_scheduled_job_timing CHECK ((interval_seconds IS NOT NULL AND interval_seconds >= 5 AND cron_expression IS NULL) OR (interval_seconds IS NULL AND cron_expression IS NOT NULL)),
    CONSTRAINT ck_scheduled_job_revision CHECK (revision >= 1),
    CONSTRAINT ck_scheduled_job_configuration CHECK (jsonb_typeof(configuration) = 'object' AND octet_length(configuration::text) <= 16384),
    FOREIGN KEY(tenant_id) REFERENCES tenant (id),
    FOREIGN KEY(actor_id) REFERENCES app_user (id)
)
"""
    )
    op.execute(
        "CREATE INDEX ix_scheduled_job_due ON scheduled_job (tenant_id, enabled, next_run_at, id)"
    )
    op.execute(
        """
CREATE TABLE scheduled_job_run (
    id VARCHAR NOT NULL,
    tenant_id VARCHAR NOT NULL,
    schedule_id VARCHAR,
    actor_id VARCHAR NOT NULL,
    job_type VARCHAR NOT NULL,
    configuration JSONB NOT NULL,
    schedule_revision INTEGER,
    scheduled_for TIMESTAMP WITH TIME ZONE,
    request_id VARCHAR(128),
    request_fingerprint VARCHAR(64),
    status VARCHAR NOT NULL,
    attempt_count INTEGER NOT NULL,
    next_attempt_at TIMESTAMP WITH TIME ZONE NOT NULL,
    claim_token VARCHAR,
    lease_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    last_error_code VARCHAR(80),
    result JSONB,
    PRIMARY KEY (id),
    CONSTRAINT fk_scheduled_run_tenant_schedule FOREIGN KEY(tenant_id, schedule_id) REFERENCES scheduled_job (tenant_id, id),
    CONSTRAINT uq_scheduled_run_occurrence UNIQUE (tenant_id, schedule_id, scheduled_for),
    CONSTRAINT uq_scheduled_run_request UNIQUE (tenant_id, request_id),
    CONSTRAINT ck_scheduled_run_status CHECK (status IN ('pending','running','retry','succeeded','failed','unresolved','cancelled')),
    CONSTRAINT ck_scheduled_run_attempts CHECK (attempt_count BETWEEN 0 AND 3),
    CONSTRAINT ck_scheduled_run_origin CHECK ((schedule_id IS NOT NULL AND scheduled_for IS NOT NULL AND schedule_revision IS NOT NULL AND request_id IS NULL AND request_fingerprint IS NULL) OR (schedule_id IS NULL AND scheduled_for IS NULL AND schedule_revision IS NULL AND request_id IS NOT NULL AND request_fingerprint IS NOT NULL)),
    CONSTRAINT ck_scheduled_run_configuration CHECK (jsonb_typeof(configuration) = 'object' AND octet_length(configuration::text) <= 16384),
    CONSTRAINT ck_scheduled_run_result CHECK (result IS NULL OR (jsonb_typeof(result) = 'object' AND octet_length(result::text) <= 4096)),
    FOREIGN KEY(tenant_id) REFERENCES tenant (id),
    FOREIGN KEY(actor_id) REFERENCES app_user (id)
)
"""
    )
    op.execute(
        "CREATE INDEX ix_scheduled_run_due ON scheduled_job_run (tenant_id, status, next_attempt_at, id)"
    )
    op.execute(
        "CREATE INDEX ix_scheduled_run_history ON scheduled_job_run (tenant_id, created_at, id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_scheduled_run_unfinished ON scheduled_job_run (tenant_id, schedule_id) WHERE status IN ('pending','running','retry','unresolved')"
    )


def downgrade() -> None:
    op.drop_table("scheduled_job_run")
    op.drop_table("scheduled_job")
