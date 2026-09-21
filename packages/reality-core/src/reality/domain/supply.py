"""Pure quantity rules for explicit supplier-supply assignments."""

from __future__ import annotations

from decimal import Decimal


def available_assignment_quantity(
    stated_quantity: Decimal, effective_assignments: Decimal
) -> Decimal:
    """Return unassigned stated supply without confusing receipts with intent."""
    return max(Decimal(0), stated_quantity - effective_assignments)


def validate_assignment_quantity(
    quantity: Decimal, supplier_available: Decimal, customer_open: Decimal | None
) -> None:
    if quantity <= 0:
        raise ValueError("Supply assignment quantity must be positive.")
    if quantity > supplier_available:
        raise ValueError("Supply assignment exceeds unassigned supplier quantity.")
    if customer_open is not None and quantity > customer_open:
        raise ValueError("Supply assignment exceeds open customer demand.")
