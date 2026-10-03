"""Current scoped delegation, linked to its actual owner decision and named token."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now


class IntakeReviewMandate(Base):
    __tablename__ = "intake_review_mandate"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "grant_decision_id"], ["action.tenant_id", "action.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "agent_token_id"],
            ["mcp_access_token.tenant_id", "mcp_access_token.id"],
        ),
        UniqueConstraint(
            "tenant_id", "grant_decision_id", name="uq_intake_mandate_grant_decision"
        ),
        CheckConstraint("revision >= 1", name="ck_intake_mandate_revision"),
        CheckConstraint("expires_at > created_at", name="ck_intake_mandate_expiry"),
        CheckConstraint(
            "jsonb_typeof(scope) = 'object'", name="ck_intake_mandate_scope"
        ),
    )
    id: Mapped[str] = mapped_column(String)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    grant_decision_id: Mapped[str] = mapped_column(String)
    agent_token_id: Mapped[str] = mapped_column(String)
    scope: Mapped[dict] = mapped_column(JSONB)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
