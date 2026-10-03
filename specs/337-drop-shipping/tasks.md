# Tasks: Drop Shipping

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Setup

- [x] T001 Clarify the spec (decisions delegated to the recommended options, 2026-10-03)
- [x] T002 Plan
- [x] T003 Tasks

## Phase 2: Drop shipment (FR-001, FR-002)

- [x] T004 Tests in `tests/test_drop_shipping.py`:
  - the supplier ships straight to the customer, stock unchanged;
  - only what is assigned and open; time and quantity refusals;
  - nothing on hand and nothing reported;
  - only a purchase order shipping to the customer; several customer lines;
  - drop-ship supply is not incoming stock, with an ordinary purchase as the control;
  - the agent's strict schema, review and verification;
  - isolation.
- [x] T005 `_append_movement` private `_drop_ship` flag
- [x] T006 `services/drop_shipping.py`: preview, record, read, `ships_to_customer`, `drop_ship_cover`
- [x] T007 Incoming stock, reorder point and at-risk leave drop-ship supply out

## Phase 3: Adapters (FR-004)

- [x] T008 Review, tools, MCP, CLI and web form
- [x] T009 Catalogs, refusals and translations

## Phase 4: Journeys (FR-003, FR-005)

- [x] T010 Stories D10, D11, G15 and R03 in `tests/scenarios/test_catalog_drop_shipping.py`
- [x] T011 Promote D10, D11 and G15; R03 partial; coverage, roadmap, matrix; `make docs-generate`

## Phase 5: Verify

- [ ] T012 Full backend suite, web checks and CI
