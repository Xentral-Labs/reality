"""Optional locale-aware presentation parts; original Inspector values stay compatible."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any


class DisplayText(str):
    parts: list[dict[str, Any]]

    def __new__(cls, value: str, parts: list[dict[str, Any]]):
        result = super().__new__(cls, value)
        result.parts = parts
        return result


def display_parts(value: Any) -> list[dict[str, Any]] | None:
    if isinstance(value, DisplayText):
        return value.parts
    if isinstance(value, datetime):
        return [{"type": "datetime", "value": value.isoformat()}]
    if isinstance(value, date):
        return [{"type": "date", "value": value.isoformat()}]
    if isinstance(value, (Decimal, int)) and not isinstance(value, bool):
        return [{"type": "number", "value": str(value)}]
    return None


def display_text(*values: Any) -> DisplayText:
    parts = []
    for value in values:
        parts.extend(display_parts(value) or [{"type": "text", "value": str(value)}])
    return DisplayText("".join(str(value) for value in values), parts)


def money(
    value: Any, currency: str | None, *, precision: int | None = None
) -> DisplayText:
    if not currency:
        return display_text(value)
    return DisplayText(
        f"{currency} {value}",
        [
            {
                "type": "money",
                "value": str(value),
                "currency": currency,
                **({"precision": precision} if precision is not None else {}),
            }
        ],
    )
