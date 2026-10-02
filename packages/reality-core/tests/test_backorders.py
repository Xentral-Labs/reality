"""Spec 305: serving backorders, the split of assigned supply, available-to-promise."""

from decimal import Decimal

from reality.services import core
from reality.services.supply_assignments import (
    assign_supply,
    reverse_supply_assignment,
    supply_coverage,
)


def _promise(session, business, quantity, due="2026-10-20", location=None):
    return core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        (location or business.location).id,
        quantity,
        due,
    )


def _purchase(session, business, quantity, due="2026-10-12"):
    return core.create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        quantity,
        due,
    )


def _assign(session, business, purchase, promise, quantity, request):
    return assign_supply(
        session,
        business.tenant.id,
        purchase.id,
        quantity,
        purpose="customer_demand",
        customer_commitment_id=promise.id,
        request_id=request,
    )


def _receive(session, business, purchase, quantity):
    return core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        commitment_id=purchase.id,
    )


def _split(session, business, promise):
    customer = supply_coverage(
        session, business.tenant.id, customer_commitment_id=promise.id
    )["customer"]
    return customer["arrived"], customer["still_to_come"]


# --- split of assigned supply (FR-006) -------------------------------------------------


def test_a_partial_receipt_covers_the_assignments_in_their_order(session, business):
    purchase = _purchase(session, business, "9")
    promises = [_promise(session, business, "3") for _ in range(3)]
    for n, promise in enumerate(promises):
        _assign(session, business, purchase, promise, "3", f"split-{n}")
    # Positive control: before anything arrives, everything is still to come.
    assert [_split(session, business, p) for p in promises] == [(0, 3)] * 3

    _receive(session, business, purchase, "4")

    assert [_split(session, business, p) for p in promises] == [
        (3, 0),
        (1, 2),
        (0, 3),
    ]
    items = supply_coverage(
        session, business.tenant.id, supplier_commitment_id=purchase.id
    )["items"]
    assert [(row["arrived"], row["still_to_come"]) for row in items] == [
        (3, 0),
        (1, 2),
        (0, 3),
    ]
    # The total stays what was assigned.
    assert supply_coverage(
        session, business.tenant.id, customer_commitment_id=promises[1].id
    )["customer"]["protecting_supply"] == Decimal(3)


def test_a_cancelled_or_reversed_assignment_leaves_the_order(session, business):
    purchase = _purchase(session, business, "9")
    first, second, third = (_promise(session, business, "3") for _ in range(3))
    reversed_row = _assign(session, business, purchase, first, "3", "order-1")
    _assign(session, business, purchase, second, "3", "order-2")
    _assign(session, business, purchase, third, "3", "order-3")
    reverse_supply_assignment(
        session,
        business.tenant.id,
        reversed_row.id,
        "3",
        reason="Customer takes stock instead",
        request_id="order-reverse",
    )
    core.cancel_commitment(
        session, business.tenant.id, second.id, reason="Customer withdrew"
    )

    _receive(session, business, purchase, "4")

    assert _split(session, business, third) == (3, 0)
