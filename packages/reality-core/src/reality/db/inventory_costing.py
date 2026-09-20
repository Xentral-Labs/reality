"""Confirmed inventory scope and retained inputs; never calculated value authority."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime
from reality.db.costing import CostRecord, _link

Index(
    "ix_cost_movement_pool_cutoff",
    Base.metadata.tables["movement"].c.tenant_id,
    Base.metadata.tables["movement"].c.item_id,
    Base.metadata.tables["movement"].c.occurred_at,
    Base.metadata.tables["movement"].c.id,
)

for _name in ("item", "party", "source_record"):
    _table = Base.metadata.tables[_name]
    if not any(
        isinstance(c, UniqueConstraint)
        and [x.name for x in c.columns] == ["tenant_id", "id"]
        for c in _table.constraints
    ):
        _table.append_constraint(
            UniqueConstraint("tenant_id", "id", name=f"uq_inventory_{_name}_tenant")
        )


class _Decision(CostRecord):
    introduced_event_id: Mapped[str] = mapped_column(String)
    action_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)


class CostPolicyRevision(_Decision, Base):
    __tablename__ = "cost_policy_revision"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "item_id", "revision"),
        UniqueConstraint("tenant_id", "supersedes_id"),
        _link("item_id", "item"),
        _link("owner_party_id", "party"),
        _link("supersedes_id", "cost_policy_revision"),
        _link("introduced_event_id", "business_event"),
        _link("action_id", "action"),
        CheckConstraint(
            "revision>0 AND method IN ('fifo','specific')",
            name="ck_inventory_policy",
        ),
    )
    item_id: Mapped[str] = mapped_column(String, index=True)
    owner_party_id: Mapped[str] = mapped_column(String)
    revision: Mapped[int]
    supersedes_id: Mapped[str | None] = mapped_column(String)
    method: Mapped[str] = mapped_column(String)
    currency: Mapped[str] = mapped_column(String)
    base_unit: Mapped[str] = mapped_column(String)
    history_start: Mapped[datetime] = mapped_column(UTCDateTime)


class CostMovementBasis(CostRecord, Base):
    __tablename__ = "cost_movement_basis"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "movement_id"),
        _link("movement_id", "movement"),
        _link("movement_event_id", "business_event"),
        _link("introduced_event_id", "business_event"),
        CheckConstraint(
            "base_quantity>0 AND movement_type IN ('receipt','shipment','transfer','return','supplier_return','adjustment','opening_stock') AND input_schema_version=1",
            name="ck_inventory_movement",
        ),
    )
    movement_id: Mapped[str] = mapped_column(String)
    movement_event_id: Mapped[str] = mapped_column(String)
    introduced_event_id: Mapped[str] = mapped_column(String)
    movement_type: Mapped[str] = mapped_column(String)
    base_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    base_unit: Mapped[str] = mapped_column(String)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime)
    input_schema_version: Mapped[int] = mapped_column(default=1)


class CostOwnershipRevision(_Decision, Base):
    __tablename__ = "cost_ownership_revision"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "receipt_basis_id", "revision"),
        UniqueConstraint("tenant_id", "supersedes_id"),
        _link("receipt_basis_id", "cost_receipt_basis"),
        _link("owner_party_id", "party"),
        _link("evidence_source_record_id", "source_record"),
        _link("supersedes_id", "cost_ownership_revision"),
        _link("introduced_event_id", "business_event"),
        _link("action_id", "action"),
        CheckConstraint(
            "revision>0 AND covered_quantity>0", name="ck_inventory_ownership"
        ),
    )
    receipt_basis_id: Mapped[str] = mapped_column(String, index=True)
    owner_party_id: Mapped[str] = mapped_column(String)
    evidence_source_record_id: Mapped[str] = mapped_column(String)
    covered_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    revision: Mapped[int]
    supersedes_id: Mapped[str | None] = mapped_column(String)


class CostOpeningBasis(_Decision, Base):
    __tablename__ = "cost_opening_basis"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "movement_basis_id"),
        _link("movement_basis_id", "cost_movement_basis"),
        _link("owner_party_id", "party"),
        _link("evidence_source_record_id", "source_record"),
        _link("introduced_event_id", "business_event"),
        _link("action_id", "action"),
        CheckConstraint(
            "acquisition_cost>=0 AND input_schema_version=1",
            name="ck_inventory_opening",
        ),
    )
    movement_basis_id: Mapped[str] = mapped_column(String)
    owner_party_id: Mapped[str] = mapped_column(String)
    evidence_source_record_id: Mapped[str] = mapped_column(String)
    acquisition_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String)
    input_schema_version: Mapped[int] = mapped_column(default=1)


class CostInventoryReview(_Decision, Base):
    __tablename__ = "cost_inventory_review"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "policy_id"),
        _link("policy_id", "cost_policy_revision"),
        _link("introduced_event_id", "business_event"),
        _link("action_id", "action"),
        CheckConstraint(
            "target_event_sequence>=0 AND input_schema_version=1 AND algorithm_version='inventory-v1'",
            name="ck_inventory_review",
        ),
    )
    policy_id: Mapped[str] = mapped_column(String)
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime)
    target_event_sequence: Mapped[int]
    knowledge_at: Mapped[datetime] = mapped_column(UTCDateTime)
    algorithm_version: Mapped[str] = mapped_column(String)
    input_schema_version: Mapped[int]
    content_hash: Mapped[str] = mapped_column(String(64))


class CostInventoryOwnershipPart(CostRecord, Base):
    __tablename__ = "cost_inventory_ownership_part"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint(
            "tenant_id", "review_id", "movement_basis_id", "owner_party_id"
        ),
        _link("review_id", "cost_inventory_review"),
        _link("movement_basis_id", "cost_movement_basis"),
        _link("owner_party_id", "party"),
        _link("evidence_source_record_id", "source_record"),
        CheckConstraint(
            "quantity>0 AND input_schema_version=1",
            name="ck_inventory_ownership_part",
        ),
    )
    review_id: Mapped[str] = mapped_column(String, index=True)
    movement_basis_id: Mapped[str] = mapped_column(String)
    owner_party_id: Mapped[str] = mapped_column(String)
    evidence_source_record_id: Mapped[str] = mapped_column(String)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    input_schema_version: Mapped[int] = mapped_column(default=1)


class CostInventoryMember(CostRecord, Base):
    __tablename__ = "cost_inventory_member"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "review_id", "movement_basis_id"),
        _link("review_id", "cost_inventory_review"),
        _link("movement_basis_id", "cost_movement_basis"),
        _link("receipt_manifest_id", "cost_input_manifest"),
        _link("ownership_revision_id", "cost_ownership_revision"),
        CheckConstraint(
            "(kind='receipt' AND receipt_manifest_id IS NOT NULL AND ownership_revision_id IS NOT NULL) OR (kind IN ('issue','transfer','loss','supplier_return','customer_return','opening') AND receipt_manifest_id IS NULL AND ownership_revision_id IS NULL)",
            name="ck_inventory_member",
        ),
    )
    review_id: Mapped[str] = mapped_column(String, index=True)
    movement_basis_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)
    receipt_manifest_id: Mapped[str | None] = mapped_column(String)
    ownership_revision_id: Mapped[str | None] = mapped_column(String)


class CostValuationAssessmentRevision(_Decision, Base):
    __tablename__ = "cost_valuation_assessment_revision"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "inventory_review_id", "revision"),
        UniqueConstraint("tenant_id", "supersedes_id"),
        _link("inventory_review_id", "cost_inventory_review"),
        _link("supersedes_id", "cost_valuation_assessment_revision"),
        _link("introduced_event_id", "business_event"),
        _link("action_id", "action"),
        CheckConstraint(
            "revision>0 AND kind IN ('write_down','recovery') AND target_event_sequence>=0 AND input_schema_version=1",
            name="ck_valuation_assessment_revision",
        ),
        CheckConstraint(
            "(kind='write_down' AND supersedes_id IS NULL) OR (kind='recovery' AND supersedes_id IS NOT NULL)",
            name="ck_valuation_assessment_predecessor",
        ),
        CheckConstraint(
            "content_hash='building' OR length(content_hash)=64",
            name="ck_valuation_assessment_hash",
        ),
    )
    inventory_review_id: Mapped[str] = mapped_column(String, index=True)
    revision: Mapped[int]
    supersedes_id: Mapped[str | None] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime)
    target_event_sequence: Mapped[int]
    knowledge_at: Mapped[datetime] = mapped_column(UTCDateTime)
    input_schema_version: Mapped[int]
    content_hash: Mapped[str] = mapped_column(String(64))


class CostValuationAssessmentPart(CostRecord, Base):
    __tablename__ = "cost_valuation_assessment_part"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint(
            "tenant_id", "assessment_revision_id", "inventory_member_id"
        ),
        _link("assessment_revision_id", "cost_valuation_assessment_revision"),
        _link("inventory_member_id", "cost_inventory_member"),
        _link("evidence_source_record_id", "source_record"),
        CheckConstraint(
            "quantity>0 AND assessed_value>=0 AND input_schema_version=1",
            name="ck_valuation_assessment_part",
        ),
    )
    assessment_revision_id: Mapped[str] = mapped_column(String, index=True)
    inventory_member_id: Mapped[str] = mapped_column(String)
    evidence_source_record_id: Mapped[str] = mapped_column(String)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    assessed_value: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String)
    input_schema_version: Mapped[int] = mapped_column(default=1)
