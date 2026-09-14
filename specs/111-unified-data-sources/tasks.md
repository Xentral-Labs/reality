# Tasks: Unified Data and Sources

## Gate
- [X] T001 Review specs/111-unified-data-sources/spec.md, plan.md and checklist; analyze all seven requirements.

## US1 — Registered origins
- [X] T002 [US1] [FR-002 FR-003 FR-004 FR-005 FR-006] Add failing tests in packages/reality-core/tests/test_unified_source_api.py for scoped metadata/SQL payload exclusion, paging/counts and exact-source evidence.
- [X] T003 [US1] [FR-002 FR-003] Implement packages/reality-core/src/reality/web/source_reads.py and typed GET adapters in web/api.py.

## US2 — Received versions
- [X] T004 [US2] [FR-004 FR-005] Add exact-source criterion to packages/reality-core/src/reality/web/read_models.py and existing evidence API.
- [X] T005 [US2] [FR-001 FR-004 FR-006] Add failing route contracts in apps/web/scripts/unified-app-contract.test.mjs and source traversal browser script unified-sources-browser.mjs.
- [X] T006 [US2] [FR-001 FR-002 FR-003 FR-004] Build apps/web/src/unified/DataSourcesPage.tsx and metadata/document clients in apps/web/src/api.ts.

## US3 — Shared evidence workspace
- [X] T007 [US3] [FR-005 FR-006] Complete documents tab and routing.ts/Shell.tsx/UnifiedApp.tsx/CaseAssistant.tsx in apps/web/src/unified/.
- [X] T008 [US3] [FR-007] Localize apps/web/src/localization.tsx and verify all locale/theme/viewport, keyboard and failure states.

## Completion
- [X] T009 Run all required gates; record review/evidence in specs/111-unified-data-sources/quickstart.md.
- [X] T010 Update docs/WEB_SPEC.md, docs/WEB_UX_MATRIX.md, docs/SPEC_COVERAGE_MATRIX.md and apps/docs/content/product-guides/daily-control.md.

## Dependencies and coverage
T001 → backend tests → read adapters → frontend tests → clients/UI/navigation → verification/docs. Research may run independently; shared code edits remain sequential. US1 is independently useful, US2 follows versioned originals, US3 adds the exact evidence continuation.

| Requirement | Test | Build |
| --- | --- | --- |
| FR-001 | T005 | T006 T007 |
| FR-002 FR-003 | T002 | T003 T006 |
| FR-004 FR-005 | T002 T005 | T004 T006 T007 |
| FR-006 | T002 T005 | T007 |
| FR-007 | T008 | T008 |
