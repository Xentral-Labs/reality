"""Derived acquisition-cost layers for one admitted, frozen economic-owner pool.

This pure boundary does not establish ownership, policy approval, source knowledge,
movement corrections or carrying value. Shared services must establish those inputs
before invoking it; application reads must not replay unbounded company history.
"""

from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from itertools import islice
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from reality.domain.costing import Amount

ALGORITHM_VERSION = "inventory-v1"
MAX_EVENTS = 10_000
MAX_PORTIONS = 20_000
ZERO = Decimal(0)
STEP = Decimal("0.0001")
Quantity = Annotated[Amount, Field(gt=0)]
Identity = Annotated[str, Field(min_length=1, max_length=200)]
Kind = Literal[
    "receipt", "issue", "loss", "supplier_return", "customer_return", "transfer"
]
Method = Literal["fifo", "specific"]


class InventoryRefusal(ValueError):
    """Stable refusal reason; no partial result has been published."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class Selection(_Input):
    entry_movement_id: Identity
    receipt_movement_id: Identity
    quantity: Quantity

    @property
    def key(self) -> tuple[str, str]:
        return self.entry_movement_id, self.receipt_movement_id


class ReturnPart(Selection):
    issue_movement_id: Identity


class InventoryEvent(_Input):
    movement_id: Identity
    kind: Kind
    quantity: Quantity
    occurred_at: AwareDatetime
    sequence: int = Field(ge=0, strict=True)
    acquisition_cost: Annotated[Amount, Field(ge=0)] | None = None
    selections: tuple[Selection, ...] = Field(default=(), max_length=MAX_PORTIONS)
    return_parts: tuple[ReturnPart, ...] = Field(default=(), max_length=MAX_PORTIONS)

    @field_validator("occurred_at")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def valid_shape(self):
        if self.kind != "receipt" and self.acquisition_cost is not None:
            raise ValueError("Only a receipt supplies an acquisition amount.")
        if self.selections and self.kind not in ("issue", "loss", "supplier_return"):
            raise ValueError("Selections require an outbound movement.")
        if bool(self.return_parts) != (self.kind == "customer_return"):
            raise ValueError("Customer returns require exact original issue portions.")
        for parts in (self.selections, self.return_parts):
            with localcontext() as context:
                context.prec = 80
                if parts and sum((p.quantity for p in parts), ZERO) != self.quantity:
                    raise ValueError("Portions must cover the exact movement quantity.")
            keys = [(getattr(p, "issue_movement_id", None), p.key) for p in parts]
            if len(set(keys)) != len(keys):
                raise ValueError("Duplicate portion reference.")
        return self


@dataclass(frozen=True, slots=True)
class CostPortion:
    entry_movement_id: str
    receipt_movement_id: str
    quantity: Decimal
    cost: Decimal | None
    issue_movement_id: str | None = None


@dataclass(frozen=True, slots=True)
class Consumption:
    movement_id: str
    kind: Kind
    quantity: Decimal
    cost: Decimal | None
    known_cost: Decimal
    unvalued_quantity: Decimal
    parts: tuple[CostPortion, ...]


@dataclass(frozen=True, slots=True)
class InventoryResult:
    issues: tuple[Consumption, ...]
    returns: tuple[Consumption, ...]
    remaining: tuple[CostPortion, ...]
    remaining_quantity: Decimal
    remaining_cost: Decimal | None
    known_remaining_cost: Decimal
    unvalued_quantity: Decimal


@dataclass(slots=True)
class _Layer:
    quantity: Decimal
    cost: Decimal | None
    used: Decimal = ZERO
    charged: Decimal = ZERO

    @property
    def left(self) -> Decimal:
        return self.quantity - self.used

    def take(self, quantity: Decimal) -> Decimal | None:
        if quantity <= 0 or quantity > self.left:
            raise InventoryRefusal("portion_exceeded")
        self.used += quantity
        if self.cost is None:
            return None
        cumulative = (self.cost * self.used / self.quantity).quantize(
            STEP, rounding=ROUND_HALF_EVEN
        )
        amount = cumulative - self.charged
        self.charged = cumulative
        return amount


@dataclass(slots=True)
class _Budget:
    portions: int = 0

    def add(self, count: int = 1) -> None:
        self.portions += count
        if self.portions > MAX_PORTIONS:
            raise InventoryRefusal("portion_limit")


def _observation(event: InventoryEvent, parts: list[CostPortion]) -> Consumption:
    unknown = sum((abs(p.quantity) for p in parts if p.cost is None), ZERO)
    known = sum((p.cost for p in parts if p.cost is not None), ZERO)
    return Consumption(
        event.movement_id,
        event.kind,
        -event.quantity if event.kind == "customer_return" else event.quantity,
        None if unknown else known,
        known,
        unknown,
        tuple(parts),
    )


def calculate_inventory(
    events: Iterable[InventoryEvent], *, method: Method
) -> InventoryResult:
    """Replay a bounded frozen pool; method is explicit and never a policy default.

    Unknown receipt amounts propagate as coverage gaps. Negative stock, unsupported
    references and resource bounds refuse the whole result rather than invent costs.
    All reported rounding happens before a caller selects an observation/filter.
    """
    if method not in ("fifo", "specific"):
        raise InventoryRefusal("unsupported_method")
    admitted = list(islice(events, MAX_EVENTS + 1))
    if len(admitted) > MAX_EVENTS:
        raise InventoryRefusal("event_limit")
    if any(not isinstance(e, InventoryEvent) for e in admitted):
        raise InventoryRefusal("typed_event_required")
    if len({e.movement_id for e in admitted}) != len(admitted):
        raise InventoryRefusal("duplicate_movement")
    budget = _Budget()
    budget.add(sum(len(e.selections) + len(e.return_parts) for e in admitted))
    admitted.sort(key=lambda e: (e.occurred_at, e.sequence, e.movement_id))
    with localcontext() as context:
        context.prec = 80
        return _replay(admitted, method, budget)


def _replay(
    events: list[InventoryEvent], method: Method, budget: _Budget
) -> InventoryResult:
    layers: OrderedDict[tuple[str, str], _Layer] = OrderedDict()
    issues: dict[str, Consumption] = {}
    # Exact original sales portions are consumed independently by return allocations.
    returnable: dict[tuple[str, str, str], _Layer] = {}
    returns: list[Consumption] = []
    stock = ZERO
    for event in events:
        if event.kind == "receipt":
            budget.add()
            layers[(event.movement_id, event.movement_id)] = _Layer(
                event.quantity, event.acquisition_cost
            )
            stock += event.quantity
        elif event.kind == "customer_return":
            parts = []
            restored: dict[str, _Layer] = {}
            for part in event.return_parts:
                budget.add()
                original = issues.get(part.issue_movement_id)
                if original is None or original.kind != "issue":
                    raise InventoryRefusal("original_sale_required")
                cursor = returnable.get((part.issue_movement_id, *part.key))
                if cursor is None:
                    raise InventoryRefusal("original_portion_required")
                amount = cursor.take(part.quantity)
                parts.append(
                    CostPortion(
                        *part.key,
                        -part.quantity,
                        None if amount is None else -amount,
                        part.issue_movement_id,
                    )
                )
                combined = restored.get(part.receipt_movement_id)
                if combined is None:
                    restored[part.receipt_movement_id] = _Layer(part.quantity, amount)
                else:
                    combined.quantity += part.quantity
                    combined.cost = (
                        None
                        if combined.cost is None or amount is None
                        else combined.cost + amount
                    )
            # One return may contain several original receipts. Opaque receipt identity
            # supplies a deterministic tie-break within this simultaneous layer entry.
            for receipt_id in sorted(restored):
                budget.add()
                layers[(event.movement_id, receipt_id)] = restored[receipt_id]
            returns.append(_observation(event, parts))
            stock += event.quantity
        elif event.kind == "transfer":
            if event.quantity > stock:
                raise InventoryRefusal("insufficient_stock")
        else:
            exact = method == "specific" or event.kind == "supplier_return"
            if exact and not event.selections:
                raise InventoryRefusal("specific_selection_required")
            if not exact and event.selections:
                raise InventoryRefusal("fifo_selection_forbidden")
            if event.quantity > stock:
                raise InventoryRefusal("insufficient_stock")
            parts = []
            if exact:
                selections = sorted(event.selections, key=lambda p: p.key)
                for selection in selections:
                    layer = layers.get(selection.key)
                    if layer is None:
                        raise InventoryRefusal("specific_layer_unavailable")
                    budget.add()
                    amount = layer.take(selection.quantity)
                    parts.append(
                        CostPortion(*selection.key, selection.quantity, amount)
                    )
                    if not layer.left:
                        del layers[selection.key]
            else:
                left = event.quantity
                while left:
                    key, layer = next(iter(layers.items()))
                    quantity = min(left, layer.left)
                    budget.add()
                    parts.append(CostPortion(*key, quantity, layer.take(quantity)))
                    left -= quantity
                    if not layer.left:
                        del layers[key]
            issues[event.movement_id] = _observation(event, parts)
            if event.kind == "issue":
                for part in parts:
                    returnable[
                        (
                            event.movement_id,
                            part.entry_movement_id,
                            part.receipt_movement_id,
                        )
                    ] = _Layer(part.quantity, part.cost)
            stock -= event.quantity
    remaining = tuple(
        CostPortion(
            *key, layer.left, None if layer.cost is None else layer.cost - layer.charged
        )
        for key, layer in layers.items()
    )
    budget.add(len(remaining))
    unknown = sum((p.quantity for p in remaining if p.cost is None), ZERO)
    known = sum((p.cost for p in remaining if p.cost is not None), ZERO)
    return InventoryResult(
        tuple(issues.values()),
        tuple(returns),
        remaining,
        stock,
        None if unknown else known,
        known,
        unknown,
    )
