# Tasks: Practice Companies

## Design gates
- [x] T016 [FR-010] Add responsive company-menu regression, implement viewport sizing,
  and verify frontend contracts/build; no membership or business behavior changes.
  Evidence: regression failed before CSS change; 108 contracts and production build
  passed afterward. Desktop/mobile visual inspection remains a release review check.
- [x] T013 [FR-008] [FR-009] Add API/service regressions for shared practice companies and protected boundaries before implementation.
- [x] T014 [FR-008] [FR-009] Implement persisted eligibility, local-operation policy, bootstrap metadata and bidirectional App navigation with Sandbox labels.
- [x] T015 [FR-008] [FR-009] Verify backend and web gates, review boundary changes and deploy locally; record evidence.
- [x] T001 Review owner-approved scope in spec.md and Constitution PASS in plan.md.
- [x] T002 Analyze spec.md, plan.md and tasks.md for coverage and critical findings. Six FR/DR fully covered, zero critical findings; checklist 5/5 PASS.

## US1 — Named creation
- [x] T003 [US1] [FR-001] [FR-003] [FR-004] [DR-002] Add failing tests in packages/reality-core/tests/test_playground_practice_companies.py and apps/web/scripts/playground-free-operations.test.mjs.
- [x] T004 [US1] [FR-001] [FR-003] [FR-004] [DR-002] Implement metadata/migration in db/core.py and migrations/versions/0043_playground_practice_companies.py; setup/API in services/playground.py and web/playground.py; update config/data_model.yaml.
- [x] T005 [US1] [FR-001] [FR-003] [FR-004] Add kind/name creation and retry UI in apps/web/src/api.ts, playground/PlaygroundPage.tsx, PlaygroundWorkspace.tsx and localization.tsx.

## US2 — Persistent lifecycle
- [x] T006 [US2] [FR-002] [DR-001] [SC-001] Add alternating/foreign/restart tests in packages/reality-core/tests/test_playground_practice_companies.py.
- [x] T007 [US2] [FR-002] [DR-001] Preserve practice runs in services/playground.py start/initialize/restart and temporary-only restart selection in PlaygroundPage.tsx.

## Verification
- [x] T008 [FR-001] [FR-003] [SC-002] Extend apps/web/scripts/playground-workspace-browser.mjs for named setup/reopen; verify browser journeys, themes/mobile.
- [x] T009 [FR-001] [FR-002] [FR-003] [FR-004] [DR-001] [DR-002] [SC-002] Run full backend, migration and UI gates; review diff; update docs/WEB_SPEC.md, docs/SPEC_COVERAGE_MATRIX.md and quickstart.md; migrate/deploy locally without data deletion.

## Dependencies
- [x] T012 [FR-007] Add API catalog parity/auth regression and browser fixture, implement read-only catalog adapter and information dialog, run targeted backend and frontend/browser gates, deploy locally. Analysis: canonical metadata reused, no business logic or persistence changes, no critical findings.
- [x] T011 [FR-006] Add browser proof and explanatory return/exit UI in OperationChooser.tsx and PlaygroundPage.tsx; translate and verify alongside T010. Analysis: no unresolved scope, no critical findings; pending execution remains outside the exit path.
- [x] T010 [FR-005] Add creation review browser assertions, refine PlaygroundPage.tsx and translations, verify contracts/build/localization and responsive themed browser checks. Pre-implementation review: owner-approved scope, Constitution PASS, complete test mapping, no critical consistency findings.

T001→T002→T003/T006→T004/T007→T005→T008→T009. Tests before implementation.
Test cases can run independently; shared service edits remain sequential. Ship both
stories together because naming without lifecycle protection is misleading.
