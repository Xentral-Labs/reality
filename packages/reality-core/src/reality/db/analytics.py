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
