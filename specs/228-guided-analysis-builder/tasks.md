# Tasks: Guided Analysis Builder

## Phase 1: Specification and Design Gates
- [x] T001 Review accepted scope and quality checklist in `spec.md` and `checklists/requirements.md`.
- [x] T002 Resolve research and pass Constitution Check in `plan.md`.
- [x] T003 Analyze requirement/task consistency in `spec.md`, `plan.md`, `tasks.md`.

## Phase 2: Shared foundation and failing proof
- [x] T004 [US3] [FR-004] [FR-007] [FR-011] [FR-012] Add lossless path tests in `packages/reality-core/tests/test_analysis_builder.py` and advanced-state tests in `apps/web/scripts/graph-steps.test.mjs` and `apps/web/scripts/analysis-builder-state.test.mjs`.
- [x] T005 [US3] [FR-007] [FR-011] Implement formatter and parser preservation in `packages/reality-core/src/reality/services/analytics/cypher_surface.py`.

## Phase 3: Ask and refine (US1)
- [x] T006 [US1] [FR-002] [FR-009] [FR-011] Add provider/validation tests in `packages/reality-core/tests/test_analysis_builder.py`.
- [x] T007 [US1] [FR-002] [FR-009] [FR-011] Implement constrained interpretation in `packages/reality-core/src/reality/services/analytics/interpretation.py`.
- [x] T008 [US1] [FR-002] [FR-007] Expose shared graph tools in `packages/reality-core/src/reality/tools/graph.py`, `tools/application.py`, `mcp/catalog.py`, `web/analytics_api.py` and `apps/web/src/api.ts`.
- [x] T009 [US1] [FR-001] [FR-003] [FR-004] [FR-009] [FR-010] Add presentation/control regression tests in `apps/web/scripts/graph-steps.test.mjs` and `apps/web/scripts/analysis-builder-state.test.mjs`.
- [x] T010 [US1] [FR-001] [FR-003] [FR-004] [FR-009] Implement question panel and sentence controls in `apps/web/src/unified/analytics/GraphSteps.tsx`.

## Phase 4: Results and connections (US2)
- [x] T011 [US2] [FR-005] [FR-006] Add graph branch/metadata tests in `apps/web/scripts/graph-steps.test.mjs` and `apps/web/scripts/analysis-builder-state.test.mjs`.
- [x] T012 [US2] [FR-005] [FR-006] Implement honest result summary, connection diagram and node editor in `apps/web/src/unified/analytics/GraphSteps.tsx`.

## Phase 5: Expert editing and reports (US3)
- [x] T013 [US3] [FR-007] [FR-008] Add draft/save preservation tests in `apps/web/scripts/graph-steps.test.mjs` and `apps/web/scripts/analysis-builder-state.test.mjs` and `packages/reality-core/tests/test_analysis_builder.py`.
- [x] T014 [US3] [FR-004] [FR-007] [FR-008] Implement expert mode and explicit saves in `apps/web/src/unified/analytics/GraphSteps.tsx`.

## Final Phase: Presentation and verification
- [x] T015 [FR-001] [FR-010] Implement scoped reference styling in `apps/web/src/unified/analytics/AnalysisBuilder.css` and supported-language copy in `apps/web/src/localization.tsx`.
- [x] T016 [FR-011] [FR-012] Update contracts in `docs/features/analytics.md`, `docs/WEB_SPEC.md`, verify existing analytics resource membership in `packages/reality-core/config/resource_catalog.yaml` (no new command/view/projection labels); generate catalog docs.
- [x] T017 [FR-012] Run spec, lint, full backend and web gates; record evidence and any blockers in `specs/228-guided-analysis-builder/verification.md`.
- [x] T018 [FR-001] [FR-010] [FR-012] Review desktop/mobile rendering and final diff against all requirements; record in `specs/228-guided-analysis-builder/verification.md`.

- [x] T019 [US2] [FR-013] Add catalog transition tests in `apps/web/scripts/graph-steps.test.mjs` and `apps/web/scripts/analysis-builder-state.test.mjs`; implement `apps/web/src/unified/analytics/DataExplorer.tsx`, `AnalyticsPage.tsx` and `routing.ts`.

## Dependencies and strategy
T001–T003 precede code. T004 → T005; T006 → T007 → T008; T009 → T010; T011 → T012; T013 → T014; T015–T018 finish all stories. Backend unit proofs and frontend query-helper proofs are independent; implementation is performed sequentially to preserve shared working-tree changes. No partial story is declared complete in place of the full accepted scope.

## Requirement Coverage
| Requirement | Test tasks | Implementation tasks |
|---|---|---|
| FR-001 | T009, T018 | T010, T015 |
| FR-002 | T006 | T007, T008 |
| FR-003 | T009 | T010 |
| FR-004 | T004, T009, T013 | T010, T014 |
| FR-005 | T011 | T012 |
| FR-006 | T011 | T012 |
| FR-007 | T004, T013 | T005, T008, T014 |
| FR-008 | T013 | T014 |
| FR-009 | T006, T009 | T007, T010 |
| FR-010 | T009, T018 | T015 |
| FR-011 | T004, T006 | T005, T007, T016 |
| FR-012 | T017, T018 | T016–T018 |
| FR-013 | T019 | T019 |

## Application design refinement
- [x] T020 Review owner scope and designer recommendations; update requirements and plan.
- [x] T021 Remove Builder header/question/examples and unused UI state.
- [x] T022 Align all new analytics surfaces with shared application design tokens and controls.
- [x] T023 Run web checks and review desktop/mobile appearance; record evidence.

## Shared workspace integration
- [x] T024 Implement FR-014 shared shell/actions/local tabs and controls across all four views.
- [x] T025 Align flat lists, table geometry/footer and remove obsolete style overrides.
- [x] T026 Verify active-view action isolation, existing web contracts, build, localization, formatting and browser layout.

## Three-area workflow
- [x] T027 FR-015: Three tabs, first-analysis entry, integrated templates and unsaved adoption.
- [x] T028 FR-016: Shared global chat handoff, checked query context, removable attachment and safe send/retry lifecycle.
- [x] T029 FR-017: Authenticated proposal-to-analysis handoff with failure/unsupported handling.
- [x] T030 Update tests/localization/contracts; verify full web suite, build and browser workflow.

## Clear question hierarchy
- [x] T031 FR-018: Restore a contained question section with heading, prominent sentence, labeled conditions and subordinate advanced controls.
- [x] T032 Verify period deduplication/removal, unchanged query semantics and web checks.

## Compact editable question
- [x] T033 FR-019: Test meaningful grouping captions and lossless query preservation.
- [x] T034 FR-019: Compact neutral sentence, integrated date, filter empty state and secondary chat action.
- [x] T035 FR-019: Verify web checks, Chrome and final review.
