# Tasks: Customer Pickup and Late 3PL Confirmations

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Setup

- [x] T001 Clarify the spec (decisions delegated to the recommended options, 2026-10-02)
- [x] T002 Plan
- [x] T003 Tasks

## Phase 2: Pickup and stated time (FR-001, FR-002)

- [ ] T004 Tests:
  - a pickup with its collector;
  - carrier refused on a pickup;
  - pickup for customer deliveries only;
  - movements carry the stated time;
  - a future time refused;
  - the lag in the read;
  - the migration guard.
- [ ] T005 Migration `0123`, model, service, reads, refusals with translations

## Phase 3: Adapters and Web (FR-003)

- [ ] T006 Tool fields, MCP schemas, Web dispatch card and detail, adapter tests, catalog gates

## Phase 4: Stories and Guide (FR-004)

- [ ] T007 Business stories D15 and D12
- [ ] T008 Promote them: Guide catalog, routing check, coverage, roadmap, matrix, docs

## Phase 5: Verification

- [ ] T009 Full backend suite and web checks
- [ ] T010 Review of the diff; fix findings
