"""Disposable company read models; never consumed by business mutations."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    PrimaryKeyConstraint,
    String,
    cast,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, Document, SourceRecord, UTCDateTime

ORDER_FLAGS = (
    "ready",
    "blocked",
    "reservation_blocked",
    "held",
    "overdue",
    "at_risk",
    "complete",
    "partial",
    "unshipped",
    "cancelled",
    "eligible",
    "received_last_hour",
    "completed_last_hour",
    "first_dispatch_sample",
    "complete_dispatch_sample",
)


class BusinessOrderRow(Base):
    __tablename__ = "business_order_row"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "generation", "document_id"),
        Index(
            "ix_business_order_page",
            "tenant_id",
            "generation",
            "received_sort",
            "document_id",
        ),
        Index(
            "ix_business_order_clock",
            "tenant_id",
            "generation",
            "next_transition_at",
            "document_id",
        ),
        *(
            Index(
                f"ix_business_order_{flag}",
                "tenant_id",
                "generation",
                "received_sort",
                "document_id",
                postgresql_where=text(f"flags @> ARRAY['{flag}']::varchar[]"),
            )
            for flag in ORDER_FLAGS
        ),
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    generation: Mapped[str] = mapped_column(String)
    document_id: Mapped[str] = mapped_column(String)
    received_sort: Mapped[datetime] = mapped_column(UTCDateTime)
    next_transition_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    flags: Mapped[list[str]] = mapped_column(ARRAY(String))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    contribution: Mapped[dict[str, Any]] = mapped_column(JSONB)


class BusinessMailRow(Base):
    __tablename__ = "business_mail_row"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "generation", "source_record_id"),
        Index(
            "ix_business_mail_page",
            "tenant_id",
            "generation",
            text("recorded_at DESC"),
            "source_record_id",
        ),
        Index(
            "ix_business_mail_direction",
            "tenant_id",
            "generation",
            "direction",
            text("recorded_at DESC"),
            "source_record_id",
        ),
        Index(
            "ix_business_mail_waiting",
            "tenant_id",
            "generation",
            text("recorded_at DESC"),
            "source_record_id",
            postgresql_where=text("waiting"),
        ),
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"))
    generation: Mapped[str] = mapped_column(String)
    source_record_id: Mapped[str] = mapped_column(String)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime)
    direction: Mapped[str] = mapped_column(String)
    waiting: Mapped[bool] = mapped_column(Boolean)
    unread: Mapped[bool] = mapped_column(Boolean)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)


# Source reply lookups and rebuild scans serve the same exact predicates as the
# services. Metadata and the additive migration both carry these indexes.
for field in ("message_id", "in_reply_to"):
    Index(
        f"ix_source_business_{field}",
        SourceRecord.tenant_id,
        SourceRecord.source_system,
        SourceRecord.source_type,
        func.md5(cast(SourceRecord.payload, JSONB)[field].astext),
    )
Index(
    "ix_source_business_scan",
    SourceRecord.tenant_id,
    SourceRecord.id,
    postgresql_where=text(
        "(source_type = 'email_message' AND (payload::jsonb)->>'direction' IN ('incoming','outgoing','inbound','outbound')) OR (source_system LIKE 'company/_simulator:%' ESCAPE '/' AND (source_type = 'incoming' OR (source_type = 'outgoing' AND (payload::jsonb)->>'direction' IN ('incoming','outgoing','inbound','outbound'))))"
    ),
)
Index(
    "ix_document_business_scan",
    Document.tenant_id,
    Document.id,
    postgresql_where=text("type = 'sales_order'"),
)
