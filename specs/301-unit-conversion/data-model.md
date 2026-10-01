# Data Model: Unit Conversion Between Purchase and Stock Units

## Changed: `movement`

| Field | Type | Why |
|---|---|---|
| `stated_quantity` | numeric(18,4), nullable | The quantity a receipt was stated in, when that differs from the stock unit (FR-002). |
| `stated_unit` | text, nullable | The unit it was stated in, e.g. `box`. |

- **Check**: `stated_quantity` and `stated_unit` are both set or both empty.
- **Rule**: `quantity` is always in the item's stock unit from now on. The stated values are evidence of what was said; they are never read back into stock.
- **Typed, not payload**: the inspector and the purchase reads show them on every receipt, and the downgrade guard filters on them (Constitution III).

## Unchanged schema, changed meaning for new purchase orders

- **`commitment.quantity`** of a supplier promise is in the item's stock unit. The line keeps the stated quantity and unit.
- **Old or new**: `domain/units.promise_unit(commitment, line, item)` tells a promise recorded before this feature, in the line's unit, from a new one.

## Not changed

- **Item**: `unit`, `purchase_unit` and `conversion_factor`, one purchase unit per item.
- **Sales lines and customer promises.**
