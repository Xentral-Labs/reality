# Implementation Plan: Stock Count Sessions

**Branch**: `307-stock-count` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

A count states, for one location, what was counted: per line the item, the lot where it is tracked, the counted quantity and the counting time. One reviewed confirmation records the count and posts its differences.

- The book quantity per line is read from the movements up to the counting time. It is never stored, and movements after it carry on.
- A gain is an adjustment into the location. A loss is an adjustment out of free stock; what free stock does not cover is scrapped from the location's blocks through the spec 304/316 scrap, with the count as the reason. Each line names the movement or movements that posted it.
- The review shows book, counted and difference per line, which part comes from blocks, and the reservations at the location the loss leaves uncovered.

See [research.md](research.md), [data-model.md](data-model.md) and [contracts/stock-count.md](contracts/stock-count.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Storage**: PostgreSQL; migration `0113_stock_count`

**Testing**:
- service tests: book as of the counting time, gains, losses, blocks, refusals, isolation;
- adapter tests;
- business stories J02, J03 and R07;
- the inventory, block and reservation suites as regression;
- web checks, browser fixtures and the full suite.

**Performance Goals**: The book quantity is read with one grouped query per count, not per line.

**Constraints**:
- adjustments only through `record_movement` and the block scrap;
- importers untouched;
- tenant-scoped;
- reviewed tools.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The count is a person's statement, kept as a source version (`internal_stock_count`); the count row names it, and every posting movement is linked from its line. |
| II. Reality is the operational authority | PASS | No document status; stock changes only through movements. |
| III. Proven schema only | PASS | Lines are read to post, to review and to explain each adjustment; counted quantity and time are what the posting acts on. |
| IV. Tenant and service boundaries | PASS | Composite tenant FKs; one service path behind every adapter. |
| V. Specification and test evidence | PASS | Tests planned per phase, with positive controls. |
| VI. Explainable Web product | PASS | Each adjustment links back to its count line, and the count to its statement and location. |
| VII. Simplicity and storage discipline | PASS | Two tables; book quantities and differences are read-time observations, and the posted adjustment states what it moved. |
| VIII. Received values are recorded, never recomputed | PASS | Counted quantity and counting time are kept as stated; the book is never stored. |

## Design

1. **Schema and services:**
   - Migration `0113`, models `StockCount` and `StockCountLine`.
   - `services/stock_counts.py`:
     - `book_as_of(item, location, lot, at)`;
     - `review_stock_count`;
     - `record_stock_count`, which records and posts;
     - `stock_counts` and `stock_count_detail` (reads).
   - The event `stock_count.posted` and the refusals.
2. **Posting:**
   - Per line, the difference is the counted quantity less the book at the counting time.
   - A gain is `record_movement("adjustment", to_location)`.
   - A loss takes free stock now (physical less blocked) first, then calls `scrap_stock_block` on the location's open blocks for the item and lot, oldest first.
   - Each adjustment names the count line (`movement_id` on the line for the free part; the scrap's own movements are listed by the line's resolutions). Every adjustment carries the reason `count <number>: <note>`.
3. **Review:** book, counted and difference per line, the part from blocks, and the reservations at the location left uncovered (reserved at the location above physical after the loss, by item).
4. **Adapters:**
   - tools `stock_count` (reviewed) and `stock_counts` / `stock_count_detail` (reads);
   - MCP propose and reads;
   - Web `GET /stock-counts`, `GET /stock-counts/{id}` and `POST /stock-counts/proposals`;
   - CLI `stock-count list|show|record`.
5. **Web:** "Inventur" on the warehouse stock view of a location, a counting card with editable counted quantities, the review and the confirmation, the count list with its adjustments, and translations.
6. **Stories and Guide:**
   - J02: gain and loss.
   - J03: a count during operation, with a shipment after the counting time.
   - R07: three reservations, a loss, the finding naming them.
   - Then the promotion, coverage, roadmap, matrix and docs, including `docs/features/inventory.md` and the spec 304 limitation it resolves.

## Rollback

The downgrade refuses while counts exist. Without counts, nothing changes.

## Complexity Tracking

No Constitution violations.
