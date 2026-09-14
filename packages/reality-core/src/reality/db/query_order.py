"""Explicit SQL column ordering shared by bounded register reads."""

from typing import Any


def query_order(
    sort: str, direction: str, columns: dict[str, Any], identity: Any, default: tuple
) -> tuple:
    if direction not in {"asc", "desc"}:
        raise ValueError("Unsupported sort direction.")
    if not sort:
        return default
    if sort not in columns:
        raise ValueError("Unsupported sort column.")
    column = columns[sort]
    return (
        (column.desc() if direction == "desc" else column.asc()).nulls_last(),
        identity.asc(),
    )
