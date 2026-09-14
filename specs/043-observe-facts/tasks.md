# Tasks: Controlled Fact Observation

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner scope approval and close clarification markers in `specs/043-observe-facts/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/043-observe-facts/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings across `specs/043-observe-facts/`

## Phase 2: Failing Proof

- [x] T004 [US1] [FR-001] [FR-002] [FR-003] [FR-004] Add strict observation, vocabulary, subject, and source tests in `packages/reality-core/tests/test_fact_observation.py`
- [x] T005 [US1] [FR-005] [FR-006] [FR-007] Add retry, conflict, concurrency, and atomic-event tests in `packages/reality-core/tests/test_fact_observation.py`
- [x] T006 [US1] [FR-010] [DR-001] [DR-002] [DR-003] Add cross-tenant, rollback, shortest-link, and typed-state-isolation assertions in `packages/reality-core/tests/test_fact_observation.py`
- [x] T007 [P] [US2] [FR-008] [FR-009] [FR-010] [DR-004] Add proposal/confirmation and MCP schema tests in `packages/reality-core/tests/test_mcp_fact_observation.py`
- [x] T008 [P] [US3] [FR-011] [FR-012] [FR-013] [DR-005] Extend catalog, Inspector, and non-mirroring tests in `packages/reality-core/tests/test_application_catalog.py` and `packages/reality-core/tests/test_master_data_api.py`

## Phase 3: User Story 1 — Canonical observation (P1)

- [x] T009 [US1] [FR-005] [FR-006] Add Fact retry identity and tenant uniqueness to `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0032_fact_observation_identity.py`
- [x] T010 [US1] [FR-003] [DR-005] Add the first bounded vocabulary entry and validation contract in `packages/reality-core/config/fact_catalog.yaml` and `packages/reality-core/src/reality/catalogs.py`
- [x] T011 [US1] [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-006] [FR-007] [FR-010] Implement strict atomic `observe_fact` behavior in `packages/reality-core/src/reality/services/core.py`
- [x] T012 [US1] [FR-011] Update machine-readable Fact storage documentation in `packages/reality-core/config/data_model.yaml`
- [x] T013 [US1] Run focused service and migration tests and record acceptance evidence in `specs/043-observe-facts/quickstart.md`

## Phase 4: User Story 2 — Agent proposal (P1)

- [x] T014 [US2] [FR-008] [FR-009] [DR-004] Register the canonical mutation in `packages/reality-core/src/reality/tools/application.py`
- [x] T015 [US2] [FR-008] [FR-009] [FR-010] Expose the strict proposal schema in `packages/reality-core/src/reality/mcp/catalog.py`
- [x] T016 [US2] [FR-012] Declare the shared command contract in `packages/reality-core/config/command_catalog.yaml`
- [x] T017 [US2] Run focused MCP/proposal tests and record acceptance evidence in `specs/043-observe-facts/quickstart.md`

## Phase 5: User Story 3 — Durable boundary guidance (P2)

- [x] T018 [P] [US3] [FR-011] [FR-013] [DR-001] [DR-002] [DR-003] Document Fact versus typed Reality versus BusinessEvent in `docs/DATA_MODEL.md`
- [x] T019 [P] [US3] [FR-008] [FR-012] [DR-004] [DR-005] Document agent observation proposals in `docs/features/chat.md`
- [x] T020 [US3] [FR-011] [FR-012] Verify the Facts register, Inspector, and composed application reference through existing read paths
- [x] T021 [US3] [FR-013] [FR-014] Publish linked Fact decision guidance and a complete agent example in `apps/docs/content/concepts/facts.md`, related concept pages, and `apps/docs/.vitepress/config.mts`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check` and verify all FR/DR coverage in `specs/043-observe-facts/`
- [x] T901 Run `make lint` and `make test`
- [x] T902 Run `make web-build` and `cd apps/web && npm run i18n:audit`
- [x] T903 Test migration upgrade/downgrade and review rollback in `packages/reality-core/migrations/versions/0032_fact_observation_identity.py`
- [x] T904 Review the final diff against `.specify/memory/constitution.md` and `specs/043-observe-facts/spec.md`
- [x] T905 Mark acceptance evidence and all completed tasks only after every required check is green
- [x] T906 Run the public Docs content contract, format check, and production build for `apps/docs/`

## Dependencies

- US1 is foundational for US2 and independently testable through the service.
- US2 depends on US1 and is independently testable through proposal plus confirmation.
- US3 documentation can begin after the contracts are stable; final catalog/read verification depends on US1 and US2.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-004 | T004, T006 | T010–T012 | Complete |
| FR-005–FR-007 | T005 | T009, T011 | Complete |
| FR-008–FR-010 | T006, T007 | T014–T017 | Complete |
| FR-011–FR-014 | T008, T021 | T012, T016, T018–T021 | Complete |
| DR-001–DR-003 | T006, T008 | T011, T012, T018 | Complete |
| DR-004–DR-005 | T007, T008 | T010, T014, T015, T019 | Complete |

## Implementation Strategy

The MVP is US1: a strict source-supported, tenant-safe, idempotent observation service. US2 exposes only that service through the existing confirmation boundary. US3 prevents semantic drift with durable and executable guidance. Tests precede each implementation phase.
