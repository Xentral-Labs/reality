---
description: "Requirement-traceable canonical catalog implementation tasks"
---

# Tasks: Canonical Core Catalogs

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`  
**Gate**: Constitution Check passed and no unresolved clarification marker

## Phase 1: Specification and Design Gates

- [x] T001 Confirm reviewed scope and completed built-in quality checks in `specs/007-core-catalogs/spec.md` and `specs/007-core-catalogs/checklists/requirements.md`
- [x] T002 Confirm all Constitution Check rows remain PASS in `specs/007-core-catalogs/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings across `specs/007-core-catalogs/spec.md`, `plan.md`, and `tasks.md`

## Phase 2: Foundational Failing Proof

- [x] T004 [P] [US1] [FR-001,FR-002,FR-003,FR-004,FR-005,FR-006,FR-014] Add failing split-resource, composition, category-contract, count, and migration-preservation tests in `backend/tests/test_application_catalog.py`
- [x] T005 [P] [US2] [FR-007,FR-008,FR-009,FR-010,FR-011] Add failing duplicate, invalid-reference, Event completeness, Projection completeness, public-Command, and offline-validation tests in `backend/tests/test_application_catalog.py`
- [x] T006 [P] [US3] [FR-012,DR-003] Add failing authenticated and unauthenticated application-reference API tests in `backend/tests/test_web_api.py`

## Phase 3: User Story 1 — Complete Vocabulary (P1)

- [x] T007 [US1] [FR-001,FR-003,FR-014] Move parameter descriptions and Commands losslessly into `backend/config/command_catalog.yaml`
- [x] T008 [P] [US1] [FR-004,FR-014] Move Events and add known omissions in `backend/config/business_event_catalog.yaml`
- [x] T009 [P] [US1] [FR-005,FR-014] Move Projections losslessly into `backend/config/projection_catalog.yaml`
- [x] T010 [P] [US1] [FR-006] Create the explicit stable predicate vocabulary in `backend/config/fact_catalog.yaml`
- [x] T011 [US1] [FR-001,FR-002,FR-003,FR-004,FR-005,FR-006,FR-010,DR-001,DR-002,DR-004,DR-005] Implement composed loading, signature enrichment, and public-Command semantics in `backend/src/reality/catalogs.py` and preserve imports through `backend/src/reality/web/application_catalog.py`

## Phase 4: User Story 2 — Drift Gate (P1)

- [x] T012 [US2] [FR-007,FR-008,FR-009,FR-010,FR-011] Implement structural, table/service/input, AST Event, Projection registry, and offline validation in `backend/src/reality/catalogs.py` and `backend/src/reality/web/data_model.py`
- [x] T013 [US2] [FR-011,FR-013,DR-001,DR-002,DR-004,DR-005] Document authoritative versus derived behavior and contributor catalog workflow in `docs/ARCHITECTURE.md` and `docs/features/operational_fields.md`
- [x] T014 [US2] [FR-007,FR-008,FR-009,FR-010,FR-011] Run focused catalog tests and record the verified commands/results in `specs/007-core-catalogs/quickstart.md`

## Phase 5: User Story 3 — Generated Product Reference (P2)

- [x] T015 [US3] [FR-002,FR-012,DR-003] Expose the composed read-only reference via the existing membership boundary in `backend/src/reality/web/api.py`
- [x] T016 [US3] [FR-012,DR-003] Add typed application-reference retrieval in `frontend/src/api.ts`
- [x] T017 [US3] [FR-012,DR-003] Replace the hard-coded Processing Projection list with catalog data and bounded loading/error states in `frontend/src/App.tsx`
- [x] T018 [US3] [FR-012,FR-013,DR-003] Align the durable reference contract in `docs/WEB_SPEC.md` and `docs/features/web.md`

## Final Phase: Cross-Cutting Review

- [x] T019 [FR-001,FR-002,FR-003,FR-004,FR-005,FR-006,FR-007,FR-008,FR-009,FR-010,FR-011,FR-012,FR-013,FR-014,DR-001,DR-002,DR-003,DR-004,DR-005] Run spec-policy and requirement-traceability audit using `scripts/check_spec_policy.py`
- [x] T020 Run Ruff and the complete backend PostgreSQL suite using `Makefile` targets
- [x] T021 [FR-012,DR-003] Run frontend build and i18n audit using `frontend/package.json` scripts
- [x] T022 [DR-005] Confirm no Alembic migration or schema change and review file-only rollback in `specs/007-core-catalogs/plan.md`
- [x] T023 Review final diff against the Constitution, mark completed tasks here, and update `specs/007-core-catalogs/quickstart.md` only with green evidence

## Dependencies

- T001–T003 gate all implementation.
- T004–T006 provide failing proof before T007–T018.
- T007–T010 may proceed in parallel; T011 depends on all four.
- T012 depends on T011; T013 and T014 depend on T012.
- T015 depends on T011–T012; T016 depends on T015; T017 depends on T016.
- T019–T023 require all story phases.

## Independent Story Evidence

- **US1**: Load one composition with four categories, exact counts, enriched Commands,
  all literal Events, all registered Projections, and an explicit Fact vocabulary.
- **US2**: Isolated missing/stale/duplicate/reference fixtures fail offline with exact
  category messages; valid catalogs and the data model pass without database access.
- **US3**: Authenticated tenant member retrieves reference; unauthenticated access is
  denied; Processing renders canonical Projection metadata without a local name list.

## Requirement Coverage

| Requirement group | Test task(s) | Implementation/documentation task(s) |
|---|---|---|
| FR-001–FR-006, FR-010, FR-014 | T004–T005 | T007–T012 |
| FR-007–FR-009, FR-011 | T005 | T012–T014 |
| FR-012 | T006, T021 | T015–T018 |
| FR-013 | T019 | T013, T018 |
| DR-001, DR-002, DR-004, DR-005 | T005, T019, T022 | T011–T013 |
| DR-003 | T006, T021 | T015–T018 |

## Implementation Strategy

The MVP is US1 plus US2: trustworthy split catalogs and executable drift gates. US3
then connects the already validated reference to the product without changing business
behavior or persistence.
