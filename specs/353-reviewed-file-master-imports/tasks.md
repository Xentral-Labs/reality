# Tasks: Reviewed file, master-data and stock imports

**Input**: spec.md, plan.md, research.md, data-model.md and contracts/intake.md.
**Status**: Implementation tasks are intentionally unchecked; design verification
does not prove runtime behavior. Domain → services → tools → adapters.

## Phase 1: Setup and existing contract inventory

- [ ] T001 Re-read dependencies and resolve exact existing regression files in `packages/reality-core/tests/`; confirm planned writer/caller coverage against `specs/351-decision-gated-intake/writer-coverage.md`.
- [ ] T002 Establish isolated PostgreSQL fixtures and the DR-001/DR-002/DR-003 negative matrix in `packages/reality-core/tests/test_file_intake_admission.py`: lossless values, causal links, derived-state and tenant refusal.

## Phase 2: US1 — Review file meaning and master records

**Independent acceptance**: Execute US1 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T003 [US1] Add and observe failing proofs for FR-001, FR-002, FR-003, FR-004 in `packages/reality-core/tests/test_file_intake_admission.py`: `test_original_artifact_precedes_approval`, `test_master_preparation_has_no_effects`, `test_master_conflicts_refuse_atomically`, `test_master_receipt_replays_exactly`.
- [ ] T004 [US1] Extend staging/parser into lossless source registration and side-effect-free profile plans in `packages/reality-core/src/reality/services/item_imports.py`; deliver FR-001, FR-002, FR-003, FR-004 without weakening their refusal checks.
- [ ] T005 [US1] Replace mutating master branches with shared prepared-profile adapters in `packages/reality-core/src/reality/services/file_interpreters.py`; deliver FR-001, FR-002, FR-003, FR-004 without weakening their refusal checks.

## Phase 3: US2 — Import a large file with explicit packages

**Independent acceptance**: Execute US2 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T006 [US2] Add and observe failing proofs for FR-005, FR-006, FR-007 in `packages/reality-core/tests/test_file_intake_admission.py`: `test_large_file_is_partitioned_before_legacy_limit`, `test_full_file_validation_covers_package_boundaries`, `test_mapping_change_and_resume_are_safe`.
- [ ] T007 [US2] Add UTF-8/multiline/exact-byte-limit, oversized-unit and more-than-ten-package tests for FR-005/FR-006 in `packages/reality-core/tests/test_file_intake_admission.py`; implement deterministic dual-limit packaging in `packages/reality-core/src/reality/services/file_intake.py`.
- [ ] T008 [US2] Add bounded full-input validation and stable package manifests without increasing the legacy one-package limit in `packages/reality-core/src/reality/services/file_intake.py`; deliver FR-005, FR-006, FR-007 without weakening their refusal checks.
- [ ] T009 [US2] Connect existing CSV panel to shared package/batch preparation and results in `apps/web/src/unified/ItemImportPanel.tsx`; deliver FR-005, FR-006, FR-007 without weakening their refusal checks.

## Phase 4: US3 — Review orders and stock effects from files

**Independent acceptance**: Execute US3 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T010 [US3] Add and observe failing proofs for FR-008, FR-009, FR-010 in `packages/reality-core/tests/test_file_intake_admission.py`: `test_file_order_is_one_atomic_unit`, `test_snapshot_does_not_adjust_before_approval`, `test_external_statement_is_not_book_stock`.
- [ ] T011 [US3] Split sales-order and inventory profile plans from no-commit application in `packages/reality-core/src/reality/services/file_interpreters.py`; deliver FR-008, FR-009, FR-010 without weakening their refusal checks.
- [ ] T012 [US3] Integrate external stock and route bank profiles through the shared financial adapter in `packages/reality-core/src/reality/services/external_stock.py`; deliver FR-008, FR-009, FR-010 without weakening their refusal checks.

## Final phase: Integration and verification

- [ ] T013 Add concurrent approval, crash-before/after-commit, cross-tenant and scope-reuse integration proof for DR-001–DR-003/SC-001 in `packages/reality-core/tests/test_file_intake_admission.py` and execute the story tests against real PostgreSQL.
- [ ] T014 Update exact source/decision explanation and applicable contracts in `specs/129-unified-item-csv-import/spec.md` plus the other paths listed in plan.md; include DR-001–DR-003 and register new test families in `docs/SPEC_COVERAGE_MATRIX.md`.
- [ ] T015 Run required gates from `quickstart.md`, review the actual diff and migration/rollback evidence, and record measured results in this feature's `verification.md` before marking any story complete (SC-002).

## Dependencies and execution order

T001 → T002 → each story's failing proof → its domain/service implementation →
tool/adapter integration → final integration tests → contract/catalog updates →
required gates. All stories depend on setup; later stories use the shared unit
contract proven by US1. Feature dependencies are listed in spec.md.

## Parallel opportunities

Independent test-fixture and browser-presentation work can be prepared separately
after the interface contract is fixed. Changes to shared executor, core services,
catalogs and generated outputs remain sequential to avoid conflicting assumptions.
No tasks are labelled parallel when they modify the same file.

## Incremental implementation

Deliver one independently tested story at a time. The first foundation/Shopify slice
proves the mechanism, not all-path coverage. Do not deploy a migrated adapter while
old write-capable workers can still bypass its boundary. Completion remains gated
by all required checks and honest unresolved-outcome reporting.

