"""Typed receipt-cost decisions; received amounts retain their original signs."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, Decimal
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)

CATEGORIES = (
    "goods",
    "inbound_freight",
    "duty",
    "other_acquisition",
    "purchase_reduction",
    "nonrecoverable_tax",
)
Category = Literal[
    "goods",
    "inbound_freight",
    "duty",
    "other_acquisition",
    "purchase_reduction",
    "nonrecoverable_tax",
]
Amount = Annotated[Decimal, Field(max_digits=18, decimal_places=4, allow_inf_nan=False)]
ALLOCATION_INCREMENT = Decimal("0.0001")


class CostingRefusal(ValueError):
    """Refuse arithmetic that would invent or silently truncate costing inputs."""


@dataclass(frozen=True)
class AllocationTarget:
    target_id: str
    weight: Decimal


@dataclass(frozen=True)
class WeightedAllocation:
    shares: dict[str, Decimal]
    allocated: Decimal
    unassigned: Decimal


def _decimal_places(value: Decimal) -> int:
    return max(0, -value.as_tuple().exponent)


def _four_place(value: Decimal, label: str) -> None:
    if not value.is_finite() or _decimal_places(value) > 4:
        raise CostingRefusal(f"{label} must fit the four decimal contract.")


def allocate_weighted(
    source_capacity: Decimal,
    allocation_total: Decimal,
    targets: list[AllocationTarget],
) -> WeightedAllocation:
    """Allocate an explicit signed total using stable largest remainders."""
    _four_place(source_capacity, "Source capacity")
    _four_place(allocation_total, "Allocation total")
    if not targets:
        raise CostingRefusal("At least one allocation target is required.")
    identities = [target.target_id for target in targets]
    if any(not identity for identity in identities):
        raise CostingRefusal("Every allocation target requires an opaque identity.")
    if len(set(identities)) != len(identities):
        raise CostingRefusal("Duplicate allocation target.")
    if any(not target.weight.is_finite() or target.weight <= 0 for target in targets):
        raise CostingRefusal("Allocation weights must be positive.")
    if allocation_total == 0:
        raise CostingRefusal("A zero allocation belongs in explicit scope review.")
    if source_capacity == 0 or (source_capacity > 0) != (allocation_total > 0):
        raise CostingRefusal("Allocation total must preserve the source bucket sign.")
    if abs(allocation_total) > abs(source_capacity):
        raise CostingRefusal("Allocation total exceeds the received source capacity.")

    magnitude = abs(allocation_total)
    weight_total = sum((target.weight for target in targets), Decimal(0))
    prepared = []
    for target in targets:
        exact = magnitude * target.weight / weight_total
        base = exact.quantize(ALLOCATION_INCREMENT, rounding=ROUND_DOWN)
        prepared.append((target.target_id, base, exact - base))
    assigned = sum((base for _, base, _ in prepared), Decimal(0))
    increments = int((magnitude - assigned) / ALLOCATION_INCREMENT)
    ranked = sorted(prepared, key=lambda row: (-row[2], row[0]))
    bonuses = {identity for identity, _, _ in ranked[:increments]}
    sign = Decimal(1) if allocation_total > 0 else Decimal(-1)
    shares = {
        identity: (base + (ALLOCATION_INCREMENT if identity in bonuses else 0))
        * sign
        for identity, base, _ in prepared
    }
    allocated = sum(shares.values(), Decimal(0))
    return WeightedAllocation(
        shares=shares,
        allocated=allocated,
        unassigned=source_capacity - allocated,
    )


def _conversion(value: Decimal, numerator: Decimal, denominator: Decimal) -> Decimal:
    if any(not part.is_finite() or part <= 0 for part in (numerator, denominator)):
        raise CostingRefusal("Conversion numerator and denominator must be positive.")
    if any(_decimal_places(part) > 12 for part in (numerator, denominator)):
        raise CostingRefusal("Conversion ratios support at most twelve decimal places.")
    if any(len(part.as_tuple().digits) > 28 for part in (numerator, denominator)):
        raise CostingRefusal("Conversion ratios support at most 28 digits.")
    return value * numerator / denominator


def convert_amount(value: Decimal, numerator: Decimal, denominator: Decimal) -> Decimal:
    """Derive a four-place monetary observation from an exact retained ratio."""
    _four_place(value, "Source amount")
    return _conversion(value, numerator, denominator).quantize(
        ALLOCATION_INCREMENT, rounding=ROUND_HALF_EVEN
    )


def convert_quantity(value: Decimal, numerator: Decimal, denominator: Decimal) -> Decimal:
    """Convert quantity only when the result fits the existing exact contract."""
    _four_place(value, "Source quantity")
    converted = _conversion(value, numerator, denominator)
    rounded = converted.quantize(ALLOCATION_INCREMENT, rounding=ROUND_HALF_EVEN)
    if converted != rounded:
        raise CostingRefusal("Converted quantity must fit the four decimal contract.")
    return rounded


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CostPart(Request):
    movement_id: str = Field(min_length=1)
    category: Category
    source_share: Amount
    cost_effect: Literal[-1, 1]
    amount_bucket: Literal["selected_basis", "nonrecoverable_tax"] = "selected_basis"
    assignment_kind: Literal["direct", "allocated"] = "direct"
    conversion_basis_revision_id: str | None = None

    @model_validator(mode="after")
    def semantic_effect(self):
        if self.source_share == 0:
            raise ValueError(
                "Zero belongs in an explicit scope review, not an allocation part."
            )
        if self.category != "nonrecoverable_tax" and self.cost_effect != (
            -1 if self.category == "purchase_reduction" else 1
        ):
            raise ValueError("Cost effect contradicts the selected category.")
        if (self.amount_bucket == "nonrecoverable_tax") != (
            self.category == "nonrecoverable_tax"
        ):
            raise ValueError("Tax parts require the independent received-tax bucket.")
        return self


def contribution(part: CostPart) -> Decimal:
    return abs(part.source_share) * part.cost_effect


def validate_shares(parts: list[CostPart], basis: Decimal, tax: Decimal) -> None:
    seen = set()
    for bucket, capacity in (("selected_basis", basis), ("nonrecoverable_tax", tax)):
        selected = [p for p in parts if p.amount_bucket == bucket]
        for part in selected:
            key = (part.movement_id, part.category, bucket)
            if key in seen:
                raise ValueError("Duplicate target/category/bucket.")
            seen.add(key)
            if capacity == 0 or (part.source_share > 0) != (capacity > 0):
                raise ValueError("Shares must preserve their source bucket sign.")
        if sum((abs(p.source_share) for p in selected), Decimal(0)) > abs(capacity):
            raise ValueError("Assigned shares exceed the received bucket.")

    for part in parts:
        if part.amount_bucket != "nonrecoverable_tax":
            continue
        effects = {
            p.cost_effect
            for p in parts
            if p.movement_id == part.movement_id and p.amount_bucket == "selected_basis"
        }
        if effects and effects != {part.cost_effect}:
            raise ValueError(
                "Tax cost direction must follow the selected amount for the same receipt."
            )


class Change(Request):
    expected_event_sequence: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=4000)


class Assign(Change):
    operation: Literal["assign"]
    document_id: str = Field(min_length=1)
    document_line_id: str | None = None
    expected_evidence_hash: str = Field(min_length=64, max_length=64)
    basis: Literal["net", "gross", "base"]
    selected_basis_tax_inclusion: Literal["included", "excluded", "unknown"]
    tax_treatment: Literal[
        "recoverable", "nonrecoverable", "mixed", "not_applicable", "unknown"
    ]
    nonrecoverable_tax_amount: Amount = Decimal(0)
    parts: list[CostPart] = Field(min_length=1, max_length=100)


class AllocationRequestTarget(Request):
    movement_id: str = Field(min_length=1)
    weight: Decimal | None = None


class Allocate(Change):
    operation: Literal["allocate"]
    document_id: str = Field(min_length=1)
    document_line_id: str | None = None
    expected_evidence_hash: str = Field(min_length=64, max_length=64)
    basis: Literal["net", "gross", "base"]
    selected_basis_tax_inclusion: Literal["included", "excluded", "unknown"]
    tax_treatment: Literal[
        "recoverable", "nonrecoverable", "mixed", "not_applicable", "unknown"
    ]
    nonrecoverable_tax_amount: Amount = Decimal(0)
    allocation_total: Amount
    category: Category
    cost_effect: Literal[-1, 1]
    amount_bucket: Literal["selected_basis", "nonrecoverable_tax"]
    driver_kind: Literal["quantity", "equal", "manual"]
    conversion_basis_revision_id: str | None = None
    targets: list[AllocationRequestTarget] = Field(min_length=2, max_length=100)

    @model_validator(mode="after")
    def exact_driver(self):
        weights = [target.weight for target in self.targets]
        if self.driver_kind == "manual" and any(weight is None for weight in weights):
            raise ValueError("Every manual allocation target requires a weight.")
        if self.driver_kind != "manual" and any(weight is not None for weight in weights):
            raise ValueError("Only a manual allocation accepts caller-supplied weights.")
        if len({target.movement_id for target in self.targets}) != len(self.targets):
            raise ValueError("Duplicate allocation target.")
        CostPart(
            movement_id=self.targets[0].movement_id,
            category=self.category,
            source_share=self.allocation_total,
            cost_effect=self.cost_effect,
            amount_bucket=self.amount_bucket,
            assignment_kind="allocated",
        )
        return self


class CategoryReview(Request):
    category: Category
    disposition: Literal["evidenced", "confirmed_zero", "not_applicable", "unresolved"]
    reason: str = Field(min_length=1, max_length=4000)


class Review(Change):
    operation: Literal["review"]
    movement_id: str = Field(min_length=1)
    categories: list[CategoryReview] = Field(min_length=6, max_length=6)

    @field_validator("categories")
    @classmethod
    def every_category(cls, values):
        if {v.category for v in values} != set(CATEGORIES):
            raise ValueError("Review every required category exactly once.")
        return values


class Replace(Assign):
    operation: Literal["replace"]
    previous_component_basis_id: str = Field(min_length=1)


class Withdraw(Change):
    operation: Literal["withdraw"]
    component_basis_id: str = Field(min_length=1)


class InventoryReceipt(Request):
    movement_id: str = Field(min_length=1)
    manifest_id: str = Field(min_length=1)
    ownership_source_record_id: str = Field(min_length=1)


class InventoryOpening(Request):
    movement_id: str = Field(min_length=1)
    evidence_source_record_id: str = Field(min_length=1)
    acquisition_cost: Amount = Field(ge=0)


class InventorySpecificSelection(Request):
    movement_id: str = Field(min_length=1)
    entry_movement_id: str = Field(min_length=1)
    receipt_movement_id: str = Field(min_length=1)
    quantity: Amount = Field(gt=0)


class InventoryReturnPart(InventorySpecificSelection):
    issue_movement_id: str = Field(min_length=1)


class InventoryOwnershipPart(Request):
    movement_id: str = Field(min_length=1)
    owner_party_id: str = Field(min_length=1)
    evidence_source_record_id: str = Field(min_length=1)
    quantity: Amount = Field(gt=0)


class InventoryScope(Request):
    item_id: str = Field(min_length=1)
    owner_party_id: str = Field(min_length=1)
    method: Literal["fifo", "specific"]
    currency: str = Field(min_length=3, max_length=3)
    base_unit: str = Field(min_length=1)
    history_start: AwareDatetime
    effective_at: AwareDatetime
    history_complete_from_zero: Literal[True]
    receipt_cost_scopes_confirmed: Literal[True]
    economic_issue_ids: list[str] = Field(max_length=100)
    loss_movement_ids: list[str] = Field(default_factory=list, max_length=100)
    supplier_return_ids: list[str] = Field(default_factory=list, max_length=100)
    customer_return_ids: list[str] = Field(default_factory=list, max_length=100)
    receipts: list[InventoryReceipt] = Field(default_factory=list, max_length=20)
    openings: list[InventoryOpening] = Field(default_factory=list, max_length=20)
    specific_selections: list[InventorySpecificSelection] = Field(
        default_factory=list, max_length=200
    )
    return_parts: list[InventoryReturnPart] = Field(
        default_factory=list, max_length=200
    )
    ownership_parts: list[InventoryOwnershipPart] = Field(
        default_factory=list, max_length=500
    )

    @field_validator("history_start", "effective_at")
    @classmethod
    def utc_inventory_time(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def exact_scope(self):
        if self.history_start > self.effective_at:
            raise ValueError("History start exceeds the valuation cutoff.")
        if len(set(self.economic_issue_ids)) != len(self.economic_issue_ids):
            raise ValueError("Duplicate economic issue identity.")
        classified = [
            *self.economic_issue_ids,
            *self.loss_movement_ids,
            *self.supplier_return_ids,
            *self.customer_return_ids,
        ]
        if len(set(classified)) != len(classified):
            raise ValueError("Duplicate inventory movement classification.")
        if len({r.movement_id for r in self.receipts}) != len(self.receipts):
            raise ValueError("Duplicate receipt identity.")
        if len({row.movement_id for row in self.openings}) != len(self.openings):
            raise ValueError("Duplicate opening identity.")
        if {r.movement_id for r in self.receipts} & {
            row.movement_id for row in self.openings
        }:
            raise ValueError("Opening and receipt identities must be disjoint.")
        ownership_keys = [
            (part.movement_id, part.owner_party_id) for part in self.ownership_parts
        ]
        if len(set(ownership_keys)) != len(ownership_keys):
            raise ValueError("Duplicate movement owner portion.")
        selected = [
            (s.movement_id, s.entry_movement_id, s.receipt_movement_id)
            for s in self.specific_selections
        ]
        if len(set(selected)) != len(selected):
            raise ValueError("Duplicate specific inventory selection.")
        selected_movements = {s.movement_id for s in self.specific_selections}
        required = set(self.supplier_return_ids)
        if self.method == "specific":
            required |= set(self.economic_issue_ids) | set(self.loss_movement_ids)
        if selected_movements != required:
            raise ValueError(
                "Exact selections must cover every required outbound movement."
            )
        returned = [
            (
                p.movement_id,
                p.issue_movement_id,
                p.entry_movement_id,
                p.receipt_movement_id,
            )
            for p in self.return_parts
        ]
        if len(set(returned)) != len(returned):
            raise ValueError("Duplicate customer-return portion.")
        if {p.movement_id for p in self.return_parts} != set(self.customer_return_ids):
            raise ValueError("Customer returns require exact original issue portions.")
        return self


class InventoryReview(InventoryScope, Change):
    operation: Literal["inventory_review"]


class InventoryBatchReview(Change):
    operation: Literal["inventory_batch_review"]
    scopes: list[InventoryScope] = Field(min_length=2, max_length=10)

    @model_validator(mode="after")
    def compatible_scopes(self):
        if sum(len(scope.receipts) + len(scope.openings) for scope in self.scopes) > 20:
            raise ValueError("Joint inventory receipt bound exceeded.")
        if len({scope.item_id for scope in self.scopes}) != len(self.scopes):
            raise ValueError("Duplicate inventory item scope.")
        for field in ("effective_at", "owner_party_id", "currency"):
            if len({getattr(scope, field) for scope in self.scopes}) != 1:
                raise ValueError(f"Joint inventory scopes require the same {field}.")
        return self


class InventoryRead(Request):
    item_id: str = Field(min_length=1)
    review_id: str | None = None
    assessment_revision_id: str | None = None


class ValuationAssessmentPart(Request):
    inventory_member_id: str = Field(min_length=1)
    evidence_source_record_id: str = Field(min_length=1)
    quantity: Amount = Field(gt=0)
    assessed_value: Amount = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)


class ValuationAssessment(Change):
    operation: Literal["valuation_assessment"]
    inventory_review_id: str = Field(min_length=1)
    kind: Literal["write_down", "recovery"]
    supersedes_id: str | None = None
    effective_at: AwareDatetime
    parts: list[ValuationAssessmentPart] = Field(min_length=1, max_length=100)

    @field_validator("effective_at")
    @classmethod
    def utc_effective_time(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def exact_revision(self):
        if self.kind == "recovery" and not self.supersedes_id:
            raise ValueError("A recovery requires an exact predecessor assessment.")
        if self.kind == "write_down" and self.supersedes_id:
            raise ValueError("A write-down cannot supersede an assessment.")
        identities = [part.inventory_member_id for part in self.parts]
        if len(set(identities)) != len(identities):
            raise ValueError("Duplicate assessment member.")
        if len({part.currency for part in self.parts}) != 1:
            raise ValueError("Assessment parts require one currency.")
        return self


SELLING_CATEGORIES = (
    "outbound_freight",
    "fulfilment",
    "packaging",
    "payment_fee",
    "marketplace_commission",
    "sales_commission",
    "other_selling",
)
SellingCategory = Literal[
    "outbound_freight",
    "fulfilment",
    "packaging",
    "payment_fee",
    "marketplace_commission",
    "sales_commission",
    "other_selling",
]


class SellingPart(Request):
    document_line_id: str = Field(min_length=1)
    category: SellingCategory
    source_share: Amount
    cost_effect: Literal[-1, 1]
    assignment_kind: Literal["direct", "allocated"] = "direct"
    conversion_basis_revision_id: str | None = None

    @field_validator("source_share")
    @classmethod
    def nonzero(cls, value):
        if value == 0:
            raise ValueError("Zero requires a scope review.")
        return value


class SellingAssign(Change):
    operation: Literal["selling_assign"]
    document_id: str = Field(min_length=1)
    document_line_id: str | None = None
    expected_evidence_hash: str = Field(min_length=64, max_length=64)
    tax_treatment: Literal["recoverable", "not_applicable"]
    selling_expense_confirmed: Literal[True]
    parts: list[SellingPart] = Field(min_length=1, max_length=100)

    @field_validator("parts")
    @classmethod
    def unique_parts(cls, values):
        if len({(p.document_line_id, p.category) for p in values}) != len(values):
            raise ValueError("Duplicate selling target/category.")
        return values


class SellingAllocationTarget(Request):
    document_line_id: str = Field(min_length=1)
    category: SellingCategory
    weight: Decimal | None = None


class SellingAllocate(Change):
    operation: Literal["selling_allocate"]
    document_id: str = Field(min_length=1)
    document_line_id: str | None = None
    expected_evidence_hash: str = Field(min_length=64, max_length=64)
    tax_treatment: Literal["recoverable", "not_applicable"]
    selling_expense_confirmed: Literal[True]
    allocation_total: Amount
    driver_kind: Literal["equal", "manual"]
    conversion_basis_revision_id: str | None = None
    targets: list[SellingAllocationTarget] = Field(min_length=2, max_length=100)

    @model_validator(mode="after")
    def exact_driver(self):
        weights = [target.weight for target in self.targets]
        if self.driver_kind == "manual" and any(weight is None for weight in weights):
            raise ValueError("Every manual allocation target requires a weight.")
        if self.driver_kind == "equal" and any(weight is not None for weight in weights):
            raise ValueError("Equal allocation does not accept caller-supplied weights.")
        identities = [
            (target.document_line_id, target.category) for target in self.targets
        ]
        if len(set(identities)) != len(identities):
            raise ValueError("Duplicate selling allocation target/category.")
        return self


class ConversionBasisReview(Change):
    operation: Literal["conversion_basis"]
    evidence_source_record_id: str = Field(min_length=1)
    kind: Literal["unit", "currency"]
    from_code: str = Field(min_length=1, max_length=100)
    to_code: str = Field(min_length=1, max_length=100)
    numerator: Decimal
    denominator: Decimal
    effective_at: AwareDatetime
    supersedes_id: str | None = None

    @model_validator(mode="after")
    def exact_ratio(self):
        if self.from_code == self.to_code:
            raise ValueError("Identity conversion requires no retained authority.")
        for value in (self.numerator, self.denominator):
            if not value.is_finite() or value <= 0:
                raise ValueError("Conversion ratio values must be positive.")
            if max(0, -value.as_tuple().exponent) > 12:
                raise ValueError("Conversion ratios support at most twelve decimal places.")
            if len(value.as_tuple().digits) > 28:
                raise ValueError("Conversion ratios support at most 28 digits.")
        return self


class SellingCategoryReview(Request):
    category: SellingCategory
    disposition: Literal["evidenced", "confirmed_zero", "not_applicable", "unresolved"]
    reason: str = Field(min_length=1, max_length=4000)


class ContributionScope(Request):
    document_line_id: str = Field(min_length=1)
    expected_candidate_hash: str = Field(min_length=64, max_length=64)
    profile: Literal["commercial_v1"]
    profile_confirmed: Literal[True]
    revenue_complete: Literal[True]
    economic_at: AwareDatetime
    selling_categories: list[SellingCategoryReview] | None = None

    @field_validator("selling_categories")
    @classmethod
    def every_selling_category(cls, values):
        if values is not None and (
            len(values) != len(SELLING_CATEGORIES)
            or {v.category for v in values} != set(SELLING_CATEGORIES)
        ):
            raise ValueError("Review every selling category exactly once.")
        return values

    @field_validator("economic_at")
    @classmethod
    def utc_economic_time(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


class ContributionReview(ContributionScope, Change):
    operation: Literal["contribution_review"]


class ContributionBatchReview(Change):
    operation: Literal["contribution_batch_review"]
    positions: list[ContributionScope] = Field(min_length=2, max_length=10)

    @field_validator("positions")
    @classmethod
    def unique_positions(cls, positions):
        if len({position.document_line_id for position in positions}) != len(positions):
            raise ValueError("Duplicate contribution position.")
        return positions


class CommercialInventoryMatchPart(Request):
    inventory_member_id: str = Field(min_length=1)
    entry_movement_basis_id: str = Field(min_length=1)
    receipt_movement_basis_id: str = Field(min_length=1)
    original_issue_member_id: str | None = None
    quantity: Amount = Field(gt=0)


class CommercialDirectMatchPart(Request):
    attribution_revision_id: str = Field(min_length=1)
    input_role: Literal[
        "service_input", "shipping_input", "kit_input", "production_input"
    ]


class CommercialMatchReview(Change):
    operation: Literal["commercial_match_review"]
    document_line_id: str = Field(min_length=1)
    expected_evidence_hash: str = Field(min_length=64, max_length=64)
    profile: Literal["commercial_v1"]
    profile_confirmed: Literal[True]
    goods_cost_disposition: Literal[
        "inventory", "direct_evidence", "not_applicable", "unresolved"
    ]
    inventory_parts: list[CommercialInventoryMatchPart] = Field(
        default_factory=list, max_length=500
    )
    direct_parts: list[CommercialDirectMatchPart] = Field(
        default_factory=list, max_length=500
    )
    direct_cost_complete: bool = False


CHANGE = TypeAdapter(
    Annotated[
        Assign
        | Allocate
        | Review
        | Replace
        | Withdraw
        | InventoryReview
        | InventoryBatchReview
        | ContributionReview
        | ContributionBatchReview
        | CommercialMatchReview
        | SellingAssign
        | SellingAllocate
        | ConversionBasisReview
        | ValuationAssessment,
        Field(discriminator="operation"),
    ]
)


class ReceiptRead(Request):
    movement_id: str = Field(min_length=1)
    manifest_id: str | None = None


class EvidenceRead(Request):
    document_id: str = Field(min_length=1)
    document_line_id: str | None = None


class ContributionRead(Request):
    document_line_id: str = Field(min_length=1)


class ReviewedContributionRead(Request):
    document_line_id: str = Field(min_length=1)
    review_id: str | None = None


class CommercialMatchRead(Request):
    document_line_id: str = Field(min_length=1)
    match_revision_id: str | None = None
