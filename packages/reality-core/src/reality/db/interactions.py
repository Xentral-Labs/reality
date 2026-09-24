"""One observed use of a company's model (spec 266, the engine room).

Operational telemetry, never a business record: no business read, projection,
exception rule or decision joins it, rows carry no argument or result values, and
they expire after seven days. What happened to the business stays in
`business_event`; this table only says that somebody, through some channel, asked
for something, and which committed events came of it.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now

CHANNELS = ("web", "mcp", "chat", "cli", "worker")
KINDS = ("read", "propose", "decide", "job")
OUTCOMES = ("ok", "refused", "failed", "awaiting_decision")
SUMMARY_BYTES = 1024


def _enumeration(column: str, values: tuple[str, ...]) -> CheckConstraint:
    listed = ", ".join(f"'{value}'" for value in values)
    return CheckConstraint(f"{column} IN ({listed})", name=f"ck_interaction_{column}")


class Interaction(Base):
    __tablename__ = "interaction"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "mcp_token_id"],
            ["mcp_access_token.tenant_id", "mcp_access_token.id"],
            name="fk_interaction_mcp_token",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "proposal_id"],
            ["action.tenant_id", "action.id"],
            name="fk_interaction_proposal",
        ),
        UniqueConstraint("cursor", name="uq_interaction_cursor"),
        _enumeration("channel", CHANNELS),
        _enumeration("kind", KINDS),
        _enumeration("outcome", OUTCOMES),
        CheckConstraint(
            f"octet_length(summary::text) <= {SUMMARY_BYTES}",
            name="ck_interaction_summary",
        ),
        # The poll: everything of one company after a cursor.
        Index("ix_interaction_cursor", "tenant_id", "cursor"),
        # Replay windows and retention.
        Index("ix_interaction_recorded", "tenant_id", "recorded_at"),
        Index("ix_interaction_correlation", "tenant_id", "correlation_id"),
        # "Who changed this": the interactions whose events span a sequence.
        Index(
            "ix_interaction_events",
            "tenant_id",
            "event_first_sequence",
            "event_last_sequence",
        ),
        # Named foreign-key indexes, so the derived-index rule finds them covered.
        Index("ix_interaction_mcp_token_id", "tenant_id", "mcp_token_id"),
        Index("ix_interaction_proposal_id", "tenant_id", "proposal_id"),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    cursor: Mapped[int] = mapped_column(BigInteger, Identity())
    started_at: Mapped[datetime] = mapped_column(UTCDateTime)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    duration_ms: Mapped[int] = mapped_column(Integer)
    channel: Mapped[str] = mapped_column(String(16))
    kind: Mapped[str] = mapped_column(String(16))
    operation: Mapped[str] = mapped_column(String(200))
    outcome: Mapped[str] = mapped_column(String(24))
    error_code: Mapped[str | None] = mapped_column(String(64), default=None)
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_user.id"), index=True, default=None
    )
    mcp_token_id: Mapped[str | None] = mapped_column(String, default=None)
    job_id: Mapped[str | None] = mapped_column(String, default=None)
    correlation_id: Mapped[str] = mapped_column(String(64))
    proposal_id: Mapped[str | None] = mapped_column(String, default=None)
    event_first_sequence: Mapped[int | None] = mapped_column(BigInteger, default=None)
    event_last_sequence: Mapped[int | None] = mapped_column(BigInteger, default=None)
    event_ranges: Mapped[list | None] = mapped_column(
        JSONB(none_as_null=True), default=None
    )
    refresh: Mapped[bool] = mapped_column(Boolean, default=False)
    summary: Mapped[dict] = mapped_column(JSONB, default=dict)
