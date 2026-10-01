# Research: Blocked Stock and Best-Before Dates

## R1. Today

- **No blocked state.** Quality holds, quarantine and expiry work only by moving goods to another location. Item-wide reads (`inventory_rows`, `item_oversold`, `reservation_exceeds_stock`) still count that location as available.
- **Expiry blocks nothing, by decision.** `docs/features/inventory.md` and `docs/features/operational_exceptions.md` say so, and `test_expiry_blocks_nothing` pins it. `stock_expired` reports expired lots with stock.
- **Scrap** is an outbound `adjustment` with a free-text reason. Return dispositions `quarantine_repair` and `scrap_loss` are a transfer and an adjustment for customer returns only.
- **Receipts** carry no condition. A damaged part can only be received, then transferred or adjusted.
- **Identity dimensions:** movements and reservations carry `handling_unit_id`, `lot_id` and `serial_unit_id`. `stock_by_identity` and `reserved_by_identity` filter on item, location and any identity.
- **Places that judge availability or physical stock for reserving, shipping or reporting:**
  - `_preview_reservation`
  - `_append_movement` (outbound physical checks)
  - `inventory_rows`
  - `inventory_detail_rows`
  - `fulfillment_readiness` / `stock_cover`
  - the open-work projection
  - `item_oversold`, `reorder_point_reached`, `stock_in_another_location` and `stock_expired`
- **Journeys:**
  - B05 and J05 are partial.
  - H08 and H15 are missing.

## R2. Design (owner decisions, 2026-10-02)

- **`stock_block` table:**
  - Fields: item, location, optional lot, handling unit and serial unit; quantity; `reason_code` (quality, damage, expiry, inspection); note; status (active, released, scrapped).
  - It records who and when for both creation and resolution, the resolution reason, `previous_block_id` and `movement_id`. `movement_id` is the receipt that created the block, or the adjustment that scrapped it.
  - A partial release or scrap closes the row for the part and opens a new active row for the rest, the reservation pattern (`previous_block_id`).
- **One rule:** `blocked_quantity(session, tenant, item, location=None, *, handling_unit_id, lot_id, serial_unit_id)`, alongside `stock_at` and `active_reserved`.
  - Available = physical − reserved − blocked, at the location and at identity level.
  - Every reader in R1 subtracts it.
  - Outbound movements (shipment, transfer, supplier return, outbound adjustment) may not take blocked stock.
  - A scrap's own adjustment consumes the block in the same step.
- **Bounds:**
  - A block may not exceed physical − reserved − already blocked at its identity, so stock reserved for an order is never blocked under it.
  - A release or scrap may not exceed the block's active quantity.
- **Reviewed tools:**
  - `stock_block`, `stock_block_release`, `stock_block_scrap`, and the read `stock_blocks`.
  - The receipt (`movement_create` receipt and `shipment_receive` movements) takes `blocked_quantity` and `block_reason`. Its review shows them, and its execution creates the block linked to the receipt movement.
- **Expiry:** `stock_expired` counts expired stock that is not blocked. Blocking it clears the finding, and the Web's finding offers "Block".

## R3. Alternatives rejected

- **A "blocked" location**: blocking would create movements (FR-003), and item-wide reads would still count the stock.
- **Automatic expiry blocking**: reverses the documented decision, by owner choice.
- **A block column on the movement**: a block is released later, by someone else, and must keep that history.

## R4. Gates

- **New table:** migration, data model and docs rows, reporting-graph deferral, reference and isolation catalogs, event catalog plus the `_literal_business_events` module list, resource catalog, coverage matrix.
- **New tools:** command catalog (commands, guidance, coverage, parameter descriptions), discovery group plus the web fixture, `tool_catalog` mcp_topics, pinned counts, refusal codes plus translations.
- **Changed readers:** the inventory and readiness suites as regression. `test_expiry_blocks_nothing` changes on purpose: expiry still blocks nothing by itself, and a person's block does.
