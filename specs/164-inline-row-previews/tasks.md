---
description: "Requirement-traceable inline row preview implementation tasks"
---

# Tasks: Inline Row Previews

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/interaction-semantics.md`, `quickstart.md`
**Gate**: Constitution Check passed; product owner approved scope on 2026-09-10; no unresolved clarification

## Phase 1: Specification and Design Gates

- [x] T001 Confirm product requirements review and close clarification markers in `specs/164-inline-row-previews/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/164-inline-row-previews/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings across `specs/164-inline-row-previews/`

## Phase 2: Failing Proof and Shared Foundation

- [x] T004 [US1] [FR-001] Add failing structural and behavior contracts for inline list/table previews in `apps/web/scripts/inline-row-previews.test.mjs`
- [x] T005 [US2] [FR-005] Add failing semantic icon-and-label inventory assertions in `apps/web/scripts/inline-row-previews.test.mjs`
- [x] T006 [US4] [FR-003] Add the focused keyboard, context-reset, desktop, and mobile journey in `apps/web/scripts/daily-work-browser.mjs` and `apps/web/scripts/unified-finance-browser.mjs`
- [x] T007 [US1] [FR-013] Extract shared read-only Inspector content and introduce inline Inspector rendering in `apps/web/src/unified/Inspector.tsx` and `apps/web/src/unified/InlinePreview.tsx`
- [x] T008 [US1] [FR-002] Add controlled single-open list disclosure and focus restoration in `apps/web/src/unified/WorkList.tsx`

## Phase 3: User Story 1 — Daily-work previews (P1)

- [x] T009 [US1] [FR-001] Replace the Commitments drawer preview with inline read-only commitment explanation while retaining focused work navigation in `apps/web/src/unified/CommitmentsPage.tsx`
- [x] T010 [US1] [FR-001] Replace the Exceptions drawer preview with inline finding guidance and separate deeper links in `apps/web/src/unified/AttentionPage.tsx`
- [x] T011 [US1] [FR-004] Replace the Decisions summary drawer with inline proposal preview while retaining the separate review workflow in `apps/web/src/unified/DecisionsPage.tsx`
- [x] T012 [US1] [FR-011] Run the daily-work contract proof from `apps/web/scripts/inline-row-previews.test.mjs`

## Phase 4: User Story 2 — Semantic actions (P1)

- [x] T013 [US2] [FR-005] Apply disclosure, navigation, related-filter, edit, and operational-action icon semantics in `apps/web/src/unified/OrdersPage.tsx`, `WarehousePage.tsx`, `FinancePage.tsx`, and `MasterDataPage.tsx`
- [x] T014 [US2] [FR-006] Add accessible outcome names and tooltips where controls remain icon-only in all in-scope page files under `apps/web/src/unified/`
- [x] T015 [US2] [FR-018] Record the semantic action contract in `docs/WEB_SPEC.md` and page-specific inline patterns in `docs/WEB_UX_MATRIX.md`
- [x] T016 [US2] [FR-007] Run the semantic inventory proof from `apps/web/scripts/inline-row-previews.test.mjs`

## Phase 5: User Story 3 — Workspace previews (P2)

- [x] T017 [US3] [FR-008] Add inline document and commitment detail rows to Sales and Purchasing in `apps/web/src/unified/OrdersPage.tsx`
- [x] T018 [US3] [FR-008] Add inline stock, reservation, and movement detail rows to `apps/web/src/unified/WarehousePage.tsx`
- [x] T019 [US3] [FR-008] Add inline open-item, payment, and journal detail rows to `apps/web/src/unified/FinancePage.tsx`
- [x] T020 [US3] [FR-016] Replace passive Master Data side detail with conditional inline previews while keeping editors separate in `apps/web/src/unified/MasterDataPage.tsx`
- [x] T021 [US3] [FR-014] Preserve explicit full-trace destinations from each Inspector-backed preview in `apps/web/src/unified/InlinePreview.tsx`
- [x] T022 [US3] [DR-001] Run existing Inspector, workspace, finance, and action confirmation contract tests from `apps/web/scripts/*.test.mjs`

## Phase 6: User Story 4 — Responsive and interaction stability (P2)

- [x] T023 [US4] [FR-010] Clear stale preview identity on tenant, route, tab, family, page, search, and filter changes in each in-scope page under `apps/web/src/unified/`
- [x] T024 [US4] [FR-012] Complete focus restoration and one-preview switching behavior in `apps/web/src/unified/InlinePreview.tsx` and `WorkList.tsx`
- [x] T025 [US4] [FR-015] Add bounded responsive preview styling using shared `br-*` primitives in `apps/web/src/unified/InlinePreview.tsx`
- [x] T026 [US4] [FR-003] Run focused daily-work and Finance browser journeys at desktop and mobile widths and record evidence in `specs/164-inline-row-previews/quickstart.md`

## Final Phase: Cross-Cutting Review

- [x] T027 Run `make spec-check` and reconcile requirement coverage in `specs/164-inline-row-previews/tasks.md`
- [x] T028 Run frontend contract tests, localization audit, formatting check, and production build in `apps/web/`
- [x] T029 Review the diff for absence of migration, backend, business-rule, tenant-boundary, and confirmation changes
- [x] T030 Run the focused desktop/mobile visual review and record screenshots/results in `specs/164-inline-row-previews/quickstart.md`
- [x] T031 Update task status only from actual green evidence and leave reviewer-owned checklist markers unchanged in `specs/164-inline-row-previews/`

## Dependencies

- T003 blocks implementation.
- T004–T006 precede T007–T011 and T017–T025.
- US1 establishes the shared list primitive used by US2 and the workspace stories.
- US2 and US3 may proceed independently after the shared foundation.
- US4 completes after all in-scope pages adopt the pattern.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–004 | T004, T012 | T007–T011 | Pending |
| FR-005–007 | T005, T016 | T013–T015 | Pending |
| FR-008–009 | T004, T022 | T008, T017–T020 | Pending |
| FR-010–012 | T006, T026 | T023–T024 | Pending |
| FR-013–017 | T022, T026 | T007, T021, T025 | Pending |
| FR-018 | T016, T027 | T015 | Pending |
| DR-001–005 | T022, T027–T029 | T007, T015, T021 | Pending |
| FR-019–020 | T004, T026, T030 | T007, T013, T025 | Complete |
