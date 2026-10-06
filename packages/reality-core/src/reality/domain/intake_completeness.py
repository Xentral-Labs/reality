"""Pure essential-value rules and non-authoritative order observations (spec 379)."""

from collections.abc import Mapping, Sequence
from typing import Any


class MissingEssentialValue(ValueError):
    def __init__(self, field: str) -> None:
        self.field = field
        super().__init__(field)


def is_unstated(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or is_unstated(value):
        raise MissingEssentialValue(field)
    return value.strip()


def order_issues(
    document: Mapping[str, Any], lines: Sequence[Mapping[str, Any]]
) -> tuple[str, ...]:
    """Observe missing statements without supplying values or rejecting an order."""
    issues = []
    for field, label in (
        ("document_date", "document date"),
        ("ordered_at", "order time"),
        ("requested_delivery_at", "agreed delivery date"),
        ("gross_amount", "order total"),
    ):
        if is_unstated(document.get(field)):
            issues.append(f"Order states no {label}.")
    for index, line in enumerate(lines, 1):
        for field, label in (
            ("unit_price", "unit price"),
            ("gross_amount", "line amount"),
        ):
            if is_unstated(line.get(field)):
                issues.append(f"Line {index} states no {label}.")
    return tuple(issues)


def stock_unit_matches(stated_unit: str, stock_unit: str) -> bool:
    """Sales promises have no implicit box/piece conversion."""
    return stated_unit.strip() == stock_unit.strip()
