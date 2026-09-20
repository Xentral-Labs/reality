"""Immutable pinned captured-review selections, separate from financial authority."""

from datetime import datetime

from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime
from reality.db.costing import CostRecord, _link


class CostCapturedBasis(CostRecord, Base):
    __tablename__ = "cost_captured_basis"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "request_id"),
        _link("census_id", "cost_company_census"),
        CheckConstraint(
            "basis_version='captured-review-basis-v2' AND length(request_hash)=64 AND length(basis_digest)=64",
            name="ck_captured_basis_version",
        ),
        CheckConstraint(
            "state IN ('building','sealed') AND ((state='sealed') = (sealed_at IS NOT NULL))",
            name="ck_captured_basis_state",
        ),
        CheckConstraint(
            "inventory_count>=0 AND contribution_count>=0 AND inventory_count+contribution_count<=10",
            name="ck_captured_basis_counts",
        ),
    )
    census_id: Mapped[str] = mapped_column(String, index=True)
    request_id: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    basis_version: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    sealed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    inventory_count: Mapped[int]
    contribution_count: Mapped[int]
    basis_digest: Mapped[str] = mapped_column(String(64))
    observations: Mapped[dict] = mapped_column(JSONB)


class CostCapturedInventoryBasis(CostRecord, Base):
    __tablename__ = "cost_captured_inventory_basis"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "basis_id", "item_id"),
        _link("basis_id", "cost_captured_basis"),
        _link("item_id", "item"),
        _link("review_id", "cost_inventory_review"),
        CheckConstraint("length(content_hash)=64", name="ck_captured_inventory_hash"),
    )
    basis_id: Mapped[str] = mapped_column(String, index=True)
    item_id: Mapped[str] = mapped_column(String, index=True)
    review_id: Mapped[str | None] = mapped_column(String, index=True)
    observations: Mapped[dict] = mapped_column(JSONB)
    content_hash: Mapped[str] = mapped_column(String(64))


class CostCapturedContributionBasis(CostRecord, Base):
    __tablename__ = "cost_captured_contribution_basis"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "basis_id", "document_line_id"),
        _link("basis_id", "cost_captured_basis"),
        _link("document_line_id", "document_line"),
        _link("review_id", "cost_contribution_review"),
        CheckConstraint(
            "length(content_hash)=64", name="ck_captured_contribution_hash"
        ),
    )
    basis_id: Mapped[str] = mapped_column(String, index=True)
    document_line_id: Mapped[str] = mapped_column(String, index=True)
    review_id: Mapped[str | None] = mapped_column(String, index=True)
    observations: Mapped[dict] = mapped_column(JSONB)
    content_hash: Mapped[str] = mapped_column(String(64))
