# Data Model: Unit Conversion Between Purchase and Stock Units

## Changed: `movement`

| Field | Type | Why |
|---|---|---|
| `stated_quantity` | numeric(18,4), nullable | The quantity a receipt was stated in, when that differs from the stock unit (FR-002). |
| `stated_unit` | text, nullable | The unit it was stated in, e.g. `box`. |

- **Check**: `stated_quantity` and `stated_unit` are both set or both empty.
- **Rule**: `quantity` is always in the item's stock unit from now on. The stated values are evidence of what was said; they are never read back into stock.
- **Typed, not payload**: the inspector and the purchase reads show them on every receipt, and the downgrade guard filters on them (Constitution III).

## Changed: `commitment`

| Field | Type | Why |
|---|---|---|
| `unit` | text, nullable | The unit a promise's quantity is held in. It is set on supplier promises made since this feature, to the item's stock unit at ordering. |

- **Empty**: the promise is in its line's unit, or in the item's unit when it has no line. That covers every promise recorded before this feature, and every customer promise.
- **Relation fixed at ordering**: a line quantity is converted into the promise by the line quantity against the promise's original quantity, for example 5 cartons → 60 pieces. It is not converted by today's item factor, so a factor changed after ordering changes no promise (review of T016, owner decision).
- **Typed, not derived**: telling old promises from new by comparing quantities with the current factor broke when master data changed. Every reader in `domain/units.py` (`promise_held_unit`, `line_in_promise`, `promise_in_line`) filters on the unit: exceptions, billable positions, the purchase view and the receipt check.
- **Downgrade**: refused while any promise carries a unit.

## Not changed

- **Item**: `unit`, `purchase_unit` and `conversion_factor`, one purchase unit per item.
- **Sales lines and customer promises.**
