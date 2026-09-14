# Tasks: Categorized Action Discovery

## Phase 1: Gates

- [x] T001 Record product approval and reviewed requirements in `spec.md`.
- [x] T002 Complete PASS Constitution Check and design in `plan.md`.
- [x] T003 Analyze `spec.md`, `plan.md`, `tasks.md` before implementation.

## Phase 2: Foundational failing proof

- [x] T004 [US1] [FR-001, FR-006, DR-001] Add classification/drift tests in `packages/reality-core/tests/test_action_discovery.py`.
- [x] T005 [US1] [FR-001, FR-006, DR-001] Implement validated catalog in `packages/reality-core/config/action_discovery.json`, `src/reality/action_discovery.py`, and `src/reality/catalogs.py`.

## Phase 3: Browse the directory

- [x] T006 [US1] [FR-002, FR-003, FR-006, FR-007] Add grouping and availability tests in `apps/web/scripts/action-discovery.test.mjs`.
- [x] T007 [US1] [FR-001, FR-002, FR-003, FR-006, FR-007] Implement `apps/web/src/unified/actionDiscovery.ts`, `ActionDirectory.tsx`, reference types in `api.ts`, and integration in `RealityInspectorPage.tsx`.

## Phase 4: Search and access

- [x] T008 [US2] [FR-004, FR-005] Add search/reset/keyboard/narrow-screen tests in `apps/web/scripts/action-discovery.test.mjs` and `action-discovery-browser.mjs`.
- [x] T009 [US2] [FR-004, FR-005] Implement search/controlled disclosures in `ActionDirectory.tsx` and translations in `apps/web/src/localization.tsx`.

## Phase 5: Contextual actions

- [x] T010 [US3] [FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, DR-001, DR-002, DR-003] Add context matrix and no-write browser checks in `apps/web/scripts/action-discovery.test.mjs` and `action-discovery-browser.mjs`.
- [x] T011 [US3] [FR-006, FR-007, FR-008, FR-009, FR-010, FR-012, DR-001, DR-002, DR-003] Integrate shared `ActionLauncher.tsx` metadata/provider into `Shell.tsx`, `UnifiedApp.tsx`, `WarehousePage.tsx`, `FinancePage.tsx`; preserve explicit record dispatch and confirmation services.
- [x] T012 [US3] [FR-011] Complete every-screen/form placement review in `inventory.md` and update `docs/WEB_SPEC.md`.

## Final phase: Verify and review

- [x] T013 Run `make spec-check`, `make lint`, complete PostgreSQL suite and `make web-build`; record results in `verification.md`.
- [x] T014 Run new browser proof and relevant existing action browser regressions; inspect screenshots and record `verification.md`.
- [x] T015 Review final diff, API additive compatibility and no-migration rollout; update `quickstart.md`, `docs/SPEC_COVERAGE_MATRIX.md` and task status from actual evidence only.

## Dependencies and independent verification

T001–T003 → T004–T005 → US1/US2 → US3 → final verification. Tests precede the
corresponding code. US1 independently checks catalog coverage and browsing; US2
checks search/accessibility; US3 checks context and preserved execution paths.
Within a story the unit and browser checks can run independently after implementation;
backend unit checks and frontend builds can run concurrently. No concurrent file edits.
All FR-001–012 and DR-001–003 map to both test and implementation/documentation tasks.

- [x] T016 [US3] [FR-008] Remove duplicate Stock contextual placements, retain creation
      actions on their owning Reservations/Movements tabs and globally, update matrix tests,
      verify frontend/backend discovery gates, and redeploy Web/API configuration.
