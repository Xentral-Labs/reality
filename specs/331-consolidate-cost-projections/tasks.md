# Tasks: Consolidate cost projections

**Language**: English
**Input**: Approved spec, plan, research, data model and compatibility contract.

## Phase 1: Design gates

- [x] T001 Record accepted scope in `specs/331-consolidate-cost-projections/spec.md`.
- [x] T002 Resolve research and pass Constitution gate in `specs/331-consolidate-cost-projections/plan.md`.
- [x] T003 Analyze requirement coverage and design consistency in `specs/331-consolidate-cost-projections/tasks.md`.

## Phase 2: Failing proof

- [x] T004 [US1] [FR-001, FR-002, FR-005, FR-008, DR-001, DR-002, DR-004, DR-005] Add physical inventory, view-write and result/inspection parity tests in `packages/reality-core/tests/test_cost_projections.py`; run red and reuse exact-value/read-only suites.
- [x] T005 [US3] [FR-006, DR-003] Add populated four-family upgrade/downgrade, duplicate-ID, wrong-family/tenant rejection and exact-copy tests in `packages/reality-core/tests/test_cost_projection_migration.py`.
- [x] T006 [US2] [FR-003, FR-004, FR-007] Plan and run existing publication, interruption, concurrency and disposal regression tests in `packages/reality-core/tests/test_captured_report.py` and `packages/reality-core/tests/test_company_generation_jobs.py`, adding shared-storage guard proofs to `packages/reality-core/tests/test_cost_projections.py`.

## Phase 3: Exact results (US1)

- [x] T007 [US1] [FR-001, FR-002, FR-005, FR-008, DR-001, DR-002, DR-003, DR-004, DR-005] Implement shared typed storage and logical writable views in `packages/reality-core/src/reality/db/cost_projections.py`, register in `packages/reality-core/src/reality/db/core.py` and preserve existing mapped fields.
- [x] T008 [US1] [FR-005, DR-004] Verify existing service, SQL analytics and inspector contracts via `packages/reality-core/tests/test_cost_records.py`, `packages/reality-core/tests/test_inventory_costing_relation.py`, `packages/reality-core/tests/test_company_generation_graph.py` and `packages/reality-core/tests/test_captured_report_graph.py`.

## Phase 4: Publication (US2)

- [x] T009 [US2] [FR-003, FR-004, FR-007, DR-003] Install shared physical storage lifecycle and identity guards in `packages/reality-core/src/reality/db/cost_projection_guards.sql`; retain company input guards.
- [x] T010 [US2] [FR-003, FR-004, FR-007] Run existing generation/publication/concurrency/disposal suites and record results in `specs/331-consolidate-cost-projections/verification.md`.

## Phase 5: Safe migration (US3)

- [x] T011 [US3] [FR-006, FR-008, DR-001, DR-003] Implement static transactional copy, parity, retirement, views and rollback in `packages/reality-core/migrations/versions/0117_cost_projections.py`; exclude logical views in `packages/reality-core/migrations/env.py`.
- [x] T012 [US3] [FR-005, FR-008] Update physical-schema comparisons in `packages/reality-core/tests/test_migrations.py` and `packages/reality-core/tests/test_captured_report.py`, and classify shared storage in `packages/reality-core/tests/test_reporting_graph_coverage.py` without widening business coverage; classify new storage as later revisions in `packages/reality-core/tests/test_schema_indexes.py`.
- [x] T013 [US3] [FR-006, FR-008] Run populated migration tests and exact identity/SQL parity in `packages/reality-core/tests/test_cost_projection_migration.py`.

## Final phase

- [x] T014 [FR-001, FR-002, FR-005, FR-008, DR-001, DR-002, DR-004, DR-005] Update durable storage/authority contracts in `docs/DATA_MODEL.md` and `docs/features/receipt-costing.md`; preserve catalog vocabulary and generate documentation if needed.
- [x] T015 Run spec policy, Ruff and complete backend suite; record evidence in `specs/331-consolidate-cost-projections/verification.md`.
- [x] T016 Run web, i18n and docs/catalog build gates and review final migration/Constitution diff in `specs/331-consolidate-cost-projections/verification.md`.

T015 is closed by the subsequent complete backend coverage of the frozen specs
316/319 source scope. Earlier red runs remain documented in [verification.md](verification.md);
see spec 319 verification for the final dedicated-server run and passing serial gates.

## Dependencies and execution

T001–T003 gate all implementation. T004–T006 precede T007. T007 precedes T009
and migration DDL snapshot T011; migration/guard integration is sequential.
US1 tests independently prove view parity; US2 proves atomicity; US3 proves populated
migration and schema retirement. Existing focused suites may run in parallel once schema
installation is complete; no concurrent edits to shared model files are planned.

## Requirement coverage

| Requirements | Test tasks | Implementation/documentation tasks |
|---|---|---|
| FR-001/002/005/008 | T004, T008, T012, T013 | T007, T011, T012, T014 |
| FR-003/004/007 | T006, T010 | T009 |
| FR-006 | T005, T013 | T011 |
| DR-001/002/004/005 | T004, T008 | T007, T014 |
| DR-003 | T005, T006 | T007, T009, T011 |
