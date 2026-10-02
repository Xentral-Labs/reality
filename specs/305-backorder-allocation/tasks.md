# Tasks: Serving Backorders on Receipt

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/backorders.md](contracts/backorders.md)

Tests come first in each phase where practical.

## Phase 1: Setup

- [x] T001 Clarify the spec with the owner (Clarifications 2026-10-02)
- [x] T002 Plan, research, data model, contract, quickstart
- [x] T003 Tasks

## Phase 2: Split of assigned supply (FR-006)

- [ ] T004 Tests: a receipt of 4 against 3 + 3 + 3 shows 3/0, 1/2, 0/3; a cancelled or reversed assignment drops out of the order; without receipts everything is still to come
- [ ] T005 `assignment_split` and the `arrived` / `still_to_come` fields in `supply_coverage`

## Phase 3: Serving backorders (FR-001, FR-004)

- [ ] T006 Tests:
  - serving order (assigned first, then due date, then promised);
  - stated lines and their refusals;
  - held promises listed apart;
  - tracked items refused;
  - stale confirmation refused;
  - blocked stock not served;
  - positive controls.
- [ ] T007 `services/backorders.py` (`waiting_promises`, `review_backorder_serving`, `serve_backorders`), the tool, the proposal review, and the refusals with translations

## Phase 4: Available-to-promise (FR-003)

- [ ] T008 Tests:
  - free now with and without waiting need;
  - purchases by date with their assignments;
  - overdue purchase;
  - a cancelled promise leaves the answer.
- [ ] T009 `available_to_promise` and its read tool

## Phase 5: Adapters and gates

- [ ] T010 MCP, Web and CLI, with adapter tests and tenant isolation
- [ ] T011 Catalog gates:
  - command and action catalogs, tool topics;
  - isolation catalog and counts;
  - resource catalog and labels;
  - coverage matrix and docs generation.

## Phase 6: Web

- [ ] T012 The serving card, "Serve backorders" after a receipt and on the warehouse row, available-to-promise in the row preview, translations, and browser fixtures

## Phase 7: Stories and Guide (FR-002, FR-005)

- [ ] T013 Business stories for B07, B08, B09 (rewrite the pinned test), G13, H16 and R02
- [ ] T014 Promote the journeys:
  - the Guide catalog and Guide tests;
  - coverage and roadmap;
  - `docs/features/b2b-operational-chain.md`.

## Phase 8: Verification

- [ ] T015 Full backend suite and web checks
- [ ] T016 Manual check per `quickstart.md`
- [ ] T017 Review of the diff; fix findings
