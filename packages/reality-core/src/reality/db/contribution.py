"""Retained full-line revenue binding and confirmed commercial review membership."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from reality.db.core import Base, UTCDateTime
from reality.db.costing import CostRecord, _link


class CostRevenueMatchBasis(CostRecord, Base):
    __tablename__ = "cost_revenue_match_basis"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "document_line_id"),
        UniqueConstraint("tenant_id", "movement_basis_id"),
        _link("document_line_id", "document_line"),
        _link("order_line_id", "document_line"),
        _link("movement_basis_id", "cost_movement_basis"),
        _link("item_id", "item"),
        _link("customer_id", "party"),
        _link("introduced_event_id", "business_event"),
        CheckConstraint(
            "quantity>0 AND stated_net>=0 AND input_schema_version=1",
            name="ck_revenue_match_basis",
        ),
    )
    document_line_id: Mapped[str] = mapped_column(String)
    order_line_id: Mapped[str] = mapped_column(String)
    movement_basis_id: Mapped[str] = mapped_column(String)
    item_id: Mapped[str] = mapped_column(String)
    customer_id: Mapped[str] = mapped_column(String)
    stated_net: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String)
    base_unit: Mapped[str] = mapped_column(String)
    invoice_date: Mapped[date | None] = mapped_column(Date, default=None)
    sales_channel: Mapped[str] = mapped_column(String)
    evidence_hash: Mapped[str] = mapped_column(String(64))
    input_schema_version: Mapped[int]
    introduced_event_id: Mapped[str] = mapped_column(String)


class CostContributionReview(CostRecord, Base):
    __tablename__ = "cost_contribution_review"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "revenue_basis_id", "revision"),
        UniqueConstraint("tenant_id", "supersedes_id"),
        _link("revenue_basis_id", "cost_revenue_match_basis"),
        _link("inventory_member_id", "cost_inventory_member"),
        _link("supersedes_id", "cost_contribution_review"),
        _link("introduced_event_id", "business_event"),
        _link("action_id", "action"),
        CheckConstraint(
            "revision>0 AND profile='commercial_v1' AND event_sequence>=0",
            name="ck_contribution_review",
        ),
    )
    revenue_basis_id: Mapped[str] = mapped_column(String, index=True)
    inventory_member_id: Mapped[str] = mapped_column(String)
    revision: Mapped[int]
    supersedes_id: Mapped[str | None] = mapped_column(String)
    profile: Mapped[str] = mapped_column(String)
    economic_at: Mapped[datetime] = mapped_column(UTCDateTime)
    knowledge_at: Mapped[datetime] = mapped_column(UTCDateTime)
    introduced_event_id: Mapped[str] = mapped_column(String)
    event_sequence: Mapped[int]
    action_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))


class CostCommercialMatchRevision(CostRecord, Base):
    __tablename__ = "cost_commercial_match_revision"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "document_line_id", "revision"),
        UniqueConstraint("tenant_id", "supersedes_id"),
        _link("document_line_id", "document_line"),
        _link("order_line_id", "document_line"),
        _link("supersedes_id", "cost_commercial_match_revision"),
        _link("introduced_event_id", "business_event"),
        _link("action_id", "action"),
        CheckConstraint(
            "revision>0 AND stated_quantity<>0 AND profile='commercial_v1' AND input_schema_version=1",
            name="ck_commercial_match_revision",
        ),
        CheckConstraint(
            "goods_cost_disposition IN ('inventory','direct_evidence','not_applicable','unresolved')",
            name="ck_commercial_match_disposition",
        ),
        CheckConstraint(
            "content_hash='building' OR length(content_hash)=64",
            name="ck_commercial_match_hash",
        ),
    )
    document_line_id: Mapped[str] = mapped_column(String, index=True)
    order_line_id: Mapped[str | None] = mapped_column(String)
    revision: Mapped[int]
    supersedes_id: Mapped[str | None] = mapped_column(String)
    stated_net: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    stated_quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String)
    base_unit: Mapped[str | None] = mapped_column(String)
    evidence_hash: Mapped[str] = mapped_column(String(64))
    goods_cost_disposition: Mapped[str] = mapped_column(String)
    profile: Mapped[str] = mapped_column(String)
    introduced_event_id: Mapped[str] = mapped_column(String)
    action_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    input_schema_version: Mapped[int]
    content_hash: Mapped[str] = mapped_column(String(64))


class CostCommercialInventoryPart(CostRecord, Base):
    __tablename__ = "cost_commercial_inventory_part"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint(
            "tenant_id",
            "match_revision_id",
            "inventory_member_id",
            "entry_movement_basis_id",
            "receipt_movement_basis_id",
        ),
        _link("match_revision_id", "cost_commercial_match_revision"),
        _link("inventory_member_id", "cost_inventory_member"),
        _link("original_issue_member_id", "cost_inventory_member"),
        _link("entry_movement_basis_id", "cost_movement_basis"),
        _link("receipt_movement_basis_id", "cost_movement_basis"),
        CheckConstraint(
            "quantity>0 AND input_schema_version=1",
            name="ck_commercial_inventory_part",
        ),
    )
    match_revision_id: Mapped[str] = mapped_column(String, index=True)
    inventory_member_id: Mapped[str] = mapped_column(String)
    original_issue_member_id: Mapped[str | None] = mapped_column(String)
    entry_movement_basis_id: Mapped[str] = mapped_column(String)
    receipt_movement_basis_id: Mapped[str] = mapped_column(String)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    input_schema_version: Mapped[int]


class CostCommercialDirectPart(CostRecord, Base):
    __tablename__ = "cost_commercial_direct_part"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint(
            "tenant_id", "match_revision_id", "attribution_revision_id", "input_role"
        ),
        _link("match_revision_id", "cost_commercial_match_revision"),
        _link("attribution_revision_id", "cost_attribution_revision"),
        CheckConstraint(
            "input_role IN ('service_input','shipping_input','kit_input','production_input') AND input_schema_version=1",
            name="ck_commercial_direct_part",
        ),
    )
    match_revision_id: Mapped[str] = mapped_column(String, index=True)
    attribution_revision_id: Mapped[str] = mapped_column(String)
    input_role: Mapped[str] = mapped_column(String)
    input_schema_version: Mapped[int]


class CostSellingPart(CostRecord, Base):
    __tablename__ = "cost_selling_attribution_part"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint(
            "tenant_id", "attribution_revision_id", "document_line_id", "category"
        ),
        _link("attribution_revision_id", "cost_attribution_revision"),
        _link("document_line_id", "document_line"),
        _link("conversion_basis_revision_id", "cost_conversion_basis_revision"),
        CheckConstraint(
            "source_share<>0 AND cost_effect IN (-1,1)", name="ck_selling_part_amount"
        ),
        CheckConstraint(
            "assignment_kind IN ('direct','allocated')", name="ck_selling_part_kind"
        ),
        CheckConstraint(
            "category IN ('outbound_freight','fulfilment','packaging','payment_fee','marketplace_commission','sales_commission','other_selling')",
            name="ck_selling_part_category",
        ),
    )
    attribution_revision_id: Mapped[str] = mapped_column(String, index=True)
    document_line_id: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    source_share: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    cost_effect: Mapped[int]
    assignment_kind: Mapped[str] = mapped_column(String)
    conversion_basis_revision_id: Mapped[str | None] = mapped_column(String)


class CostSellingReviewCategory(CostRecord, Base):
    __tablename__ = "cost_selling_review_category"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "review_id", "category"),
        _link("review_id", "cost_contribution_review"),
        CheckConstraint(
            "disposition IN ('evidenced','confirmed_zero','not_applicable','unresolved')",
            name="ck_selling_review_disposition",
        ),
        CheckConstraint(
            "category IN ('outbound_freight','fulfilment','packaging','payment_fee','marketplace_commission','sales_commission','other_selling')",
            name="ck_selling_review_category",
        ),
    )
    review_id: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String)
    disposition: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)


class CostSellingReviewMember(CostRecord, Base):
    __tablename__ = "cost_selling_review_member"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "review_id", "part_id"),
        _link("review_id", "cost_contribution_review"),
        _link("part_id", "cost_selling_attribution_part"),
    )
    review_id: Mapped[str] = mapped_column(String, index=True)
    part_id: Mapped[str] = mapped_column(String)
