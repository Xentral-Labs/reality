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


def promise_unit(promised: Decimal, line: Any | None, item: Any) -> str:
    """Whether a promise is held in the stock unit or in its line's unit.

    Since spec 301 a purchase line in the purchase unit promises its quantity in
    the stock unit. A promise recorded before kept the line's quantity as
    stated, in the line's unit, and was not converted. The two are told apart by
    the one fact that differs: the promise's original quantity.
    """
    if line is None or line.unit == item.unit:
        return "stock"
    converted = in_unit(item, Decimal(line.quantity), line.unit, item.unit)
    if converted is not None and Decimal(promised) == converted:
        return "stock"
    return "line"
