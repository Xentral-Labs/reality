"""Pure quantity rules for explicit supplier-supply assignments."""

from __future__ import annotations

from decimal import Decimal

from reality.domain.refusals import DomainRefusal


def available_assignment_quantity(
    stated_quantity: Decimal, effective_assignments: Decimal
) -> Decimal:
    """Return unassigned stated supply without confusing receipts with intent."""
    return max(Decimal(0), stated_quantity - effective_assignments)


def assignable_demand_quantity(
    stated_quantity: Decimal, open_quantity: Decimal, protecting_supply: Decimal
) -> Decimal:
    """Return customer demand that further supply may still protect.

    Assignments are totals against the stated demand, so what is already protected
    is not assignable again; delivery is not attributed to supply, so the open
    quantity bounds each new statement as well.
    """
    return max(Decimal(0), min(open_quantity, stated_quantity - protecting_supply))


def validate_assignment_quantity(
    quantity: Decimal, supplier_available: Decimal, customer_open: Decimal | None
) -> None:
    if quantity <= 0:
        raise DomainRefusal(code="supply_assignment_quantity_not_positive")
    if quantity > supplier_available:
        raise DomainRefusal(code="supply_assignment_exceeds_supplier")
    if customer_open is not None and quantity > customer_open:
        raise DomainRefusal(code="supply_assignment_exceeds_demand")
