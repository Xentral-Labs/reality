# Research: Unit Conversion Between Purchase and Stock Units

Read on 2026-10-01 against `origin/main` at ebf3b6e7. Paths are under `packages/reality-core/src/reality/`.

## R1. Today

- **One number, two meanings.** A movement has no unit column. Against its promise it is compared raw:
  - `validate_commitment_movement_quantity` and `open_quantity` subtract it from the promise, so it reads in the promise's unit.
  - Stock (`stock_at`, `inventory_positions.movement_legs`) and costing (`costing.py`, `base_quantity = movement.quantity` in `item.unit`) add the same number as stock units.
  - Five cartons received against a five-carton order therefore add five pieces to stock.
- **Promises take the line's quantity.** `create_manual_order` defaults a line's unit to the item's stock unit, never the purchase unit, and the promise gets the line quantity unchanged. Commitment has no unit column.
- **Readers that subtract movements from promises raw**: `open_quantity`, `commitment_terms`, `delivery_reads.fulfillment_expressions`, overdue incoming, supply assignments and the supply-and-demand incoming.
- **Readers that convert**: the invoice-matching classes `receipt_unbilled` and `billed_not_received` convert billed lines into the order line's unit and compare that with raw receipts; `item_oversold` converts the promise's open quantity from the line unit.
- **The shared rule** `_in_unit` (`services/exceptions.py`) knows only the item's own pair:
  - purchase unit → stock unit multiplies by the factor;
  - stock unit → purchase unit divides and refuses a remainder;
  - anything else is "no stated relation".
- **Receipt paths**: the reviewed `movement_create`, `shipment_receive` and the Web receipt form all pass a bare quantity. No path names a unit.
- **Master data**: `create_item` and `update_item` require a factor > 0; there is nothing per supplier.

## R2. Design (owner decisions)

- **Promise in the stock unit.** A purchase order line keeps the stated quantity and unit. Its supplier promise is created in the item's stock unit:
  - a line in the stock unit: quantity as stated;
  - a line in the purchase unit: quantity × factor;
  - any other unit: refused, `purchase_unit_not_convertible`.
  - The conversion is the item's own stated relation applied at interpretation, the same rule the exception classes already use, moved to `domain/units.py` so that services and classes share it.
- **Receipt in the stock unit, stated kept.** `record_movement` gains an optional `unit`:
  - stated in the purchase unit, the movement's `quantity` is converted to the stock unit, and `stated_quantity` and `stated_unit` keep what was said;
  - stated in the stock unit or omitted: unchanged, and the stated columns stay empty;
  - another unit is refused, `movement_unit_not_convertible`.
- **Readers.**
  - Everything that subtracts movements from promises now works in one unit for new purchase orders, unchanged.
  - The two invoice-matching classes convert the billed quantity into the stock unit, instead of reading receipts in the line unit, when the order line's promise is in the stock unit.
  - `item_oversold` stops converting a promise that is already in the stock unit.
- **Telling old from new**: the review of T016 found that comparing the promise's quantity with today's factor breaks when master data changes. The owner decided that a supplier promise made since this feature records its unit (`commitment.unit`). A promise without one is in its line's unit. Readers ask `domain/units.promise_held_unit` and convert line quantities by the relation fixed at ordering (`line_in_promise`, `promise_in_line`).
- **Earlier purchase orders** keep their meaning. `units_not_comparable` names an open supplier promise in a purchase unit recorded before the change, with the reason `promise_in_purchase_unit`, so it is not silently mis-summed.
- **Sales lines** are unchanged.

## R3. Reads in both units (FR-002)

- **Delivery case and open-work rows** for a supplier promise state the open and received quantity in the stock unit, and, when the line is in the purchase unit, the same in the purchase unit (exact division, else stock unit only).
- **Movement inspector** shows `5 box (60 pcs)` for a converted receipt.
- **Web receipt form**: offers the stock unit and, when the item states one, the purchase unit, and shows the converted quantity in the review.

## R4. Gates

- **Migration `0106_movement_stated_unit`**:
  - nullable `movement.stated_quantity numeric(18,4)` and `movement.stated_unit`, with a check that both are set or neither;
  - the old-schema trap of spec 299: declared deferred with `FetchedValue`;
  - the downgrade refuses while converted receipts exist.
- **The rest**: refusal codes with translations; the MCP schemas of `movement_create` and `shipment_receive` gain `unit`; catalogs, docs, `data_model.yaml`, and the reference and isolation catalogs if touched.
