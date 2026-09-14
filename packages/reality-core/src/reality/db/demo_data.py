"""Synthetic integration lifecycle; source/import outcomes own progress."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now


class DemoDataConnection(Base):
    __tablename__ = "demo_data_connection"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "source_system_id"],
            ["source_system.tenant_id", "source_system.id"],
            name="fk_demo_connection_source_scope",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "current_schedule_id"],
            ["scheduled_job.tenant_id", "scheduled_job.id"],
            name="fk_demo_connection_schedule_scope",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "settlement_schedule_id"],
            ["scheduled_job.tenant_id", "scheduled_job.id"],
            name="fk_demo_connection_settlement_schedule_scope",
        ),
        CheckConstraint(
            "state IN ('stopped','running','paused','disconnected')",
            name="ck_demo_connection_state",
        ),
        CheckConstraint("revision >= 1", name="ck_demo_connection_revision"),
        CheckConstraint(
            "state NOT IN ('running','paused') OR current_schedule_id IS NOT NULL",
            name="ck_demo_connection_active_schedule",
        ),
        CheckConstraint(
            "(last_request_key IS NULL) = (last_request_fingerprint IS NULL)",
            name="ck_demo_connection_request_pair",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), unique=True)
    source_system_id: Mapped[str] = mapped_column(String)
    current_schedule_id: Mapped[str | None] = mapped_column(String, default=None)
    # Feature 168: the settlement stream's schedule, created and cancelled with
    # the order schedule; NULL for connections that never started since then.
    settlement_schedule_id: Mapped[str | None] = mapped_column(String, default=None)
    state: Mapped[str] = mapped_column(String(16), default="stopped")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    last_request_key: Mapped[str | None] = mapped_column(String(128), default=None)
    last_request_fingerprint: Mapped[str | None] = mapped_column(
        String(64), default=None
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
