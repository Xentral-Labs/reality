---
description: "Requirement-traceable deployable application layout tasks"
---

# Tasks: Deployable Application Layout

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and
`quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede the implementation they prove.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner approval, stable names, and closed clarification markers in `specs/021-deployable-app-layout/spec.md` and `specs/021-deployable-app-layout/checklists/requirements.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/021-deployable-app-layout/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve every CRITICAL or HIGH finding across `spec.md`, `plan.md`, and `tasks.md`

## Phase 2: Failing Repository Contract Proof

- [x] T004 [P] [US1] [FR-001] [FR-002] Add failing stable tree and retired-root assertions in `packages/reality-core/tests/test_repository_layout.py`
- [x] T005 [P] [US1] [FR-003] [FR-004] Add failing API/MCP Dockerfile ownership and same-core build-input assertions in `packages/reality-core/tests/test_repository_layout.py`
- [x] T006 [P] [US1] [FR-008] Add failing active command, CI, policy, and current-document stale-path scan in `packages/reality-core/tests/test_repository_layout.py`
- [x] T007 [P] [US2] [FR-006] Add failing Compose service-to-application mapping, command, port, probe, and pool assertions in `packages/reality-core/tests/test_repository_layout.py`
- [x] T008 [P] [US3] [FR-007] [FR-012] Add failing Make, README, install, migration, test, and web-app command assertions in `packages/reality-core/tests/test_repository_layout.py`

**Checkpoint**: Proof fails only because the old layout still exists and current paths
have not moved.

## Phase 3: User Story 1 — Identify Deployable Units (P1)

**Goal**: The root tree makes Web, API, MCP, and the shared core immediately obvious.

**Independent Test**: Map every deployable application directory and verify API/MCP
consume one core without copied business modules.

