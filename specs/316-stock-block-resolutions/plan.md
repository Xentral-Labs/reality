# Implementation Plan: Stock Blocks Keep What Was Stated

**Branch**: `316-stock-block-resolutions` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

A stock block becomes an unchanging statement. Each release or scrap is appended as a
`stock_block_resolution` row. The open quantity (stated less resolved) is derived in one
shared SQL rule that every blocked-stock reader uses. Migration `0109` folds the split
chains of spec 304 into their first block and drops the stored lifecycle columns.

See [data-model.md](data-model.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Storage**: PostgreSQL; migration `0109_stock_block_resolution`

**Testing**:
- service tests (`tests/test_stock_blocks.py`): stated quantity kept, resolutions,
  open quantity, one id, refusals, receipt vs. scrap movement, migration fold
- reader tests (`tests/test_stock_block_readers.py`): every reader after partial
  release and partial scrap
- adapter tests (`tests/test_stock_block_adapters.py`): MCP, Web, CLI shapes and filters
- the stories B05, H08, H15, J05 and the full suite as regression

**Performance Goals**: The shared rule adds one grouped outer join of resolutions per
blocked-stock read. Blocks are few per item and location, so this adds nothing per row.

**Constraints**: availability numbers identical to spec 304 for the same history;
tenant-scoped; reviewed tools unchanged.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The block is the person's statement. Resolutions are later statements about it. A scrap resolution links its adjustment movement. |
| II. Reality is the operational authority | PASS | No document fields. |
| III. Proven schema only | PASS | Resolution quantity is subtracted by every availability read. `kind` is shown and decides whether a movement exists. `receipt_movement_id` is read by the receipt link and the correction guard. |
| IV. Tenant and service boundaries | PASS | Composite tenant FKs. One service path behind every adapter. |
| V. Specification and test evidence | PASS | Tests are changed first per phase; spec 304 tests stay as regression. |
| VI. Explainable Web product | PASS | The block shows what was stated, what is open and each outcome with who and why. |
| VII. Simplicity and storage discipline | PASS | `stock_block` goes from 18 to 13 columns. The resolution table has 9. No stored lifecycle state. See Complexity Tracking for the added table. |
| VIII. Received values are recorded, never recomputed | PASS | This is the defect being fixed: the stated quantity is no longer overwritten. |

## Design

1. **Schema** (`db/core.py`, migration `0109`):
   - `stock_block`: drop `status`, `resolved_at`, `resolved_by`, `resolution_reason`,
     `previous_block_id`. Rename `movement_id` → `receipt_movement_id`. Replace index
     `(tenant, item, location, status)` with `(tenant, item, location)`.
   - New `stock_block_resolution`: `id`, `tenant_id`, `block_id`, `kind`
     (`release`|`scrap`), `quantity > 0`, `reason` (non-blank), `resolved_at`,
     `resolved_by`, `movement_id`. Check `(kind = 'scrap') = (movement_id IS NOT NULL)`.
     Unique movement. The movement FK is `DEFERRABLE INITIALLY DEFERRED`, so a scrap
     row is written once with its final movement id. The resolution has to exist before
     the adjustment runs, or the adjustment would be refused for taking stock that is
     still blocked.
   - Data fold: walk each `previous_block_id` chain from its root. The root's quantity
     becomes the sum of the chain. Every closed row becomes a resolution with its own
     id, quantity, reason, who, when and, for a scrap, its movement. Continuation rows
     are deleted. The receipt movement of a root that a whole scrap overwrote is taken
     from that block's `stock_block.created` event payload.
   - Downgrade refuses while resolutions exist. Otherwise it restores the columns
     (`status = 'active'`, `movement_id = receipt_movement_id`).
2. **Shared rule** (`services/core.py`): `_open_stock_blocks(tenant_id)` returns a
   subquery of open blocks with their identity and `quantity` = open quantity.
   `blocked_quantity` and `blocked_within_identity` sum it. The five bulk readers select
   from it instead of `StockBlock.status == 'active'`:
   - `core.py` item supply
   - `web/read_models.py`
   - `inventory_positions.py`
   - `projections.py`
   - `exceptions._blocked_by_item_location`

   The correction guard reads `StockBlockResolution.movement_id`.
3. **Service** (`services/stock_blocks.py`):
   - `release_stock_block` and `scrap_stock_block` append one resolution and return
     `{block_id, released|scrapped, open_quantity[, movement_id]}`.
   - The list filters `active|resolved|all` on the derived open quantity.
   - Rows carry `quantity` (stated), `open_quantity`, `status` (derived), `resolutions`
     and `receipt_movement_id`.
   - Validation checks against the open quantity (`stock_block_not_active` when 0).
   - The review carries the open quantity it saw.
   - `record_movement` / `_append_movement` take a private `_movement_id`.
4. **Adapters**:
   - The MCP `status` enum becomes `active|resolved|all`. Web, CLI and the tool handler
     are pass-through.
   - The web list and card show the open quantity, plus the stated quantity when it
     differs, and prefill the open quantity.
   - `api.ts` types.
   - `make docs-generate`.
5. **Gates**: reporting-graph coverage, schema FK indexes (`later_tables`),
   isolation catalog and its pinned count, coverage matrix, `docs/DATA_MODEL.md`,
   `docs/features/inventory.md`.

## Rollback

The downgrade refuses while any resolution exists. That is the same stance as `0108`:
history is not discarded to make a downgrade possible.

## Complexity Tracking

| Addition | Why needed | Simpler alternative rejected because |
|---|---|---|
| Table `stock_block_resolution` | One block can have several outcomes, each with its own quantity, reason, who and when. Overwriting the block destroys the stated quantity. | Facts carry no typed quantity or movement link, and availability sums the quantity in SQL. Columns on the block allow only one outcome, which is the current defect. |
