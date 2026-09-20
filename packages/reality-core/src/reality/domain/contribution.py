"""Read-only commercial_v1 arithmetic; services must admit matching and evidence first."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from itertools import islice
from types import MappingProxyType
from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from reality.domain.costing import Amount
from reality.domain.inventory_costing import Identity

ALGORITHM_VERSION = "commercial-v1"
MAX_SLICES = 10_000
MAX_COMMERCIAL_MATCH_LINES = 100
MAX_COMMERCIAL_MATCH_PARTS = 500
ZERO = Decimal(0)
MONEY_STEP = Decimal("0.0001")
# The first input contributes revenue/value; subsequent inputs are deductions.
CONTRIBUTION_TERMS = MappingProxyType(
    {
        "revenue": ("revenue",),
        "goods_cost": ("goods_cost",),
        "direct_selling_cost": ("direct_selling_cost",),
        "allocated_selling_cost": ("allocated_selling_cost",),
        "db1": ("revenue", "goods_cost"),
        "db2": (
            "revenue",
            "goods_cost",
            "direct_selling_cost",
            "allocated_selling_cost",
        ),
    }
)
GROUPINGS = frozenset(
    {"position_id", "order_id", "item_id", "customer_id", "channel_id", "month"}
)


class ContributionRefusal(ValueError):
    """Refuse the scope without returning a partial result."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class ContributionContext(_Input):
    tenant_id: Identity
    generation_id: Identity | None
    policy_revision_id: Identity
    profile_revision_id: Identity | None
    mode: Literal["reviewed", "preview"] = "reviewed"
    profile: Literal["commercial_v1"]
    effective_at: AwareDatetime
    knowledge_at: AwareDatetime

    @model_validator(mode="after")
    def authority_shape(self):
        if self.mode == "reviewed" and (
            not self.generation_id or not self.profile_revision_id
        ):
            raise ValueError(
                "Reviewed context requires generation and profile revision."
            )
        if self.mode == "preview" and (
            self.generation_id is not None or self.profile_revision_id is not None
        ):
            raise ValueError("Preview has no admitted generation or profile revision.")
        return self

    @field_validator("effective_at", "knowledge_at")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


class ContributionInput(_Input):
    amount: Amount | None
    state: Literal["reviewed", "evidenced", "provisional", "unknown"]
    references: tuple[Identity, ...] = Field(default=(), max_length=100)

    @model_validator(mode="after")
    def shape(self):
        if (self.amount is None) != (self.state == "unknown"):
            raise ValueError("Unknown is absent; other states require an amount.")
        if self.state != "unknown" and not self.references:
            raise ValueError("Known and provisional inputs require basis references.")
        if len(set(self.references)) != len(self.references):
            raise ValueError("Duplicate basis reference.")
        return self


class MatchedSlice(_Input):
    slice_id: Identity
    context: ContributionContext
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    base_unit: Identity
    quantity: Amount
    economic_date: date
    position_id: Identity | None = None
    order_id: Identity | None = None
    item_id: Identity | None = None
    customer_id: Identity | None = None
    channel_id: Identity | None = None
    revenue: ContributionInput
    goods_cost: ContributionInput
    direct_selling_cost: ContributionInput
    allocated_selling_cost: ContributionInput


class CommercialInventoryPart(_Input):
    member_id: Identity
    entry_basis_id: Identity
    receipt_basis_id: Identity
    original_issue_member_id: Identity | None = None
    quantity: Amount = Field(gt=0)

    @property
    def key(self) -> tuple[str, str, str, str | None]:
        return (
            self.member_id,
            self.entry_basis_id,
            self.receipt_basis_id,
            self.original_issue_member_id,
        )


