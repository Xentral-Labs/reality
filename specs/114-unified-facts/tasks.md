# Tasks: Unified Facts

## Gates
- [x] T001 Review spec/research/Constitution and analyze requirement coverage before implementation.

## US1 — Recorded observations
- [x] T002 [US1] [FR-002 FR-003 FR-006] Add failing tests in packages/reality-core/tests/test_unified_facts_api.py for scoped search/count, stable paging, repeated observations, source/rule metadata projection and bounded choices.
- [x] T003 [US1] [FR-002 FR-003 FR-006] Add web/fact_reads.py and update web/api.py facts read; preserve defaults and metadata shapes.
- [x] T004 [US1] [FR-001 FR-003 FR-007] Add failing route tests and original-content/browser coverage in apps/web/scripts/unified-app-contract.test.mjs and unified-facts-browser.mjs.

## US2 — Context and evidence
- [x] T005 [US2] [FR-004 FR-005] Add exact source/subject/foreign Inspector tests in test_unified_facts_api.py and update the intentional Inspector meaning assertion in test_master_data_api.py.
- [x] T006 [US2] [FR-005] Update shared fact Inspector in web/api.py and original-value markers in apps/web/src/unified/Inspector.tsx.
- [x] T007 [US1] [US2] [FR-001 FR-003 FR-004 FR-006] Build FactsPage.tsx, typed api.ts client, routing/Shell/UnifiedApp/CaseAssistant and DataSourcesPage links.

## US3 and completion
- [x] T008 [US3] [FR-006 FR-007] Localize localization.tsx and verify keyboard/reload/error/reset and16 visual combinations.
- [x] T009 Run full required suites and authenticated synthetic preview; record final review in quickstart.md.
- [x] T010 Update WEB_SPEC, WEB_UX_MATRIX, SPEC_COVERAGE_MATRIX, daily-control guide and migration tracking; update V0 only after green verification.

## Dependencies and coverage
T001 → T002/T004/T005 failing proof → T003/T006 → T007 → T008 → T009/T010.

| Requirement | Tests | Implementation |
| --- | --- | --- |
| FR-001 | T004 | T007 |
| FR-002 | T002 | T003 |
| FR-003 | T002 T004 | T003 T007 |
| FR-004 | T005 | T007 |
| FR-005 | T005 | T006 |
| FR-006 | T002 T008 | T003 T007 T008 |
| FR-007 | T004 T008 | T008 |
