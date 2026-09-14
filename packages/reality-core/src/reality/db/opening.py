"""Typed opening coverage and residual-item identity, never a stored balance."""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now


class OpeningScope(Base):
    __tablename__ = "opening_scope"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_opening_scope_tenant_id"),
        UniqueConstraint(
            "tenant_id",
            "source_namespace",
            "party_id",
            "direction",
            "currency",
            name="uq_opening_scope_coverage",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "party_id"],
            ["party.tenant_id", "party.id"],
            name="fk_opening_scope_party_tenant",
        ),
        CheckConstraint(
            "direction IN ('customer_debt','customer_credit','supplier_debt','supplier_credit')",
            name="ck_opening_scope_direction",
        ),
        CheckConstraint(
            "coverage_kind IN ('individual','summary')", name="ck_opening_scope_kind"
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    source_namespace: Mapped[str] = mapped_column(String)
    snapshot_key: Mapped[str] = mapped_column(String)
    cutover_date: Mapped[date] = mapped_column(Date)
    coverage_kind: Mapped[str] = mapped_column(String)
    party_id: Mapped[str] = mapped_column(String, index=True)
    direction: Mapped[str] = mapped_column(String)
    currency: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)


class OpeningItem(Base):
    __tablename__ = "opening_item_detail"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "scope_id",
            "external_item_key",
            name="uq_opening_item_identity",
        ),
        UniqueConstraint("document_id", name="uq_opening_item_document"),
        ForeignKeyConstraint(
            ["tenant_id", "scope_id"],
            ["opening_scope.tenant_id", "opening_scope.id"],
            name="fk_opening_item_scope_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["document.tenant_id", "document.id"],
            name="fk_opening_item_document_tenant",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)
    scope_id: Mapped[str] = mapped_column(String, index=True)
    document_id: Mapped[str] = mapped_column(String)
    external_item_key: Mapped[str] = mapped_column(String)
    original_due_date: Mapped[date | None] = mapped_column(Date, default=None)
