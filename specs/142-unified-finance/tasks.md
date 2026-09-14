# Tasks: Unified Finance

## Setup and gate
- [X] T001 Review specs/142-unified-finance/spec.md, plan.md and built-in requirements checklist; analyze requirement coverage before implementation.

## US1 — Open items
- [X] T002 [US1] [FR-001 FR-002 FR-006] Add failing route/recovery tests in apps/web/scripts/unified-app-contract.test.mjs and Finance browser proof in apps/web/scripts/unified-finance-browser.mjs.
- [X] T003 [US1] [FR-001 FR-002] Build open-item presentation in apps/web/src/unified/FinancePage.tsx using existing canonical reads and complete per-currency controls.

## US2 — Payments and journal
- [X] T004 [US2] [FR-003 FR-004 FR-005] Add paged payment/journal browser cases in apps/web/scripts/unified-finance-browser.mjs.
- [X] T005 [US2] [FR-003 FR-004 FR-005] Extend optional page in apps/web/src/api.ts; add payment/journal tabs and native Inspector to FinancePage.tsx.

## US3 — Shared App
- [X] T006 [US3] [FR-001 FR-006] Wire routing.ts, CaseAssistant.tsx, Shell.tsx and UnifiedApp.tsx in apps/web/src/unified/.
- [X] T007 [US3] [FR-007] Add controls to apps/web/src/localization.tsx and run the browser locale/theme/viewport, keyboard and failure matrix.

## Completion
- [X] T008 Run full backend/frontend/browser/docs gates and record evidence and review in specs/142-unified-finance/quickstart.md.
- [X] T009 Update docs/WEB_SPEC.md, docs/WEB_UX_MATRIX.md, docs/SPEC_COVERAGE_MATRIX.md and apps/docs/content/product-guides/daily-control.md.

## Dependencies / strategy
T001 → tests → client/UI → routing/localization → full verification and docs. US1 is independently useful; US2 reuses its register scaffolding. Tests/read-only research can run alongside independent design, but shared-file edits stay sequential.

## Coverage
| Requirement | Tests | Implementation |
| --- | --- | --- |
| FR-001 FR-002 | T002 | T003 T006 |
| FR-003 FR-004 | T004 | T005 |
| FR-005 | T004 | T005 |
| FR-006 | T002 | T006 |
| FR-007 | T007 | T007 |
