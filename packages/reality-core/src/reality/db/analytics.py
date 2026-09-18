"""Private analytical configuration; results remain read-time observations."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now


class AnalyticsReport(Base):
    __tablename__ = "analytics_report"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_analytics_report_tenant"),
        UniqueConstraint(
            "tenant_id",
            "owner_user_id",
            "create_request_id",
            name="uq_analytics_report_create",
        ),
        CheckConstraint("revision > 0", name="ck_analytics_report_revision"),
        CheckConstraint(
            "length(trim(name)) BETWEEN 1 AND 120", name="ck_analytics_report_name"
        ),
        Index(
            "ix_analytics_report_owner",
            "tenant_id",
            "owner_user_id",
            "id",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"))
    name: Mapped[str] = mapped_column(String(120))
    definition: Mapped[dict] = mapped_column(JSONB)
    # Which kind of question this is, and the model version that gave it meaning.
    # Null for reports saved by the configured generation, whose meaning lives in
    # the definition itself; a graph report always carries both.
    kind: Mapped[str | None] = mapped_column(String, default=None)
    model_version: Mapped[str | None] = mapped_column(String, default=None)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    create_request_id: Mapped[str] = mapped_column(String(128))
    create_payload_hash: Mapped[str] = mapped_column(String(64))
    last_request_id: Mapped[str] = mapped_column(String(128))
    last_payload_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)


class AnalysisRequest(Base):
    """One question asked, and — once the worker has answered it — that answer.

    Deliberately not an `AnalyticsReport`. A report is a saved *question*, re-asked
    on every read, so it is always as current as the records. This is a saved
    *answer*: true of one moment, and of no other. Putting both in one table would
    make it a matter of which column happens to be set whether a row is a question
    or a fact, which is how the two would eventually be confused.

    `rows` is therefore never read as a current figure. It carries `answered_at`
    and `model_version` so that whoever reads it knows exactly what it is evidence
    of, and `expires_at` so an uncollected answer does not linger as one.
    """

    __tablename__ = "analysis_request"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_analysis_request_tenant"),
        UniqueConstraint(
            "tenant_id",
            "requested_by_user_id",
            "request_id",
            name="uq_analysis_request_idempotent",
        ),
        CheckConstraint(
            "state IN ('accepted', 'running', 'ready', 'failed')",
            name="ck_analysis_request_state",
        ),
        Index(
            "ix_analysis_request_requester",
            "tenant_id",
            "requested_by_user_id",
            "id",
        ),
        Index("ix_analysis_request_expiry", "expires_at"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    requested_by_user_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"))
    # The checked traversal, exactly as it was accepted. The answer means nothing
    # without it, so the two are never stored apart.
    question: Mapped[dict] = mapped_column(JSONB)
    model_version: Mapped[str] = mapped_column(String)
    # Why this question could not be answered in the request. One of the derivation
    # size codes; kept so the asker is told which limit sent it to the worker.
    deferred_reason: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String, default="accepted")
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("scheduled_job_run.id"), default=None
    )
    rows: Mapped[list | None] = mapped_column(JSONB, default=None)
    row_count: Mapped[int | None] = mapped_column(Integer, default=None)
    statements: Mapped[int | None] = mapped_column(Integer, default=None)
    answered_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    failure_code: Mapped[str | None] = mapped_column(String, default=None)
    failure_message: Mapped[str | None] = mapped_column(String, default=None)
    request_id: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