class CommercialMatchLine(_Input):
    line_id: Identity
    flow: Literal["sale", "credit"]
    stated_net: Amount
    stated_quantity: Amount | None
    disposition: Literal[
        "inventory", "direct_evidence", "not_applicable", "unresolved"
    ]
    inventory_parts: tuple[CommercialInventoryPart, ...] = Field(
        default=(), max_length=MAX_COMMERCIAL_MATCH_PARTS
    )
    direct_revision_ids: tuple[Identity, ...] = Field(
        default=(), max_length=MAX_COMMERCIAL_MATCH_PARTS
    )
    direct_cost_complete: bool = False

    @model_validator(mode="after")
    def exact_match_shape(self):
        if self.flow == "sale" and (
            self.stated_net < 0
            or (self.stated_quantity is not None and self.stated_quantity <= 0)
        ):
            raise ValueError("Sale amount and quantity sign mismatch.")
        if self.flow == "credit" and (
            self.stated_net > 0
            or self.stated_quantity is None
            or self.stated_quantity >= 0
        ):
            raise ValueError("Credit amount and quantity sign mismatch.")
        if len({part.key for part in self.inventory_parts}) != len(
            self.inventory_parts
        ):
            raise ValueError("Duplicate commercial inventory portion.")
        if len(set(self.direct_revision_ids)) != len(self.direct_revision_ids):
            raise ValueError("Duplicate commercial direct evidence.")
        if self.disposition == "inventory":
            if (
                self.stated_quantity is None
                or not self.inventory_parts
                or self.direct_revision_ids
                or self.direct_cost_complete
                or sum((part.quantity for part in self.inventory_parts), ZERO)
                != abs(self.stated_quantity)
            ):
                raise ValueError(
                    "Commercial inventory portions must conserve stated quantity."
                )
            if self.flow == "credit" and any(
                part.original_issue_member_id is None
                for part in self.inventory_parts
            ):
                raise ValueError("Credit return portions require an original issue.")
            if self.flow == "sale" and any(
                part.original_issue_member_id is not None
                for part in self.inventory_parts
            ):
                raise ValueError("Sale portions cannot name an original issue.")
        elif self.disposition == "direct_evidence":
            if (
                self.inventory_parts
                or not self.direct_revision_ids
                or not self.direct_cost_complete
            ):
                raise ValueError("Direct evidence must be explicitly complete.")
        elif (
            self.inventory_parts
            or self.direct_revision_ids
            or self.direct_cost_complete
        ):
            raise ValueError("Disposition does not accept cost evidence portions.")
        return self


@dataclass(frozen=True, slots=True)
class CommercialRevenuePart:
    inventory_key: tuple[str, str, str, str | None]
    quantity: Decimal
    amount: Decimal


@dataclass(frozen=True, slots=True)
class CommercialMatchObservation:
    line_id: str
    stated_net: Decimal
    stated_quantity: Decimal | None
    disposition: str
    complete: bool
    revenue_parts: tuple[CommercialRevenuePart, ...]


def admit_commercial_matches(
    lines: Iterable[CommercialMatchLine],
    capacities: dict[tuple[str, str, str, str | None], Decimal],
) -> tuple[CommercialMatchObservation, ...]:
    """Validate explicit match conservation and derive no new authority.

    Revenue portions are deterministic read-time observations of one source-stated line
    total. Callers retain the line total and exact inventory portions, never these amounts.
    """
    admitted = tuple(islice(lines, MAX_COMMERCIAL_MATCH_LINES + 1))
    if len(admitted) > MAX_COMMERCIAL_MATCH_LINES:
        raise ContributionRefusal("commercial_match_line_bound")
    if len({line.line_id for line in admitted}) != len(admitted):
        raise ContributionRefusal("duplicate_commercial_match_line")
    if sum((len(line.inventory_parts) for line in admitted), 0) > MAX_COMMERCIAL_MATCH_PARTS:
        raise ContributionRefusal("commercial_match_part_bound")
    used: dict[tuple[str, str, str, str | None], Decimal] = defaultdict(Decimal)
    for line in admitted:
        for part in line.inventory_parts:
            if part.key not in capacities:
                raise ContributionRefusal("match_capacity_missing")
            capacity = capacities[part.key]
            if capacity <= 0:
                raise ContributionRefusal("match_capacity_invalid")
            used[part.key] += part.quantity
            if used[part.key] > capacity:
                raise ContributionRefusal("match_capacity_exceeded")
    observations = []
    with localcontext() as decimal_context:
        decimal_context.prec = 80
        for line in sorted(admitted, key=lambda row: row.line_id):
            revenue_parts = []
            cumulative_quantity = cumulative_amount = ZERO
            parts = sorted(line.inventory_parts, key=lambda part: part.key)
            total_quantity = sum((part.quantity for part in parts), ZERO)
            for part in parts:
                cumulative_quantity += part.quantity
                target = (
                    line.stated_net * cumulative_quantity / total_quantity
                ).quantize(MONEY_STEP, rounding=ROUND_HALF_EVEN)
                revenue_parts.append(
                    CommercialRevenuePart(
                        part.key, part.quantity, target - cumulative_amount
                    )
                )
                cumulative_amount = target
            observations.append(
                CommercialMatchObservation(
                    line_id=line.line_id,
                    stated_net=line.stated_net,
                    stated_quantity=line.stated_quantity,
                    disposition=line.disposition,
                    complete=line.disposition != "unresolved",
                    revenue_parts=tuple(revenue_parts),
                )
            )
    return tuple(observations)


@dataclass(frozen=True, slots=True)
class CoveredAmount:
    known: Decimal
    total: Decimal | None
    required: int
    covered: int
    evidenced: int
    provisional: int


