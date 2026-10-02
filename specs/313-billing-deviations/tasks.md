# Tasks: Over-Billing and Quantity Lowered Below Delivered

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Setup

- [x] T001 Clarify the spec (decisions delegated to the recommended options, 2026-10-02)
- [x] T002 Plan
- [x] T003 Tasks

## Phase 2: Shipped beyond the order (FR-002)

- [x] T004 Tests:
  - lowered below shipped is reported;
  - it clears by a return and by a revision up;
  - a cancelled rest is not reported;
  - nothing beyond is the control;
  - isolation.
- [x] T005 Derivation, catalog entries, pinned lists, translations

## Phase 3: Stories and Guide (FR-001, FR-004)

- [x] T006 Business stories A05 and E07
- [x] T007 Promote A05 and E07: Guide catalog, routing check, coverage, roadmap, matrix, docs

## Phase 4: Verification

- [ ] T008 Full backend suite and web checks
- [ ] T009 Review of the diff; fix findings
