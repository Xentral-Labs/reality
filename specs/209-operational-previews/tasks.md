# Tasks: Operational quick previews

## Phase 1: Specification and Design Gates
- [x] T001 Confirm user-approved scope and requirements quality in `specs/209-operational-previews/spec.md` and `checklists/requirements.md`.
- [x] T002 Review Constitution Check in `specs/209-operational-previews/plan.md`.
- [x] T003 Analyze specification, plan and tasks; record result in `specs/209-operational-previews/verification.md`.

## Phase 2: User Story 1
- [x] T004 [US1] [FR-001] [FR-002] [FR-003] [FR-007] Add failing document/tenant/read-only tests in `packages/reality-core/tests/test_operational_previews.py`.
- [x] T005 [US1] [FR-001] [FR-002] [FR-003] [FR-007] Compose document and commitment previews in `packages/reality-core/src/reality/services/operational_previews.py` and delegate from `web/api.py`.

## Phase 3: User Story 2
- [x] T006 [US2] [FR-004] [FR-005] [FR-007] Add warehouse/shipment tests in `packages/reality-core/tests/test_operational_previews.py`.
- [x] T007 [US2] [FR-004] [FR-005] [FR-007] Compose named warehouse and shipment previews in `packages/reality-core/src/reality/services/operational_previews.py`.

## Phase 4: User Story 3
- [x] T008 [US3] [FR-006] [FR-007] Add partial settlement/allocation/reversal tests in `packages/reality-core/tests/test_operational_previews.py`.
- [x] T009 [US3] [FR-006] [FR-007] Scope existing financial reads in `packages/reality-core/src/reality/services/core.py` and compose finance preview sections in `operational_previews.py`.

## Phase 5: Shared UI and Review
- [x] T010 [FR-001] [FR-002] [FR-008] Add browser acceptance fixtures/assertions in `apps/web/scripts/operational-previews-browser.mjs` and `apps/web/scripts/operational-preview-labels.test.mjs`.
- [x] T011 [FR-001] [FR-008] Render optional preview sections, hints, overflow and named links in `apps/web/src/api.ts`, `unified/InlinePreview.tsx`, `unified/Inspector.tsx`, `unified/ShipmentsRegister.tsx`; localize in `localization.tsx`.
- [x] T012 [FR-001] [FR-007] [FR-008] Update `docs/WEB_SPEC.md` and `docs/SPEC_COVERAGE_MATRIX.md`; run all checks listed in plan and review final diff, recording results in `specs/209-operational-previews/verification.md`.

## Phase 6: Approved Master-data Extension
- [x] T013 [US4] [FR-009] Add failing list/name/format/revision tests in `packages/reality-core/tests/test_reference_workspace.py` and master-data browser fixtures in `apps/web/scripts/operational-previews-browser.mjs`.
- [x] T014 [US4] [FR-009] Enrich bounded reads in `packages/reality-core/src/reality/services/reference_workspace.py`, add preview presentation in `operational_previews.py`, and render via `apps/web/src/unified/MasterDataPage.tsx` with column profiles in `RegisterTable.tsx`.
- [x] T015 [US4] [FR-010] Assert navigation placement in `apps/web/scripts/operational-previews-browser.mjs`, then move the existing link in `apps/web/src/unified/Shell.tsx`.
- [x] T016 [US4] [FR-009] [FR-010] Update `docs/WEB_SPEC.md` and rerun relevant backend, frontend/browser and spec checks; record evidence in `specs/209-operational-previews/verification.md`.

## Dependencies and Strategy
T001–T003 gate implementation. T004/T006/T008 precede their service code. T010 precedes UI changes. Deliver all four stories before completion. Test fixture cases can be developed independently; shared files are edited sequentially. No schema/migration task is needed.

## Requirement Coverage
| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T004,T010 | T005,T011 |
| FR-002 | T004,T010 | T005 |
| FR-003 | T004 | T005 |
| FR-004 | T006 | T007 |
| FR-005 | T006 | T007 |
| FR-006 | T008 | T009 |
| FR-007 | T004,T006,T008 | T005,T007,T009 |
| FR-008 | T010 | T011,T012 |
| FR-009 | T013 | T014,T016 |
| FR-010 | T015 | T015,T016 |
