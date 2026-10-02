# Tasks: Serving Backorders on Receipt

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/backorders.md](contracts/backorders.md)

Tests come first in each phase where practical.

## Phase 1: Setup

- [x] T001 Clarify the spec with the owner (Clarifications 2026-10-02)
- [x] T002 Plan, research, data model, contract, quickstart
- [x] T003 Tasks

## Phase 2: Split of assigned supply (FR-006)

- [x] T004 Tests: a receipt of 4 against 3 + 3 + 3 shows 3/0, 1/2, 0/3; a cancelled or reversed assignment drops out of the order; without receipts everything is still to come
- [x] T005 `assignment_split` and the `arrived` / `still_to_come` fields in `supply_coverage`

## Phase 3: Serving backorders (FR-001, FR-004)

- [x] T006 Tests:
  - serving order (assigned first, then due date, then promised);
  - stated lines and their refusals;
  - held promises listed apart;
  - tracked items refused;
  - stale confirmation refused;
  - blocked stock not served;
  - positive controls.
- [x] T007 `services/backorders.py` (`waiting_promises`, `review_backorder_serving`, `serve_backorders`), the tool, the proposal review, and the refusals with translations

## Phase 4: Available-to-promise (FR-003)

- [x] T008 Tests:
  - free now with and without waiting need;
  - purchases by date with their assignments;
  - overdue purchase;
  - a cancelled promise leaves the answer.
- [x] T009 `available_to_promise` and its read tool

## Phase 5: Adapters and gates

- [x] T010 MCP, Web and CLI, with adapter tests and tenant isolation
- [x] T011 Catalog gates:
  - command and action catalogs, tool topics;
  - isolation catalog and counts;
  - resource catalog and labels;
  - coverage matrix and docs generation.

## Phase 6: Web

- [x] T012 The serving card, "Serve backorders" after a receipt and on the warehouse row, available-to-promise in the row preview, translations, and browser fixtures

## Phase 7: Stories and Guide (FR-002, FR-005)

- [x] T013 Business stories for B07, B08, B09 (rewrite the pinned test), G13, H16 and R02
- [x] T014 Promote the journeys:
  - the Guide catalog and Guide tests;
  - coverage and roadmap;
  - `docs/features/b2b-operational-chain.md`.

## Phase 8: Verification

- [ ] T015 Full backend suite and web checks
- [x] T016 Manual check per `quickstart.md` on an isolated stack, in German
  - A receipt of 4 offered "Serve backorders". The assigned order (due 25 Oct) was proposed 3 before the order due 10 Oct (1). Changing the second line to 0 and reviewing again reserved only 3.
  - The warehouse preview showed 2 short now and 10 more from 30 Oct (8 in total), naming the purchase.
  - Serving from the warehouse row with the location chosen proposed the remaining 1. Closing it withdrew the review: 1 executed and 3 withdrawn proposals, none left open.
- [x] T017 Review of the diff; fix findings
  - Serving order and available-to-promise read revised due dates.
  - Supply still to come is capped at what each promise still needs, so a reserved or delivered promise no longer holds back its purchase.
  - The confirmation compares what the review showed (available stock, waiting needs, holds) under the delivery lock and refuses any change.
  - Customers under a delivery hold and promises held in their line's unit are listed apart.
  - The card withdraws superseded, closed and location-changed reviews and offers to review again after a refused confirmation.
  - The isolation test sends foreign items, locations, promises and purchases inside the company's own request.
