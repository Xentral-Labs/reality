# Tasks: Consolidate Finance Reference Storage

Input: reviewed spec, plan, data model and contracts. Tests precede implementation.

## Phase 1: Specification and Design Gates
- [x] T001 Review approved scope and requirements in `spec.md`.
- [x] T002 Confirm independent research and post-design Constitution PASS in `plan.md`.
- [x] T003 Analyze requirement coverage in `spec.md`, `plan.md`, `tasks.md` before implementation.

## Phase 2: Foundational Failing Proof
- [x] T004 [US1] [FR-001] [FR-003] [FR-005] [FR-007] [FR-008] Add failing storage/view CRUD proof and plan existing service regressions in `packages/reality-core/tests/test_finance_reference_store.py`.

## Phase 3: User Story 1 — Familiar Catalogs
- [x] T005 [US1] [FR-001] [FR-003] [FR-005] [FR-007] [FR-008] Implement typed store and writable view registration in `packages/reality-core/src/reality/db/finance_reference_store.py` and `db/core.py`, preserving existing canonical services.
- [x] T006 [US1] Run lifecycle, permissions, stale/audit and concurrency tests in `tests/finance/test_references.py` and `tests/finance/test_target_mappings.py`; record `verification.md`.

## Phase 4: User Story 2 — Exact Retained Links
- [x] T007 [US2] [FR-002] [FR-004] [FR-006] [FR-010] Add collision, typed-FK, metadata and deletion/count proofs in `packages/reality-core/tests/test_finance_reference_store.py`.
- [x] T008 [US2] [FR-002] [FR-004] [FR-006] [FR-010] Redirect exact FK shapes and metadata dependencies in `packages/reality-core/src/reality/db/finance_reference_store.py`; verify unchanged physical purge/count handling in `services/core.py` and `services/account_deletion.py`; name the store in the existing Finance deferral in `tests/test_reporting_graph_coverage.py`.
- [x] T009 [US2] Run assignment/source/target history tests in `tests/finance/test_components.py`, `test_source_mappings.py`, `test_target_mappings.py`; record `verification.md`.

## Phase 5: User Story 3 — Reversible Reduction
- [x] T010 [US3] [FR-002] [FR-003] [FR-004] [FR-006] [FR-007] [FR-009] [FR-010] Add populated exact-schema roundtrip tests in `packages/reality-core/tests/test_finance_reference_migration.py` before migration implementation.
- [x] T011 [US3] [FR-009] [FR-010] Implement frozen schema migration `packages/reality-core/migrations/versions/0119_finance_references.py`, retaining historical migration compatibility.
- [x] T012 [US3] Run migration/index/deletion and populated rollback proofs; record `verification.md`.

## Final Phase: Verification and Review
- [x] T013 [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-006] [FR-007] [FR-008] [FR-009] [FR-010] Update physical/logical storage documentation in `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/SPEC_COVERAGE_MATRIX.md`, `apps/docs/scripts/data_model_reference.py` (unchanged selection validated; catalogs are not exposed there).
- [x] T014 Run lint, spec-check, generated docs/catalog/build, frontend/i18n and complete backend PostgreSQL suite; record actual results in `verification.md`.
- [x] T015 Review final scoped diff, requirements, migration and rollback; complete task status only after required checks pass in `verification.md`.

## Requirement Coverage
| Requirement | Test tasks | Implementation/documentation tasks |
|---|---|---|
| FR-001 | T004,T006 | T005,T013 |
| FR-002 | T007,T010 | T008,T013 |
| FR-003 | T004,T010 | T005,T013 |
| FR-004 | T007,T010 | T008,T013 |
| FR-005 | T004,T006 | T005,T013 |
| FR-006 | T007,T009,T010 | T008,T013 |
| FR-007 | T004,T010 | T005,T013 |
| FR-008 | T004 | T005,T013 |
| FR-009 | T010,T012 | T011,T013 |
| FR-010 | T007,T010,T012 | T008,T011,T013 |

SC-001/004: T004/T005/T013. SC-002: T010/T011/T012. SC-003: T006/T009/T014.

## Dependencies and Execution
T001→T002→T003→T004→T005→T006; T007→T008→T009; T010→T011→T012; then T013→T014→T015. Shared file edits remain sequential. Existing independent service modules can be tested in parallel; no agent delegation beyond planning/review required by the planning skill. US1 provides familiar catalog behavior; US2 independently proves retained links; US3 proves reversible deployment. No live rollout.
