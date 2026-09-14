from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


class ShipmentCompatibilityError(ValueError):
    """A shipment purpose, direction, or physical movement contradicts another."""


PURPOSES = {
    "customer_delivery": ("outbound", "shipment", "customer"),
    "supplier_delivery": ("inbound", "receipt", "supplier"),
    "customer_return": ("inbound", "return", "customer"),
    "supplier_return": ("outbound", "supplier_return", "supplier"),
}
DIRECTIONS = frozenset({"inbound", "outbound"})
EVENT_TYPES = frozenset(
    {
        "announced",
        "handed_over",
        "in_transit",
        "delivered",
        "delivery_exception",
        "received",
    }
)
REPORTER_TYPES = frozenset({"company", "counterparty", "carrier", "integration"})


def validate_shipment_direction(purpose: str, direction: str) -> None:
    expected = PURPOSES.get(purpose)
    if expected is None:
        raise ShipmentCompatibilityError("Unsupported shipment purpose.")
    if direction != expected[0]:
        raise ShipmentCompatibilityError(
            "Shipment direction does not match its purpose."
        )


def validate_movement_compatibility(
    purpose: str, direction: str, movement_type: str
) -> None:
    validate_shipment_direction(purpose, direction)
    if movement_type != PURPOSES[purpose][1]:
        raise ShipmentCompatibilityError(
            "Movement type does not match the shipment purpose."
        )


def required_party_role(purpose: str) -> str:
    if purpose not in PURPOSES:
        raise ShipmentCompatibilityError("Unsupported shipment purpose.")
    return PURPOSES[purpose][2]


def current_observations(
    *,
    direction: str,
    package_ids: Sequence[str],
    effective_movements: Iterable[Mapping[str, Any]],
    current_events: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    if direction not in DIRECTIONS:
        raise ShipmentCompatibilityError("Unsupported shipment direction.")
    movements = tuple(effective_movements)
    events = tuple(current_events)
    moved = bool(movements)
    delivered_packages = {
        event.get("package_id")
        for event in events
        if event.get("event_type") == "delivered" and event.get("package_id")
    }
    applicable = set(package_ids)
    movement_times = [row.get("occurred_at") for row in movements if row.get("occurred_at")]
    announced_times = [
        row.get("occurred_at")
        for row in events
        if row.get("event_type") == "announced" and row.get("occurred_at")
    ]
    delivered_times = [
        row.get("occurred_at")
        for row in events
        if row.get("event_type") == "delivered" and row.get("occurred_at")
    ]
    externally_delivered = bool(applicable) and applicable.issubset(delivered_packages)
    return {
        "announced": any(event.get("event_type") == "announced" for event in events),
        "announced_at": min(announced_times) if announced_times else None,
        "dispatched": direction == "outbound" and moved,
        "dispatched_at": (
            min(movement_times) if direction == "outbound" and movement_times else None
        ),
        "received": direction == "inbound" and moved,
        "received_at": (
            min(movement_times) if direction == "inbound" and movement_times else None
        ),
        "externally_delivered": externally_delivered,
        "externally_delivered_at": (
            max(delivered_times) if externally_delivered and delivered_times else None
        ),
        "has_exception": any(
            event.get("event_type") == "delivery_exception" for event in events
        ),
    }