@dataclass(frozen=True, slots=True)
class ContributionGroup:
    currency: str
    base_unit: str
    dimensions: tuple[tuple[str, str | None], ...]
    quantity: Decimal
    revenue: CoveredAmount
    goods_cost: CoveredAmount
    direct_selling_cost: CoveredAmount
    allocated_selling_cost: CoveredAmount
    db1: CoveredAmount
    db2: CoveredAmount
    db1_rate: Decimal | None
    db2_rate: Decimal | None
    slices: tuple[MatchedSlice, ...]


@dataclass(frozen=True, slots=True)
class ContributionResult:
    context: ContributionContext
    state: Literal["no_activity", "complete", "partial"]
    groups: tuple[ContributionGroup, ...]


def _covered(
    rows: tuple[MatchedSlice, ...], fields: tuple[str, ...], *, final: bool
) -> CoveredAmount:
    known = ZERO
    covered = evidenced = provisional = 0
    for row in rows:
        inputs = [getattr(row, name) for name in fields]
        actual = all(i.state in ("reviewed", "evidenced") for i in inputs)
        covered += int(all(i.state == "reviewed" for i in inputs))
        evidenced += int(actual)
        provisional += int(any(i.state == "provisional" for i in inputs))
        if actual:
            # The first term is positive; subsequent terms are deductions.
            known += inputs[0].amount - sum((i.amount for i in inputs[1:]), ZERO)
    return CoveredAmount(
        known,
        known if final and covered == len(rows) else None,
        len(rows),
        covered,
        evidenced,
        provisional,
    )


def _rate(margin: CoveredAmount, revenue: CoveredAmount) -> Decimal | None:
    if margin.total is None or revenue.total is None or revenue.total <= 0:
        return None
    return (100 * margin.total / revenue.total).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_EVEN
    )


def aggregate_contribution(
    slices: Iterable[MatchedSlice],
    *,
    context: ContributionContext,
    group_by: tuple[str, ...] = (),
) -> ContributionResult:
    """Aggregate compatible slices and independent actual/reviewed coverage."""
    if (
        len(group_by) > len(GROUPINGS)
        or len(set(group_by)) != len(group_by)
        or set(group_by) - GROUPINGS
    ):
        raise ContributionRefusal("unsupported_grouping")
    rows = tuple(islice(slices, MAX_SLICES + 1))
    if len(rows) > MAX_SLICES:
        raise ContributionRefusal("slice_bound")
    seen = set()
    grouped = defaultdict(list)
    for row in rows:
        if row.context != context:
            raise ContributionRefusal("context_mismatch")
        if row.economic_date > context.effective_at.date():
            raise ContributionRefusal("economic_date_after_cutoff")
        if row.slice_id in seen:
            raise ContributionRefusal("duplicate_slice")
        seen.add(row.slice_id)
        dimensions = tuple(
            (
                name,
                row.economic_date.strftime("%Y-%m")
                if name == "month"
                else getattr(row, name),
            )
            for name in group_by
        )
        grouped[(row.currency, row.base_unit, dimensions)].append(row)
    results = []
    with localcontext() as decimal_context:
        decimal_context.prec = 80
        for (currency, unit, dimensions), members in sorted(
            grouped.items(), key=lambda pair: repr(pair[0])
        ):
            scope = tuple(sorted(members, key=lambda row: row.slice_id))
            revenue = _covered(
                scope, CONTRIBUTION_TERMS["revenue"], final=context.mode == "reviewed"
            )
            goods = _covered(
                scope,
                CONTRIBUTION_TERMS["goods_cost"],
                final=context.mode == "reviewed",
            )
            direct = _covered(
                scope,
                CONTRIBUTION_TERMS["direct_selling_cost"],
                final=context.mode == "reviewed",
            )
            allocated = _covered(
                scope,
                CONTRIBUTION_TERMS["allocated_selling_cost"],
                final=context.mode == "reviewed",
            )
            db1 = _covered(
                scope, CONTRIBUTION_TERMS["db1"], final=context.mode == "reviewed"
            )
            db2 = _covered(
                scope,
                CONTRIBUTION_TERMS["db2"],
                final=context.mode == "reviewed",
            )
            results.append(
                ContributionGroup(
                    currency,
                    unit,
                    dimensions,
                    sum((row.quantity for row in scope), ZERO),
                    revenue,
                    goods,
                    direct,
                    allocated,
                    db1,
                    db2,
                    _rate(db1, revenue),
                    _rate(db2, revenue),
                    scope,
                )
            )
    state = (
        "no_activity"
        if not rows
        else "complete"
        if all(g.db2.total is not None for g in results)
        else "partial"
    )
    return ContributionResult(context, state, tuple(results))
