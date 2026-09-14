"""An ordinary company's creation receipt, not business authority."""

from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now


class OrdinaryCompanyCreation(Base):
    __tablename__ = "ordinary_company_creation"
    __table_args__ = (
        UniqueConstraint("actor_id", "request_key", name="uq_company_creation_request"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), unique=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("app_user.id"))
    request_key: Mapped[str] = mapped_column(String(128))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
