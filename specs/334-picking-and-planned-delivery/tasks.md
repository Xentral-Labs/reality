# Tasks: Picking and Planned Outbound Deliveries

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Setup

- [x] T001 Clarify the spec (decisions delegated to the recommended options, 2026-10-02)
- [x] T002 Plan
- [x] T003 Tasks

## Phase 2: Planned deliveries and picking (FR-001 to FR-004)

- [x] T004 Tests first in `tests/test_outbound_deliveries.py`:
  - plan with recipient, address and slot;
  - quantity bound across deliveries;
  - other customer refused;
  - revision keeps every statement;
  - pick moves stock and reservation to staging;
  - pick beyond planned refused with nothing moved;
  - put-back moves both back;
  - cancellation leaves goods waiting to be put back;
  - tenant isolation.
- [x] T005 Migration `0128_outbound_deliveries`, models and indexes
- [x] T006 Service, reads and refusals with translations

## Phase 3: Dispatch (FR-005)

- [x] T007 Tests:
  - dispatch through a planned delivery records the link, address and slot;
  - mismatching movements refused in review and at confirmation;
  - unpicked delivery refused;
  - a waiting put-back refused;
  - no change without a delivery.
- [x] T008 `shipment_dispatch` field, review and confirmation checks, shipment read

## Phase 4: Adapters and Web (FR-006)

- [x] T009 Application tools, MCP, CLI, Web API, catalog gates, adapter tests
- [x] T010 Web card on the shipments page with pick, put-back and dispatch; translations

## Phase 5: Stories and Guide (FR-007)

- [x] T011 Business stories A08, A11, A21, A24, D04, D13, M05
- [x] T012 Promote them: Guide catalog, coverage, roadmap, matrix, docs generation

## Phase 6: Verification

- [x] T013 Full backend suite and web checks
- [x] T014 Review of the diff; fix findings
