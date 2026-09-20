"""Retained receipt-cost evidence, owner decisions and exact review membership."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime, now


def _link(column: str, table: str):
    return ForeignKeyConstraint(
        ["tenant_id", column], [f"{table}.tenant_id", f"{table}.id"]
    )


# Existing records already use opaque global IDs. These keys additionally enforce
# same-tenant costing links at the database boundary.
for _table in (
    "movement",
    "movement_correction",
    "business_event",
    "interpretation_outcome",
):
    _target = Base.metadata.tables[_table]
    if not any(
        isinstance(c, UniqueConstraint)
        and [x.name for x in c.columns] == ["tenant_id", "id"]
        for c in _target.constraints
    ):
        _target.append_constraint(
            UniqueConstraint("tenant_id", "id", name=f"uq_cost_{_table}_tenant")
        )


class CostRecord:
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), index=True)


class CostReceiptBasis(CostRecord, Base):
    __tablename__ = "cost_receipt_basis"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "movement_id"),
        _link("movement_id", "movement"),
        _link("introduced_event_id", "business_event"),
        CheckConstraint("base_quantity>0", name="ck_cost_receipt_quantity"),
    )
    movement_id: Mapped[str] = mapped_column(String)
    introduced_event_id: Mapped[str] = mapped_column(String)
    base_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    base_unit: Mapped[str] = mapped_column(String)
    input_schema_version: Mapped[int] = mapped_column(default=1)


class CostComponentBasis(CostRecord, Base):
    __tablename__ = "cost_component_basis"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "component_id"),
        _link("component_id", "financial_component"),
        _link("introduced_event_id", "business_event"),
        _link("interpretation_outcome_id", "interpretation_outcome"),
    )
    component_id: Mapped[str] = mapped_column(String)
    introduced_event_id: Mapped[str] = mapped_column(String)
    interpretation_outcome_id: Mapped[str | None] = mapped_column(String)
    evidence_fingerprint: Mapped[str] = mapped_column(String(64))
    input_schema_version: Mapped[int] = mapped_column(default=1)


class CostConversionBasisRevision(CostRecord, Base):
    __tablename__ = "cost_conversion_basis_revision"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint(
            "tenant_id", "kind", "from_code", "to_code", "revision"
        ),
        UniqueConstraint("tenant_id", "supersedes_id"),
        _link("evidence_source_record_id", "source_record"),
        _link("supersedes_id", "cost_conversion_basis_revision"),
        _link("introduced_event_id", "business_event"),
        _link("action_id", "action"),
        CheckConstraint(
            "revision>0 AND kind IN ('unit','currency') AND from_code<>to_code AND numerator>0 AND denominator>0 AND input_schema_version=1",
            name="ck_cost_conversion_basis",
        ),
        CheckConstraint(
            "content_hash='building' OR length(content_hash)=64",
            name="ck_cost_conversion_hash",
        ),
    )
    evidence_source_record_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)
    from_code: Mapped[str] = mapped_column(String)
    to_code: Mapped[str] = mapped_column(String)
    numerator: Mapped[Decimal] = mapped_column(Numeric(28, 12))
    denominator: Mapped[Decimal] = mapped_column(Numeric(28, 12))
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime)
    revision: Mapped[int]
    supersedes_id: Mapped[str | None] = mapped_column(String)
    introduced_event_id: Mapped[str] = mapped_column(String)
    action_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    input_schema_version: Mapped[int]
    content_hash: Mapped[str] = mapped_column(String(64))


class CostAttribution(CostRecord, Base):
    __tablename__ = "cost_attribution_revision"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "component_basis_id", "revision"),
        UniqueConstraint("tenant_id", "supersedes_id"),
        _link("component_basis_id", "cost_component_basis"),
        _link("supersedes_id", "cost_attribution_revision"),
        _link("introduced_event_id", "business_event"),
        _link("action_id", "action"),
        CheckConstraint(
            "revision>0 AND state IN ('assigned','withdrawn') AND basis IN ('net','gross','base')",
            name="ck_cost_attribution_state",
        ),
        CheckConstraint(
            "tax_treatment IN ('recoverable','nonrecoverable','mixed','not_applicable','unknown') AND selected_basis_tax_inclusion IN ('included','excluded','unknown')",
            name="ck_cost_attribution_tax",
        ),
    )
    component_basis_id: Mapped[str] = mapped_column(String, index=True)
    revision: Mapped[int]
    supersedes_id: Mapped[str | None] = mapped_column(String)
    introduced_event_id: Mapped[str] = mapped_column(String)
    action_id: Mapped[str] = mapped_column(String)
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime, default=now)
    reason: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String)
    basis: Mapped[str] = mapped_column(String)
    tax_treatment: Mapped[str] = mapped_column(String)
    selected_basis_tax_inclusion: Mapped[str] = mapped_column(String)
    nonrecoverable_tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))


class CostAttributionPart(CostRecord, Base):
    __tablename__ = "cost_attribution_part"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint(
            "tenant_id",
            "attribution_revision_id",
            "receipt_basis_id",
            "amount_bucket",
            "category",
        ),
        _link("attribution_revision_id", "cost_attribution_revision"),
        _link("receipt_basis_id", "cost_receipt_basis"),
        _link("conversion_basis_revision_id", "cost_conversion_basis_revision"),
        CheckConstraint(
            "source_share<>0 AND cost_effect IN (-1,1)", name="ck_cost_part_amount"
        ),
        CheckConstraint(
            "amount_bucket IN ('selected_basis','nonrecoverable_tax') AND assignment_kind IN ('direct','allocated')",
            name="ck_cost_part_kind",
        ),
        CheckConstraint(
            "category IN ('goods','inbound_freight','duty','other_acquisition','purchase_reduction','nonrecoverable_tax')",
            name="ck_cost_part_category",
        ),
    )
    attribution_revision_id: Mapped[str] = mapped_column(String, index=True)
    receipt_basis_id: Mapped[str] = mapped_column(String, index=True)
    amount_bucket: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    source_share: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    cost_effect: Mapped[int]
    assignment_kind: Mapped[str] = mapped_column(String)
    conversion_basis_revision_id: Mapped[str | None] = mapped_column(String)


class CostComponentReplacement(CostRecord, Base):
    __tablename__ = "cost_component_replacement"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "previous_basis_id"),
        UniqueConstraint("tenant_id", "replacement_basis_id"),
        _link("previous_basis_id", "cost_component_basis"),
        _link("replacement_basis_id", "cost_component_basis"),
        _link("introduced_event_id", "business_event"),
        _link("action_id", "action"),
        CheckConstraint(
            "previous_basis_id<>replacement_basis_id",
            name="ck_cost_replacement_distinct",
        ),
    )
    previous_basis_id: Mapped[str] = mapped_column(String)
    replacement_basis_id: Mapped[str] = mapped_column(String)
    introduced_event_id: Mapped[str] = mapped_column(String)
    action_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)


class CostCorrectionBasis(CostRecord, Base):
    __tablename__ = "cost_correction_basis"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "movement_correction_id"),
        _link("movement_correction_id", "movement_correction"),
        _link("introduced_event_id", "business_event"),
    )
    movement_correction_id: Mapped[str] = mapped_column(String)
    introduced_event_id: Mapped[str] = mapped_column(String)
    input_schema_version: Mapped[int] = mapped_column(default=1)


class CostInputManifest(CostRecord, Base):
    __tablename__ = "cost_input_manifest"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        CheckConstraint(
            "state IN ('sealed') AND target_event_sequence>=0",
            name="ck_cost_manifest_state",
        ),
    )
    target_event_sequence: Mapped[int]
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime)
    knowledge_at: Mapped[datetime] = mapped_column(UTCDateTime)
    input_schema_version: Mapped[int]
    algorithm_version: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    content_hash: Mapped[str] = mapped_column(String(64))
    sealed_at: Mapped[datetime] = mapped_column(UTCDateTime)


class CostScopeReview(CostRecord, Base):
    __tablename__ = "cost_scope_review"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "receipt_basis_id", "revision"),
        UniqueConstraint("tenant_id", "supersedes_id"),
        _link("receipt_basis_id", "cost_receipt_basis"),
        _link("manifest_id", "cost_input_manifest"),
        _link("supersedes_id", "cost_scope_review"),
        _link("introduced_event_id", "business_event"),
        _link("action_id", "action"),
        CheckConstraint("revision>0", name="ck_cost_review_revision"),
    )
    receipt_basis_id: Mapped[str] = mapped_column(String, index=True)
    revision: Mapped[int]
    supersedes_id: Mapped[str | None] = mapped_column(String)
    manifest_id: Mapped[str] = mapped_column(String)
    introduced_event_id: Mapped[str] = mapped_column(String)
    action_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)


class CostReviewCategory(CostRecord, Base):
    __tablename__ = "cost_scope_review_category"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "review_id", "category"),
        _link("review_id", "cost_scope_review"),
        CheckConstraint(
            "disposition IN ('evidenced','confirmed_zero','not_applicable','unresolved')",
            name="ck_cost_review_disposition",
        ),
    )
    review_id: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String)
    disposition: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)


class CostManifestReceipt(CostRecord, Base):
    __tablename__ = "cost_manifest_receipt"
    __table_args__ = (
        UniqueConstraint("tenant_id", "manifest_id", "receipt_basis_id"),
        _link("manifest_id", "cost_input_manifest"),
        _link("receipt_basis_id", "cost_receipt_basis"),
    )
    manifest_id: Mapped[str] = mapped_column(String, index=True)
    receipt_basis_id: Mapped[str] = mapped_column(String)


class CostManifestComponent(CostRecord, Base):
    __tablename__ = "cost_manifest_component"
    __table_args__ = (
        UniqueConstraint("tenant_id", "manifest_id", "component_basis_id"),
        _link("manifest_id", "cost_input_manifest"),
        _link("component_basis_id", "cost_component_basis"),
    )
    manifest_id: Mapped[str] = mapped_column(String, index=True)
    component_basis_id: Mapped[str] = mapped_column(String)


class CostManifestAttribution(CostRecord, Base):
    __tablename__ = "cost_manifest_attribution"
    __table_args__ = (
        UniqueConstraint("tenant_id", "manifest_id", "attribution_revision_id"),
        _link("manifest_id", "cost_input_manifest"),
        _link("attribution_revision_id", "cost_attribution_revision"),
    )
    manifest_id: Mapped[str] = mapped_column(String, index=True)
    attribution_revision_id: Mapped[str] = mapped_column(String)


class CostManifestCorrection(CostRecord, Base):
    __tablename__ = "cost_manifest_correction"
    __table_args__ = (
        UniqueConstraint("tenant_id", "manifest_id", "correction_basis_id"),
        _link("manifest_id", "cost_input_manifest"),
        _link("correction_basis_id", "cost_correction_basis"),
    )
    manifest_id: Mapped[str] = mapped_column(String, index=True)
    correction_basis_id: Mapped[str] = mapped_column(String)


class CostManifestReplacement(CostRecord, Base):
    __tablename__ = "cost_manifest_replacement"
    __table_args__ = (
        UniqueConstraint("tenant_id", "manifest_id", "replacement_id"),
        _link("manifest_id", "cost_input_manifest"),
        _link("replacement_id", "cost_component_replacement"),
    )
    manifest_id: Mapped[str] = mapped_column(String, index=True)
    replacement_id: Mapped[str] = mapped_column(String)
