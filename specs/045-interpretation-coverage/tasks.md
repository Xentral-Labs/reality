# Tasks: Interpretation Coverage

## Phase 1 — Tests

- [X] T001 [US1] Add failing model/service tests in `packages/reality-core/tests/test_interpretation_coverage.py` for FR-001–FR-005 and DR-001–DR-005.
- [X] T002 [US2] Add failing classification decision-table and retry tests for FR-004–FR-006 and FR-009–FR-010.
- [X] T003 [US3] Add failing tool/MCP parity and tenant-isolation tests for FR-007–FR-009.

## Phase 2 — Domain and persistence

- [X] T004 [US1] Add tenant-scoped outcome/reference models in `db/core.py`.
- [X] T005 [US1] Add reversible migration `0033_interpretation_outcomes.py`.
- [X] T006 [US1] Update tenant-isolation catalog and schema tests.

## Phase 3 — Services

- [X] T007 [US1] Add append/reference services and atomic Shopify success recording.
- [X] T008 [US2] Record safe failure/retry and attempt-zero intake classifications.
- [X] T009 [US3] Add coverage reads with `not_recorded` handling.

## Phase 4 — Tools and adapters

- [X] T010 [US3] Register the read-only application tool.
- [X] T011 [US3] Add MCP schema/discovery and Chat parity.

## Phase 5 — Documentation and verification

- [X] T012 Update data-model, source-ingestion, and docs-site documentation.
- [X] T013 Run targeted and migration tests.
- [X] T014 Run all repository gates and final diff review, preserving unrelated web changes.

All FR-001–FR-010 and DR-001–DR-005 map to T001–T012; executable proof maps to T001–T003 and T013–T014.
