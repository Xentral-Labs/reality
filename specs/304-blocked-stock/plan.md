# Implementation Plan: Blocked Stock and Best-Before Dates

**Branch**: `304-blocked-stock` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

Stock can be blocked where it lies, with a reason and optionally on its exact lot, pallet or serial. No movement is created.

Blocked stock is excluded from every availability reader and from reserving, shipping and transferring. A block is released or scrapped, wholly or partly, through the review, and scrapping records the reasoned adjustment.

A reviewed receipt can block part or all of what it receives (H08, H15). The expired-stock finding offers to block the lot (J05). Expiry still blocks nothing by itself.

See [research.md](research.md), [data-model.md](data-model.md) and [contracts/blocked-stock.md](contracts/blocked-stock.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Storage**: PostgreSQL; migration `0108_stock_block`

**Testing**:
- service, reader, exception, adapter and story tests
- the inventory, readiness and shipment suites as regression
- web checks and browser fixtures
- the full suite

**Performance Goals**: Readers add one grouped blocked-quantity read beside their reservation read, and nothing per row.

**Constraints**:
- unchanged results without blocks;
- no movement for a block or release;
- tenant-scoped;
- reviewed tools.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | A block is a person's statement about held stock; a receipt's block links to its receipt movement. |
| II. Reality is the operational authority | PASS | No document status; availability is read from movements, reservations and blocks. |
| III. Proven schema only | PASS | Every availability read filters and subtracts active blocks; reason and status are filtered and shown. |
| IV. Tenant and service boundaries | PASS | Composite tenant FKs; one service path behind every adapter. |
| V. Specification and test evidence | PASS | Tests planned per phase; regression on existing readers. |
| VI. Explainable Web product | PASS | Blocked quantities show their reason, who blocked them and the receipt or scrap they belong to. |
| VII. Simplicity and storage discipline | PASS | One rule beside `stock_at`; the reservation split pattern for partial resolution. |
| VIII. Received values are recorded, never recomputed | PASS | Stated quantities and reasons are kept as stated. |

## Design

1. **Schema and services:**
   - Migration `0108`, the `StockBlock` model and `services/stock_blocks.py` (block, release, scrap, list), with events and refusals.
   - `blocked_quantity` and `blocked_by_identity` in `core.py`.
2. **Readers:**
   - Subtract active blocks in `_preview_reservation`, the outbound checks of `_append_movement` (the scrap's adjustment is exempt for its own block), `inventory_rows` (with a `blocked` field), `inventory_detail_rows`, and the readiness rule and open-work projection (physical basis less blocked).
   - Do the same in `item_oversold`, `reorder_point_reached`, `stock_in_another_location` and `stock_expired` (unblocked expired stock only).
   - Projection invalidation: the `stock_block.*` events invalidate Inventory, Item supply and demand, Fulfillment queue and blockers, Operational Exceptions and Timeline.
3. **Receipt:** `blocked_quantity` and `block_reason` on `movement_create` receipt and on `shipment_receive` movements. The review shows them, and the block is created after the receipt movement in the same transaction.
4. **Adapters:** delivery-action reviews for the three tools; MCP propose tools and the read; Web pass-through and a GET; the CLI `stock` group.
5. **Web:**
   - The warehouse stock view shows "Blocked" and "Block".
   - A blocks list with release and scrap through the review.
   - "Of which blocked" in the receipt form.
   - "Block" on the expired-stock finding.
   - Translations.
6. **Stories and Guide:**
   - B05: 20 in stock, 5 blocked for quality, 15 reservable; release restores them.
   - H08: a receipt of 20 with 5 damaged blocked, then the 5 scrapped.
   - H15: received blocked for inspection, nothing reservable, released days later.
   - J05: an expired lot is named, blocked from the finding and scrapped.
   - Then the promotion, coverage, roadmap, matrix and docs (including `docs/features/inventory.md`).

## Rollback

The downgrade refuses while blocks exist. Without blocks, every reader reads as before.

## Complexity Tracking

No Constitution violations.
