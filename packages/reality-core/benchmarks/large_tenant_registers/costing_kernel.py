"""Pure costing observations for qualification only; never product authority."""

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_FLOOR, ROUND_HALF_EVEN, Decimal, localcontext

STEP = Decimal("0.0001")
ZERO = Decimal(0)


def money(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 80
        return value.quantize(STEP, rounding=ROUND_HALF_EVEN)


def _proportion(amount: Decimal, numerator: Decimal, denominator: Decimal) -> Decimal:
    # Numeric(18,4) operands can require more than the process-default 28 digits
    # to decide which side of a four-decimal half-even tie the exact ratio lies.
    with localcontext() as context:
        context.prec = 80
        return amount * numerator / denominator


def acquisition_cost(
    net: Decimal | None,
    adjustments: list[Decimal],
    tax: Decimal | None,
    recoverable: bool | None,
) -> Decimal | None:
    """Compose stated amounts; never infer a missing tax/net amount from a rate."""
    if net is None or recoverable is None or (not recoverable and tax is None):
        return None
    return net + sum(adjustments, ZERO) + (ZERO if recoverable else tax)


def allocate(amount: Decimal, weights: dict[str, Decimal]) -> dict[str, Decimal]:
    if not weights or any(w <= 0 for w in weights.values()) or money(amount) != amount:
        raise ValueError("Positive weights and four-decimal amount required.")
    total = sum(weights.values(), ZERO)
    units = abs(amount) / STEP
    exact = {k: _proportion(units, w, total) for k, w in weights.items()}
    whole = {k: v.to_integral_value(rounding=ROUND_FLOOR) for k, v in exact.items()}
    remainder = int(units - sum(whole.values(), ZERO))
    order = sorted(weights, key=lambda k: (-(exact[k] - whole[k]), k))
    for key in order[:remainder]:
        whole[key] += 1
    sign = -1 if amount < 0 else 1
    return {k: whole[k] * STEP * sign for k in sorted(weights)}


@dataclass(frozen=True, slots=True)
class Event:
    identity: str
    kind: str
    quantity: Decimal
    cost: Decimal | None = None
    original_issue: str | None = None
    specific_layer: str | None = None


@dataclass(slots=True)
class Layer:
    identity: str
    quantity: Decimal
    cost: Decimal | None
    used: Decimal = ZERO
    charged: Decimal = ZERO

    def take(self, quantity: Decimal) -> Decimal | None:
        if quantity <= 0 or self.used + quantity > self.quantity:
            raise ValueError("Invalid layer consumption.")
        self.used += quantity
        if self.cost is None:
            return None
        cumulative = money(_proportion(self.cost, self.used, self.quantity))
        delta = cumulative - self.charged
        self.charged = cumulative
        return delta


@dataclass(frozen=True, slots=True)
class Issue:
    identity: str
    quantity: Decimal
    cost: Decimal | None
    # Exact layer portions retain the shortest cost provenance.
    parts: tuple[tuple[str, Decimal, Decimal | None], ...]


@dataclass(frozen=True, slots=True)
class Result:
    issues: tuple[Issue, ...]
    remaining_quantity: Decimal
    remaining_cost: Decimal | None
    known_remaining_cost: Decimal
    unvalued_quantity: Decimal
    returns: tuple[Issue, ...] = ()


def replay(events: Iterable[Event]) -> Result:
    """Replay one tenant/pool in supplied canonical business order, without mutation."""
    layers: deque[Layer] = deque()
    issued: dict[str, Issue] = {}
    returned: dict[str, Layer] = {}
    reversals = []
    seen: set[str] = set()
    for event in events:
        if event.identity in seen or event.quantity <= 0:
            raise ValueError("Duplicate identity or nonpositive quantity.")
        if money(event.quantity) != event.quantity:
            raise ValueError("Unsupported base quantity precision.")
        seen.add(event.identity)
        if event.kind == "receipt":
            if event.cost is not None and (
                event.cost < 0 or money(event.cost) != event.cost
            ):
                raise ValueError("Invalid receipt cost.")
            layers.append(Layer(event.identity, event.quantity, event.cost))
        elif event.kind == "return":
            original = issued.get(event.original_issue)
            if original is None:
                raise ValueError("Return requires an earlier exact issue.")
            portions = original.parts
            if event.specific_layer is not None:
                portions = tuple(p for p in portions if p[0] == event.specific_layer)
                if len(portions) != 1:
                    raise ValueError("Exact return layer unavailable.")
            elif len(portions) > 1 and event.quantity != original.quantity:
                raise ValueError(
                    "Ambiguous partial return requires original layer identity."
                )
            if event.quantity > sum((p[1] for p in portions), ZERO):
                raise ValueError("Return exceeds original quantity.")
            reversed_parts = []
            for index, (identity, quantity, cost) in enumerate(portions):
                key = original.identity + ":" + identity
                cursor = returned.setdefault(key, Layer(key, quantity, cost))
                part_quantity = event.quantity if len(portions) == 1 else quantity
                part_cost = cursor.take(part_quantity)
                return_id = (
                    event.identity
                    if len(portions) == 1
                    else f"{event.identity}:{index}"
                )
                layers.append(Layer(return_id, part_quantity, part_cost))
                reversed_parts.append(
                    (
                        identity,
                        -part_quantity,
                        None if part_cost is None else -part_cost,
                    )
                )
            reverse_cost = (
                None
                if any(p[2] is None for p in reversed_parts)
                else sum((p[2] for p in reversed_parts), ZERO)
            )
            reversals.append(
                Issue(
                    event.identity, -event.quantity, reverse_cost, tuple(reversed_parts)
                )
            )
        elif event.kind == "transfer":
            if sum((l.quantity - l.used for l in layers), ZERO) < event.quantity:
                raise ValueError("Insufficient stock for transfer.")
        elif event.kind == "issue":
            left = event.quantity
            cost = ZERO
            known = True
            parts = []
            while left > 0:
                if not layers:
                    raise ValueError("Insufficient stock; valuation unavailable.")
                layer = layers[0]
                if event.specific_layer is not None:
                    layer = next(
                        (l for l in layers if l.identity == event.specific_layer), None
                    )
                    if layer is None or layer.quantity - layer.used < left:
                        raise ValueError("Specific identity unavailable.")
                quantity = min(left, layer.quantity - layer.used)
                part_cost = layer.take(quantity)
                parts.append((layer.identity, quantity, part_cost))
                if part_cost is None:
                    known = False
                else:
                    cost += part_cost
                left -= quantity
                if layer.used == layer.quantity:
                    layers.remove(layer)
            issued[event.identity] = Issue(
                event.identity, event.quantity, cost if known else None, tuple(parts)
            )
        else:
            raise ValueError("Unknown movement kind.")
    quantity = sum((l.quantity - l.used for l in layers), ZERO)
    unknown = sum((l.quantity - l.used for l in layers if l.cost is None), ZERO)
    known = sum((l.cost - l.charged for l in layers if l.cost is not None), ZERO)
    return Result(
        tuple(issued.values()),
        quantity,
        None if unknown else known,
        known,
        unknown,
        tuple(reversals),
    )
