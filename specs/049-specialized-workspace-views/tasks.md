---
description: "Requirement-traceable specialized workspace View tasks"
---

# Tasks: Specialized Workspace Views

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm product-scope approval and absence of clarification markers in `specs/049-specialized-workspace-views/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/049-specialized-workspace-views/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve every CRITICAL finding across `specs/049-specialized-workspace-views/`

## Phase 2: Failing Proof

- [x] T004 [P] [US1] [FR-001] [FR-002] [FR-003] [FR-011] Add failing specialized classification, shared-projection alias, exclusion, and invalid-reference cases in `packages/reality-core/tests/test_application_catalog.py`
- [x] T005 [P] [US2] [FR-004] [FR-005] [FR-006] [FR-007] [FR-012] Add failing four-direct-plus-complete-launcher contracts in `apps/web/scripts/workspace-actions-contract.test.mjs`
- [x] T006 [P] [US3] [FR-008] [FR-009] [DR-001] [DR-003] [DR-004] Add failing allowlist, bounded-page, search, and tenant-boundary tests in `packages/reality-core/tests/test_http_boundary.py`
- [x] T007 [P] [US3] [FR-009] [FR-010] Add failing specialized route, explicit-column, state, and API-client contracts in `apps/web/scripts/workspace-actions-contract.test.mjs`
- [x] T008 Run focused tests, observe the intended failures, and record them in `specs/049-specialized-workspace-views/quickstart.md`

## Phase 3: User Story 1 — Discover Specialized Views (P1)

- [x] T009 [US1] [FR-001] [FR-002] [FR-003] Classify Orders, Warehouse Queue, Fulfillment blockers, and Supply & demand while excluding tenant usage and price resolution in `packages/reality-core/config/workspace_catalog.yaml`
- [x] T010 [US1] [FR-002] [FR-011] Extend validated Web routes and preserve safe multi-View projection reuse in `packages/reality-core/src/reality/catalogs.py`
- [x] T011 [US1] [FR-001] [FR-002] [FR-003] [FR-011] Run catalog tests and record the independent discovery result in `specs/049-specialized-workspace-views/quickstart.md`

## Phase 4: User Story 2 — Compact Complete Navigation (P1)

- [x] T012 [US2] [FR-004] [FR-005] Add generic four-direct View disclosure and launcher state in `apps/web/src/App.tsx`
- [x] T013 [US2] [FR-005] [FR-006] [FR-007] [FR-012] Implement the complete localized searchable View launcher with accessible close and selection behavior in `apps/web/src/App.tsx`
- [x] T014 [P] [US2] [FR-005] [FR-006] Add View-launcher translations for all supported languages in `apps/web/src/localization.tsx`
- [x] T015 [P] [US2] [FR-012] Add responsive launcher and sidebar disclosure styles in `apps/web/src/tailwind.css`
- [x] T016 [US2] [FR-004] [FR-005] [FR-006] [FR-007] [FR-012] Run frontend navigation contracts and record the result in `specs/049-specialized-workspace-views/quickstart.md`

## Phase 5: User Story 3 — Read Specialized Projections (P2)

- [x] T017 [US3] [FR-008] [FR-009] [DR-001] [DR-003] [DR-004] Add the allowlisted bounded projection View endpoint delegating to `projection_page` in `packages/reality-core/src/reality/web/api.py`
- [x] T018 [US3] [FR-008] [FR-009] Add typed bounded projection-page response and client method in `apps/web/src/api.ts`
- [x] T019 [US3] [FR-009] [FR-010] [DR-002] Implement trusted route metadata and the reusable readable projection table with search, paging, and shared states in `apps/web/src/App.tsx`
- [x] T020 [P] [US3] [FR-009] [FR-010] Add specialized page labels, columns, and state translations in `apps/web/src/localization.tsx`
- [x] T021 [P] [US3] [FR-009] [FR-010] Add responsive specialized table and toolbar styles in `apps/web/src/tailwind.css`
- [x] T022 [US3] [FR-008] [FR-009] [FR-010] [DR-001] [DR-002] [DR-003] [DR-004] Run HTTP and frontend specialized-page stories and record results in `specs/049-specialized-workspace-views/quickstart.md`

## Final Phase: Verification and Review

- [x] T028 [US2] [FR-004] [SC-002] Update the approved direct-View limit and durable Web contract from four to five in `specs/049-specialized-workspace-views/spec.md`, supporting artifacts, and `docs/WEB_SPEC.md`
- [x] T029 [US2] [FR-004] [SC-002] Add and observe a failing five-direct-Views regression contract in `apps/web/scripts/workspace-actions-contract.test.mjs`
- [x] T030 [US2] [FR-004] [SC-002] Raise the shared direct-View presentation limit to five in `apps/web/src/App.tsx`
- [x] T031 [US2] [FR-004] [SC-002] Run focused frontend contracts, the production Web build, spec checks, and final diff review

- [x] T023 [SC-005] Audit every FR/DR against scenarios, tests, and implementation tasks in `specs/049-specialized-workspace-views/spec.md` and `specs/049-specialized-workspace-views/tasks.md`
- [x] T024 [SC-004] Run `make spec-check`, catalog tests, and focused HTTP tests and record results in `specs/049-specialized-workspace-views/quickstart.md`
- [ ] T025 [SC-001] [SC-002] [SC-003] Run frontend contracts, format check, strict i18n audit, production build, and desktop/mobile visual checks and record results in `specs/049-specialized-workspace-views/quickstart.md`
- [ ] T026 Run `make lint` and the complete backend PostgreSQL suite and record results in `specs/049-specialized-workspace-views/quickstart.md`
- [x] T027 Review the final diff against the Constitution, approved scope, user-owned Docs changes, no-schema claim, and rollback plan in `specs/049-specialized-workspace-views/plan.md`

## Dependencies

- T001-T003 gate all implementation.
- T004-T008 precede the code they prove.
- User Story 1 establishes catalog routes consumed by User Stories 2 and 3.
- User Story 2 and User Story 3 can proceed after User Story 1, but shared `App.tsx` changes remain sequential.
- T023-T027 require all story tasks.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) |
|---|---|---|
| FR-001-FR-003 | T004 | T009-T011 |
| FR-004-FR-007, FR-012 | T005 | T012-T016 |
| FR-008-FR-010 | T006-T007 | T017-T022 |
| FR-011 | T004 | T010-T011 |
| DR-001-DR-004 | T006-T007 | T017-T022, T027 |
| SC-001-SC-005 | T023-T026 | T023-T027 |

## Implementation Strategy

The MVP is User Stories 1 and 2: complete classification plus compact discovery. User Story 3 completes the usable read destination and is required before release. All 27 tasks follow the required checkbox, ID, story, requirement, and file-path format.