- [x] T009 [US1] [FR-002] Move the complete Python workspace from `backend/` to `packages/reality-core/` without changing `reality.*` imports or migration contents
- [x] T010 [P] [US1] [FR-001] [FR-005] Move the complete browser product from `frontend/` to `apps/web/` without changing UI behavior
- [x] T011 [P] [US1] [FR-003] Create the explicit API image definition in `apps/api/Dockerfile`
- [x] T012 [P] [US1] [FR-003] Create the explicit MCP image definition in `apps/mcp/Dockerfile`
- [x] T013 [US1] [FR-004] Remove the obsolete shared `packages/reality-core/Dockerfile` and prove neither app directory contains copied `reality` modules
- [x] T014 [US1] [FR-001] [FR-002] Update root and application Docker ignore ownership in `.dockerignore`, `packages/reality-core/.dockerignore`, and `apps/web/.dockerignore`
- [x] T015 [US1] [FR-008] Update Spec Policy roots, catalog path, and discovered test paths in `scripts/check_spec_policy.py`
- [x] T016 [US1] [FR-008] [DR-004] Update executable coverage ownership paths in `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T017 [US1] [FR-001] Run `packages/reality-core/tests/test_repository_layout.py` tree/image/policy cases and record the result in `specs/021-deployable-app-layout/quickstart.md`

## Phase 4: User Story 2 — Build and Operate Independently (P1)

**Goal**: API, MCP, and Web are real independently buildable and diagnosable units.

**Independent Test**: Build all images, run the stack, stop MCP while API remains
healthy, then verify MCP recovery.

- [x] T018 [US2] [FR-006] Update migration, API, MCP, and Web build definitions and dependencies in `compose.yml`
- [x] T019 [US2] [FR-003] [FR-004] Ensure `apps/api/Dockerfile` installs `packages/reality-core` and owns only the Web/API command and port
- [x] T020 [US2] [FR-003] [FR-004] Ensure `apps/mcp/Dockerfile` installs `packages/reality-core` and owns only the MCP command and port
- [x] T021 [US2] [FR-005] Update Web build inputs and nginx ownership in `apps/web/Dockerfile` and `apps/web/nginx.conf`
- [x] T022 [US2] [FR-006] Preserve API/MCP health, readiness, dependencies, URLs, and separate database pools in `compose.yml`
- [x] T023 [US2] [FR-007] Update Python/frontend dependency caching, changed-file lint globs, install paths, and test working directories in `.github/workflows/quality.yml`
- [x] T024 [US2] [FR-009] [DR-002] Run focused API, MCP, CLI, Copilot, proposal, and adapter-equivalence tests from `packages/reality-core/tests/`
- [x] T025 [US2] [FR-010] Run the unchanged Alembic migration construction/backfill suite from `packages/reality-core/tests/test_migrations.py`
- [x] T026 [US2] [FR-003] [FR-006] Build API, MCP, and Web images independently and validate `docker compose config`
- [x] T027 [US2] [FR-006] Run the live stop/restart isolation story and record results in `specs/021-deployable-app-layout/quickstart.md`

## Phase 5: User Story 3 — Coherent Developer Workflow (P2)

**Goal**: Clean-checkout install, tests, migrations, builds, and documentation use one
coherent current layout.

**Independent Test**: Follow README and Make commands from installation through all
quality gates with no retired-path dependency.

- [x] T028 [US3] [FR-007] Update install, test, lint, status, and Web build targets in `Makefile`
- [x] T029 [US3] [FR-007] Update root build-context exclusions in `.dockerignore` without excluding shared package inputs required by API/MCP images
- [x] T030 [US3] [FR-012] Rewrite repository layout, local development, storage, and deployment commands in `README.md`
- [x] T031 [P] [US3] [FR-008] [FR-011] Update current architecture paths and atomic rollback guidance in `docs/ARCHITECTURE.md` and `docs/decisions/0005-frontend-backend-object-storage.md`
- [x] T032 [P] [US3] [FR-008] Update current Web, CLI, catalog, and spec-driven workflow paths in `docs/WEB_SPEC.md`, `docs/CLI_SPEC.md`, and `docs/SPEC_DRIVEN_WORKFLOW.md`
- [x] T033 [P] [US3] [FR-008] Update current feature documentation paths in `docs/features/web.md` and `docs/features/operational_fields.md`
- [x] T034 [US3] [FR-011] Document atomic release and rollback behavior in `specs/021-deployable-app-layout/contracts/path-migration.md` and `README.md`
- [x] T035 [US3] [FR-009] [DR-001] [DR-002] [DR-003] Run the full shared-core PostgreSQL suite from `packages/reality-core/`
- [x] T036 [US3] [FR-005] Run Web localization tests, audit, and production build from `apps/web/`
- [x] T037 [US3] [FR-007] [FR-012] Follow the documented clean-checkout command sequence and record evidence in `specs/021-deployable-app-layout/quickstart.md`

## Final Phase: Cross-Cutting Review

- [x] T038 [P] [FR-001] [FR-008] Run repository stale-path scan and verify only explicitly historical references remain
- [x] T039 [P] [FR-007] Run Ruff from the shared-core workspace using the exact CI command and Spec Policy through `scripts/check_spec_policy.py`
- [x] T040 [P] [FR-003] [FR-004] Inspect built API/MCP images to prove same shared package release and distinct commands
- [x] T041 [FR-010] Confirm no Alembic revision content or database schema change exists against `specs/021-deployable-app-layout/data-model.md`
- [x] T042 [FR-009] [DR-001] [DR-002] [DR-003] Reconcile complete regression results with the feature specification and Constitution
- [x] T043 [FR-011] Review rollback from new to prior repository release without mixed-layout support
- [x] T044 Review final diff against every FR/DR row and mark `specs/021-deployable-app-layout/tasks.md` complete only after all gates are green

## Dependencies

```text
Specification/design gates
  -> failing repository contract proof
  -> US1 stable ownership tree
       -> US2 independent builds/operations
       -> US3 developer workflow and documentation
  -> cross-cutting verification
```

- US1 establishes the paths required by US2 and US3.
- US2 and US3 may proceed in parallel after the atomic moves and policy root update.
- Final verification requires all applications and the shared core to be on the new
  layout; compatibility symlinks are not permitted.

## Parallel Opportunities

- T004–T008 are independent assertions in one new test file but should be authored
  together before the move.
- T010–T012 touch independent application paths after T009 establishes the package root.
- T031–T033 update separate documentation families after commands are stable.
- T038–T040 are independent final policy, lint, and image inspections.

## Implementation Strategy

The smallest coherent increment is US1: one visible application tree and one shared
package. It is not releasable alone because current commands move atomically; US2 must
complete in the same PR. US3 closes the professional developer and documentation
contract before merge.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-002 | T004, T017, T038 | T009–T010, T014–T016 | Complete |
| FR-003–FR-004 | T005, T026, T040 | T011–T013, T019–T020 | Complete |
| FR-005–FR-006 | T007, T026–T027, T036 | T010, T018, T021–T022 | Complete |
| FR-007–FR-008 | T006, T008, T037–T039 | T015–T016, T023, T028–T033 | Complete |
| FR-009–FR-010 | T024–T025, T035, T041–T042 | T018–T23 | Complete |
| FR-011–FR-012 | T008, T037, T043 | T030–T034 | Complete |
| DR-001–DR-004 | T024, T035, T038, T042 | T009–T16, T031–T34 | Complete |
