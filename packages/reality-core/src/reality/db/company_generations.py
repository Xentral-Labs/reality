"""Retained financial company inputs and disposable exact-population observations."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now
from reality.db.costing import CostRecord, _link


class CostCompanyManifest(CostRecord, Base):
    __tablename__ = "cost_company_manifest"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "scope_key", "content_hash"),
        _link("census_id", "cost_company_census"),
        CheckConstraint(
            "state IN ('building','sealed') AND ((state='sealed') = (sealed_at IS NOT NULL))",
            name="ck_company_manifest_state",
        ),
        CheckConstraint(
            "target_event_sequence>=0 AND inventory_count>=0 AND contribution_count>=0 AND header_gap_count>=0 AND source_gap_count>=0",
            name="ck_company_manifest_counts",
        ),
        CheckConstraint(
            "length(scope_key)=64 AND length(population_digest)=64 AND length(gap_digest)=64 AND length(content_hash)=64",
            name="ck_company_manifest_hashes",
        ),
    )
    census_id: Mapped[str] = mapped_column(String)
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime)
    knowledge_at: Mapped[datetime] = mapped_column(UTCDateTime)
    target_event_sequence: Mapped[int]
    inventory_algorithm_version: Mapped[str] = mapped_column(String)
    contribution_algorithm_version: Mapped[str] = mapped_column(String)
    scope_key: Mapped[str] = mapped_column(String(64))
    population_digest: Mapped[str] = mapped_column(String(64))
    inventory_count: Mapped[int]
    contribution_count: Mapped[int]
    header_gap_count: Mapped[int]
    source_gap_count: Mapped[int]
    gap_digest: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String)
    sealed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    content_hash: Mapped[str] = mapped_column(String(64))


class CostCompanyInventoryInput(CostRecord, Base):
    __tablename__ = "cost_company_inventory_input"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "manifest_id", "id"),
        UniqueConstraint("tenant_id", "manifest_id", "item_id"),
        _link("manifest_id", "cost_company_manifest"),
        _link("item_id", "item"),
        _link("review_id", "cost_inventory_review"),
        CheckConstraint(
            "support_state IN ('known','unknown') AND ((support_state='known') = (review_id IS NOT NULL)) AND length(input_fingerprint)=64",
            name="ck_company_inventory_input_shape",
        ),
    )
    manifest_id: Mapped[str] = mapped_column(String, index=True)
    item_id: Mapped[str] = mapped_column(String)
    review_id: Mapped[str | None] = mapped_column(String)
    input_fingerprint: Mapped[str] = mapped_column(String(64))
    support_state: Mapped[str] = mapped_column(String)


class CostCompanyContributionInput(CostRecord, Base):
    __tablename__ = "cost_company_contribution_input"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "manifest_id", "id"),
        UniqueConstraint("tenant_id", "manifest_id", "census_line_id"),
        _link("manifest_id", "cost_company_manifest"),
        _link("census_line_id", "cost_company_census_line"),
        _link("review_id", "cost_contribution_review"),
        _link("inventory_review_id", "cost_inventory_review"),
        CheckConstraint(
            "db1_state IN ('known','unknown') AND db2_state IN ('known','unknown') AND NOT (db2_state='known' AND db1_state='unknown') AND ((db1_state='known') = (review_id IS NOT NULL)) AND length(input_fingerprint)=64",
            name="ck_company_contribution_input_shape",
        ),
    )
    manifest_id: Mapped[str] = mapped_column(String, index=True)
    census_line_id: Mapped[str] = mapped_column(String)
    review_id: Mapped[str | None] = mapped_column(String)
    inventory_review_id: Mapped[str | None] = mapped_column(String)
    input_fingerprint: Mapped[str] = mapped_column(String(64))
    db1_state: Mapped[str] = mapped_column(String)
    db2_state: Mapped[str] = mapped_column(String)


class CostCompanyGeneration(CostRecord, Base):
    __tablename__ = "cost_company_generation"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "scope_key", "id"),
        UniqueConstraint("tenant_id", "manifest_id", "algorithm_bundle"),
        _link("manifest_id", "cost_company_manifest"),
        CheckConstraint(
            "state IN ('building','sealed') AND ((state='sealed') = (completed_at IS NOT NULL))",
            name="ck_company_generation_state",
        ),
        CheckConstraint(
            "expected_work_count>=0 AND completed_work_count>=0 AND completed_work_count<=expected_work_count AND inventory_count>=0 AND contribution_count>=0",
            name="ck_company_generation_counts",
        ),
        CheckConstraint(
            "length(scope_key)=64 AND length(inventory_content_hash)=64 AND length(contribution_content_hash)=64",
            name="ck_company_generation_hashes",
        ),
    )
    manifest_id: Mapped[str] = mapped_column(String, index=True)
    algorithm_bundle: Mapped[str] = mapped_column(String)
    scope_key: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String)
    expected_work_count: Mapped[int]
    completed_work_count: Mapped[int]
    inventory_count: Mapped[int]
    contribution_count: Mapped[int]
    inventory_content_hash: Mapped[str] = mapped_column(String(64))
    contribution_content_hash: Mapped[str] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class CostCompanyInventoryResult(CostRecord, Base):
    __tablename__ = "cost_company_inventory_result"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "generation_id", "inventory_input_id"),
        _link("generation_id", "cost_company_generation"),
        _link("inventory_input_id", "cost_company_inventory_input"),
        _link("inventory_generation_id", "cost_inventory_generation"),
        CheckConstraint(
            "state IN ('known','unknown') AND ((state='known') = (inventory_generation_id IS NOT NULL)) AND length(result_fingerprint)=64",
            name="ck_company_inventory_result_shape",
        ),
    )
    generation_id: Mapped[str] = mapped_column(String, index=True)
    inventory_input_id: Mapped[str] = mapped_column(String)
    inventory_generation_id: Mapped[str | None] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    result_fingerprint: Mapped[str] = mapped_column(String(64))


class CostCompanyContributionResult(CostRecord, Base):
    __tablename__ = "cost_company_contribution_result"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "generation_id", "contribution_input_id"),
        _link("generation_id", "cost_company_generation"),
        _link("contribution_input_id", "cost_company_contribution_input"),
        _link("contribution_generation_id", "cost_contribution_generation"),
        _link("review_id", "cost_contribution_review"),
        CheckConstraint(
            "db1_state IN ('known','unknown') AND db2_state IN ('known','unknown') AND NOT (db2_state='known' AND db1_state='unknown') AND ((db1_state='known') = (contribution_generation_id IS NOT NULL AND review_id IS NOT NULL)) AND length(result_fingerprint)=64",
            name="ck_company_contribution_result_shape",
        ),
    )
    generation_id: Mapped[str] = mapped_column(String, index=True)
    contribution_input_id: Mapped[str] = mapped_column(String)
    contribution_generation_id: Mapped[str | None] = mapped_column(String)
    review_id: Mapped[str | None] = mapped_column(String)
    db1_state: Mapped[str] = mapped_column(String)
    db2_state: Mapped[str] = mapped_column(String)
    result_fingerprint: Mapped[str] = mapped_column(String(64))


class CostCompanyPublication(CostRecord, Base):
    __tablename__ = "cost_company_publication"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "scope_key"),
        ForeignKeyConstraint(
            ["tenant_id", "scope_key", "generation_id"],
            [
                "cost_company_generation.tenant_id",
                "cost_company_generation.scope_key",
                "cost_company_generation.id",
            ],
        ),
    )
    scope_key: Mapped[str] = mapped_column(String(64))
    generation_id: Mapped[str] = mapped_column(String, index=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
