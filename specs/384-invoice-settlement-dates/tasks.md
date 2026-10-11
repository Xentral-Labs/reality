---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Invoice Settlement Dates in One Read

**Input**: `spec.md` and `plan.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

Paths are relative to the repository root; `core/` abbreviates `packages/reality-core/`.

## Phase 1: Gates

- [X] T001 Try `graph_ask` once against a paid invoice and record the result in `plan.md` Research
- [X] T002 Confirm every Constitution Check row is PASS and no schema change, in `plan.md`

## Phase 2: User Story 1 — A paid invoice explains its own settlement (P1)

### Tests

- [X] T003 [US1] [FR-001] [FR-002] [FR-004] Add a failing service test for due date, open amount and
  two dated allocations in `core/tests/finance/test_settlement_flows.py`
- [X] T004 [US1] [FR-003] In the same test, reverse one payment and assert the allocation disappears
  while the other remains and allocations plus open equal gross
- [X] T005 [US1] [FR-005] Assert the MCP `finance_settlement_context` handler returns the same answer
- [X] T006 [US1] [FR-001] Add a test that an unsettled invoice without a term is due on its document
  date and has no allocations
- [X] T007 Observe T003–T006 failing before the change

### Implementation

- [X] T008 [US1] [FR-001] [FR-002] [FR-003] [FR-004] Extend the invoice branch of `settlement_context`
  in `core/src/reality/services/finance/settlement_flows.py`
- [X] T009 [US1] Update `finance_settlement_context` purpose and proof text in
  `core/config/command_catalog.yaml`; run `make docs-generate`
- [X] T010 Add a spec 384 section to `docs/SPEC_COVERAGE_MATRIX.md`

## Phase 3: Verification

- [X] T011 Run the finance settlement test files, `ruff check`/`ruff format --check`,
  `make spec-check` and `make docs-catalog-check`; record results in `checklists/requirements.md`

## Requirement Coverage

| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T003, T006 | T008 |
| FR-002 | T003 | T008 |
| FR-003 | T004 | T008 |
| FR-004 | T003 | T008 |
| FR-005 | T005 | T008, T009 |
