"""The one rule for expressing a quantity in another unit.

The only relation Reality holds is the one an item states between its own stock
unit and its own purchase unit: "we buy this in boxes of twelve", written down
by the company. The exception classes compare with it at read time (spec 087),
and since spec 301 a purchase in the purchase unit is interpreted with it into
the stock unit. Both ask here, so they cannot disagree.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

ZERO = Decimal(0)


def in_unit(
    item: Any | None, quantity: Decimal, recorded: str, target: str
) -> Decimal | None:
    """A quantity recorded in one unit, expressed in another, or None.

    Multiplying a stated quantity by a stated factor stores no second authority
    for either of them. Three things stop it, and each is a company that has not
    said enough: no item to carry a statement, a factor that states nothing, and
    a pair the statement does not cover. A fourth stops it although everything
    was said: a conversion leaving a remainder, because a hundred and seven
    pieces are not a number of boxes, and rounding them into one is the thing
    this product exists not to do.
    """
    if recorded == target:
        return quantity
    if item is None:
        return None
    factor = Decimal(item.conversion_factor)
    if factor <= ZERO:
        return None
    if recorded == item.purchase_unit and target == item.unit:
        return quantity * factor
    if recorded == item.unit and target == item.purchase_unit:
        whole, remainder = divmod(quantity, factor)
        return whole if remainder == ZERO else None
    return None


def decline_reason(item: Any | None, recorded: str, target: str) -> str:
    """Which of the two went wrong, because their exits are different.

    A relation nobody stated is master data to fill in. A relation that is
    stated and does not divide is a company that ordered ten boxes and delivered
    a hundred and seven pieces, and telling it to state the relation would be
    advice it has already taken.
    """
    if item is None or Decimal(item.conversion_factor) <= ZERO:
        return "no_stated_relation"
    if {recorded, target} != {item.unit, item.purchase_unit}:
        return "no_stated_relation"
    return "conversion_leaves_a_remainder"


def promise_held_unit(commitment_unit: str | None, line: Any | None, item_unit: str) -> str:
    """The unit a promise's quantity is held in.

    Since spec 301 a purchase promise records the unit it was made in, the
    item's stock unit at the time of ordering. A promise recorded before kept
    its line's quantity as stated, in the line's unit, and says nothing; one
    without a line was always in the item's unit. Reading the marker rather
    than today's master data means a factor changed after ordering changes no
    promise.
    """
    if commitment_unit:
        return commitment_unit
    return line.unit if line is not None else item_unit


def line_in_promise(
    quantity: Decimal, line: Any, promised: Decimal, held: str
) -> Decimal | None:
    """A quantity in an order line's unit, in the unit its promise is held in.

    The relation is the one fixed when the line was promised: its quantity
    against the promise's original quantity, so five cartons that became sixty
    pieces stay twelve pieces a carton whatever the item says later.
    """
    if line.unit == held:
        return quantity
    stated = Decimal(line.quantity)
    if stated <= ZERO:
        return None
    return quantity * Decimal(promised) / stated


def promise_in_line(
    quantity: Decimal, line: Any, promised: Decimal, held: str
) -> Decimal | None:
    """The inverse: a promise-unit quantity in the line's unit, if it is whole."""
    if line.unit == held:
        return quantity
    if Decimal(promised) <= ZERO:
        return None
    whole, remainder = divmod(quantity * Decimal(line.quantity), Decimal(promised))
    return whole if remainder == ZERO else None
