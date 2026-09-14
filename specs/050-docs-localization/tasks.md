---
description: "Requirement-traceable multilingual Docs implementation tasks"
---

# Tasks: Multilingual Product Documentation

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/docs-locale-contract.md`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review and close clarification markers in `specs/050-docs-localization/spec.md`
- [x] T002 Confirm all Constitution Check rows are PASS in `specs/050-docs-localization/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings in `specs/050-docs-localization/`

## Phase 2: Failing Proof

- [x] T004 [US1] [FR-001] [FR-002] Add failing locale inventory and four-language configuration assertions in `apps/docs/scripts/docs-contract.test.mjs`
- [x] T005 [US1] [FR-003] [FR-008] Add failing localized navigation, theme-copy, and search assertions in `apps/docs/scripts/docs-contract.test.mjs`
- [x] T006 [US2] [FR-004] [FR-005] [FR-006] [FR-007] [FR-014] Add failing selector route-symmetry, stable-English, and fallback assertions in `apps/docs/scripts/docs-contract.test.mjs`
- [x] T007 [US3] [FR-009] [FR-010] [FR-011] [FR-012] [FR-013] [FR-015] Add failing guide parity, protected-token, and diagnostic assertions in `apps/docs/scripts/docs-contract.test.mjs`

## Phase 3: User Story 1 — Complete localized reader journey (P1)

**Independent test**: Select each locale and reach every reader area and guide chapter with localized navigation and search controls.

- [x] T008 [US1] [FR-001] [FR-003] Configure root, German, Dutch, and Spanish locales and shared navigation topology in `apps/docs/.vitepress/config.mts`
- [x] T009 [P] [US1] [FR-002] [FR-009] [FR-010] Translate the complete German page inventory in `apps/docs/content/de/`
- [x] T010 [P] [US1] [FR-002] [FR-009] [FR-010] Translate the complete Dutch page inventory in `apps/docs/content/nl/`
- [x] T011 [P] [US1] [FR-002] [FR-009] [FR-010] Translate the complete Spanish page inventory in `apps/docs/content/es/`
- [x] T012 [US1] [FR-003] [FR-008] Add localized theme, search, not-found, edit, and footer copy in `apps/docs/.vitepress/config.mts`
- [x] T013 [US1] Run the four-language reader-journey contract tests in `apps/docs/scripts/docs-contract.test.mjs`

## Phase 4: User Story 2 — Context-preserving language switch (P2)

**Independent test**: Switch among all locales on nested pages and retain the equivalent topic; root English routes remain valid.

- [x] T014 [US2] [FR-004] [FR-005] [FR-014] Enable locale selector routing for equivalent relative paths in `apps/docs/.vitepress/config.mts`
- [x] T015 [US2] [FR-006] [FR-007] Preserve canonical English paths and explicit fallback behavior in `apps/docs/.vitepress/config.mts`
- [x] T016 [US2] Run selector and route acceptance checks from `specs/050-docs-localization/quickstart.md`

## Phase 5: User Story 3 — Safe translation maintenance (P3)

**Independent test**: Contract fixtures detect missing pages, navigation, broken links, chapters, and semantic markers with locale/path diagnostics.

- [x] T017 [US3] [FR-011] Translate and cross-link all guide pages under `apps/docs/content/{de,nl,es}/concepts/business-reality-guide/`
- [x] T018 [US3] [FR-012] [FR-013] Implement inventory, link, and navigation parity checks in `apps/docs/scripts/docs-contract.test.mjs`
- [x] T019 [US3] [FR-009] [FR-010] [FR-015] Implement protected-token and guide marker checks in `apps/docs/scripts/docs-contract.test.mjs`
- [x] T020 [US3] Verify business semantics using `specs/050-docs-localization/quickstart.md`

## Final Phase: Cross-Cutting Review

- [x] T021 Run Docs formatting, tests, and build from `apps/docs/`
- [x] T022 Run `make spec-check` and `git diff --check` from repository root
- [x] T023 Review the diff against the Constitution and FR-001–FR-015 in `specs/050-docs-localization/spec.md`
- [x] T024 Update task status only after all checks are green in `specs/050-docs-localization/tasks.md`

## Dependencies

- Phase 1 blocks implementation; Phase 2 tests precede behavior.
- User Story 1 is the MVP; User Story 2 depends on its locale topology.
- User Story 3 depends on complete content; its tests begin in Phase 2.
- The three translation tasks can run in parallel.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T004 | T008 | Complete |
| FR-002 | T004 | T009–T011 | Complete |
| FR-003 | T005 | T008, T012 | Complete |
| FR-004–FR-007 | T006 | T014–T015 | Complete |
| FR-008 | T005 | T012 | Complete |
| FR-009–FR-010 | T007 | T009–T011, T019 | Complete |
| FR-011 | T007 | T017 | Complete |
| FR-012–FR-013 | T007 | T018 | Complete |
| FR-014 | T006 | T014 | Complete |
| FR-015 | T007 | T019 | Complete |
