# Tasks: Stock Count Sessions

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/stock-count.md](contracts/stock-count.md)

Tests come first in each phase where practical.

## Phase 1: Setup

- [x] T001 Clarify the spec with the owner (Clarifications 2026-10-02)
- [x] T002 Plan, research, data model, contract, quickstart
- [x] T003 Tasks

## Phase 2: Count record and posting (FR-001, FR-002, FR-005)

- [x] T004 Tests:
  - schema checks and the migration downgrade;
  - book as of the counting time;
  - gain and loss;
  - a loss partly from blocks;
  - a loss beyond stock;
  - refusals;
  - lots;
  - the review's reservations;
  - a replayed confirmation;
  - tenant isolation.
- [x] T005 Migration `0113`, the models, `services/stock_counts.py`, the event, the refusals with translations

## Phase 3: Adapters and gates (FR-003)

- [x] T006 Tools, MCP, Web and CLI, with adapter tests
- [x] T007 Catalog gates:
  - data model and docs field rows;
  - reporting graph;
  - command and action catalogs, tool topics;
  - isolation catalog and counts;
  - events and counts;
  - resource catalog and labels;
  - coverage matrix and docs generation.

## Phase 4: Web

- [x] T008 "Inventur" on the warehouse stock view, the counting card, the count list, translations, browser fixtures

## Phase 5: Stories and Guide (FR-004)

- [x] T009 Business stories J02, J03 and R07
- [x] T010 Promote the journeys:
  - the Guide catalog and Guide tests;
  - coverage and roadmap;
  - `docs/features/inventory.md`;
  - the spec 304 limitation.

## Phase 6: Verification

- [ ] T011 Full backend suite and web checks
- [ ] T012 Manual check per `quickstart.md`
- [x] T013 Review of the diff; fix findings
  - The count's adjustments are dated at the counting time, so the same sheet counted twice posts its loss once.
  - A counting time before the goods first came, or without its offset, is refused.
  - The stale check compares where a loss would come from, not only the book.
  - Corrected movements and their compensations leave the book.
  - The reservations named are per location and leave blocked stock out.
  - The detail reads lines from the records and their movements.
  - The web card guards double clicks, withdraws after a failed confirmation, and says how lot-tracked items are counted.
  - Indexes on `(tenant_id, item_id)` and `(tenant_id, lot_id)`.
  - Tests for each of these, plus the replay and the block resolution's citation.
