"""Retained current observations, distinct from admitted financial manifests."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime
from reality.db.costing import CostRecord, _link


class CostCompanyCensus(CostRecord, Base):
    __tablename__ = "cost_company_census"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "request_id"),
        CheckConstraint(
            "input_schema_version=1 AND event_sequence>=0 AND length(request_hash)=64 AND length(content_hash)=64",
            name="ck_company_census_version",
        ),
        CheckConstraint(
            "state IN ('building','sealed') AND ((state='sealed') = (sealed_at IS NOT NULL))",
            name="ck_company_census_state",
        ),
        CheckConstraint(
            "movement_count>=0 AND document_count>=0 AND line_count>=0 AND source_count>=0 AND movement_count+document_count+line_count+source_count<=100000",
            name="ck_company_census_counts",
        ),
    )
    request_id: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime)
    snapshot_identity: Mapped[str] = mapped_column(String)
    event_sequence: Mapped[int]
    input_schema_version: Mapped[int]
    state: Mapped[str] = mapped_column(String)
    movement_count: Mapped[int]
    document_count: Mapped[int]
    line_count: Mapped[int]
    source_count: Mapped[int]
    content_hash: Mapped[str] = mapped_column(String(64))
    sealed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class CostCompanyCensusMovement(CostRecord, Base):
    __tablename__ = "cost_company_census_movement"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "census_id", "id"),
        UniqueConstraint("tenant_id", "census_id", "movement_id"),
        _link("census_id", "cost_company_census"),
        _link("movement_id", "movement"),
        CheckConstraint("length(content_hash)=64", name="ck_census_movement_hash"),
    )
    census_id: Mapped[str] = mapped_column(String, index=True)
    movement_id: Mapped[str] = mapped_column(String, index=True)
    observed_values: Mapped[dict] = mapped_column(JSONB)
    content_hash: Mapped[str] = mapped_column(String(64))


class CostCompanyCensusDocument(CostRecord, Base):
    __tablename__ = "cost_company_census_document"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "census_id", "id"),
        UniqueConstraint("tenant_id", "census_id", "document_id"),
        _link("census_id", "cost_company_census"),
        _link("document_id", "document"),
        CheckConstraint("length(content_hash)=64", name="ck_census_document_hash"),
    )
    census_id: Mapped[str] = mapped_column(String, index=True)
    document_id: Mapped[str] = mapped_column(String, index=True)
    observed_values: Mapped[dict] = mapped_column(JSONB)
    content_hash: Mapped[str] = mapped_column(String(64))


class CostCompanyCensusLine(CostRecord, Base):
    __tablename__ = "cost_company_census_line"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "census_id", "id"),
        UniqueConstraint("tenant_id", "census_id", "document_line_id"),
        _link("census_id", "cost_company_census"),
        _link("document_line_id", "document_line"),
        CheckConstraint("length(content_hash)=64", name="ck_census_line_hash"),
        ForeignKeyConstraint(
            ["tenant_id", "census_id", "document_member_id"],
            [
                "cost_company_census_document.tenant_id",
                "cost_company_census_document.census_id",
                "cost_company_census_document.id",
            ],
        ),
    )
    census_id: Mapped[str] = mapped_column(String, index=True)
    document_line_id: Mapped[str] = mapped_column(String, index=True)
    observed_values: Mapped[dict] = mapped_column(JSONB)
    content_hash: Mapped[str] = mapped_column(String(64))
    document_member_id: Mapped[str] = mapped_column(String, index=True)


class CostCompanyCensusSource(CostRecord, Base):
    __tablename__ = "cost_company_census_source"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "census_id", "id"),
        UniqueConstraint("tenant_id", "census_id", "source_record_id"),
        _link("census_id", "cost_company_census"),
        _link("source_record_id", "source_record"),
        CheckConstraint("length(content_hash)=64", name="ck_census_source_hash"),
        _link("interpretation_outcome_id", "interpretation_outcome"),
    )
    census_id: Mapped[str] = mapped_column(String, index=True)
    source_record_id: Mapped[str] = mapped_column(String, index=True)
    observed_values: Mapped[dict] = mapped_column(JSONB)
    content_hash: Mapped[str] = mapped_column(String(64))
    interpretation_outcome_id: Mapped[str | None] = mapped_column(String, index=True)
