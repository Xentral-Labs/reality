"""Tenant-owned timing and execution metadata, never business authority."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now


class ScheduledJob(Base):
    __tablename__ = "scheduled_job"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "id", name="uq_scheduled_job_tenant_id"),
        UniqueConstraint(
            "tenant_id", "create_request_id", name="uq_scheduled_job_request"
        ),
        CheckConstraint(
            "(interval_seconds IS NOT NULL AND interval_seconds >= 5 AND cron_expression IS NULL) OR (interval_seconds IS NULL AND cron_expression IS NOT NULL)",
            name="ck_scheduled_job_timing",
        ),
        CheckConstraint("revision >= 1", name="ck_scheduled_job_revision"),
        CheckConstraint(
            "jsonb_typeof(configuration) = 'object' AND octet_length(configuration::text) <= 16384",
            name="ck_scheduled_job_configuration",
        ),
        Index("ix_scheduled_job_due", "tenant_id", "enabled", "next_run_at", "id"),
        # A suspended schedule is found by its own recovery moment, never by scanning
        # every disabled schedule of a company (spec 256 FR-007).
        Index(
            "ix_scheduled_job_recovery",
            "tenant_id",
            "resume_after",
            postgresql_where="resume_after IS NOT NULL",
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    actor_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"))
    job_type: Mapped[str] = mapped_column(String)
    configuration: Mapped[dict] = mapped_column(JSONB)
    interval_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    cron_expression: Mapped[str | None] = mapped_column(String, default=None)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    next_run_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    #: When an infrastructure failure suspended this schedule, the moment it may try
    #: again. Timing, not an observation: nothing here says why it was suspended.
    resume_after: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    create_request_id: Mapped[str] = mapped_column(String(128))
    create_fingerprint: Mapped[str] = mapped_column(String(64))
    last_control_request_id: Mapped[str | None] = mapped_column(
        String(128), default=None
    )
    last_control_fingerprint: Mapped[str | None] = mapped_column(
        String(64), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class ScheduledJobRun(Base):
    __tablename__ = "scheduled_job_run"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "schedule_id"],
            ["scheduled_job.tenant_id", "scheduled_job.id"],
            name="fk_scheduled_run_tenant_schedule",
        ),
        UniqueConstraint(
            "tenant_id",
            "schedule_id",
            "scheduled_for",
            name="uq_scheduled_run_occurrence",
        ),
        UniqueConstraint("tenant_id", "request_id", name="uq_scheduled_run_request"),
        CheckConstraint(
            "status IN ('pending','running','retry','succeeded','failed','unresolved','cancelled')",
            name="ck_scheduled_run_status",
        ),
        CheckConstraint(
            "attempt_count BETWEEN 0 AND 3", name="ck_scheduled_run_attempts"
        ),
        CheckConstraint(
            "(schedule_id IS NOT NULL AND scheduled_for IS NOT NULL AND schedule_revision IS NOT NULL AND request_id IS NULL AND request_fingerprint IS NULL) OR (schedule_id IS NULL AND scheduled_for IS NULL AND schedule_revision IS NULL AND request_id IS NOT NULL AND request_fingerprint IS NOT NULL)",
            name="ck_scheduled_run_origin",
        ),
        CheckConstraint(
            "jsonb_typeof(configuration) = 'object' AND octet_length(configuration::text) <= 16384",
            name="ck_scheduled_run_configuration",
        ),
        CheckConstraint(
            "result IS NULL OR (jsonb_typeof(result) = 'object' AND octet_length(result::text) <= 4096)",
            name="ck_scheduled_run_result",
        ),
        CheckConstraint(
            "failure_detail IS NULL OR length(failure_detail) <= 400",
            name="ck_scheduled_run_failure_detail",
        ),
        Index(
            "uq_scheduled_run_unfinished",
            "tenant_id",
            "schedule_id",
            unique=True,
            postgresql_where="status IN ('pending','running','retry','unresolved')",
        ),
        CheckConstraint(
            "(job_type = 'projections.refresh' AND actor_id IS NULL AND schedule_id IS NULL) OR (job_type <> 'projections.refresh' AND actor_id IS NOT NULL)",
            name="ck_scheduled_run_actor",
        ),
        # One unfinished refresh run per projection of a company (spec 181 FR-004).
        # The projection is read out of the run's own configuration, so the queue
        # stays the only place that says what is already promised.
        Index(
            "uq_projection_run_unfinished",
            "tenant_id",
            "job_type",
            text("(configuration #>> '{arguments,names,0}')"),
            unique=True,
            postgresql_where="job_type = 'projections.refresh' AND status IN ('pending','running','retry','unresolved')",
        ),
        Index("ix_scheduled_run_due", "tenant_id", "status", "next_attempt_at", "id"),
        Index("ix_scheduled_run_history", "tenant_id", "created_at", "id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    schedule_id: Mapped[str | None] = mapped_column(String, default=None)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("app_user.id"))
    job_type: Mapped[str] = mapped_column(String)
    configuration: Mapped[dict] = mapped_column(JSONB)
    schedule_revision: Mapped[int | None] = mapped_column(Integer, default=None)
    scheduled_for: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    request_id: Mapped[str | None] = mapped_column(String(128), default=None)
    request_fingerprint: Mapped[str | None] = mapped_column(String(64), default=None)
    status: Mapped[str] = mapped_column(String, default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    claim_token: Mapped[str | None] = mapped_column(String, default=None)
    lease_expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    last_error_code: Mapped[str | None] = mapped_column(String(80), default=None)
    #: A bounded operator-readable cause behind the code: exception class and a
    #: truncated message. Never a payload, credential or connection string.
    failure_detail: Mapped[str | None] = mapped_column(String(400), default=None)
    result: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True), default=None)
