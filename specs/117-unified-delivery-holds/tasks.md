# Tasks: Unified Delivery Holds

## Gates
- [x] T001 Review accepted scope and requirements in `spec.md`.
- [x] T002 Pass Constitution and resolve research in `plan.md` and `research.md`.
- [x] T003 Analyze `spec.md`, `plan.md`, `tasks.md` for coverage and conflicts before implementation.

## US1/US2 — Explain and control delivery holds
- [x] T004 [US1] [US2] [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] Add failing service/tool/API, stale, scope and event recovery proofs in `packages/reality-core/tests/test_unified_delivery_holds.py`.
- [x] T005 [US1] [US2] [FR-001] [FR-002] [FR-003] [FR-004] Implement shared validation, action attribution and snapshots/proof in `packages/reality-core/src/reality/services/core.py`, `hold_actions.py` and `delivery_reads.py`.
- [x] T006 [US2] [FR-002] [FR-003] [FR-004] [FR-005] Extend shared review/execute/API plumbing in `packages/reality-core/src/reality/services/delivery_actions.py`, `tools/application.py` and `web/api.py`.
- [x] T007 [US2] Prove independent hold/release stories and record results in `quickstart.md`.

## US3 — Shared UI and recovery
- [x] T008 [US3] [FR-001] [FR-002] [FR-003] [FR-005] [FR-006] Add failing browser case/global/review/reload/scope/layout proof in `apps/web/scripts/unified-holds-browser.mjs`.
- [x] T009 [US3] [FR-001] [FR-002] [FR-003] [FR-005] [FR-006] Extend `apps/web/src/unified/ActionCard.tsx`, `ActionLauncher.tsx`, `DeliveryCase.tsx`, `ChatPage.tsx`, `DecisionsPage.tsx`, `apps/web/src/api.ts` and `localization.tsx` with shared hold controls and reason labels.

## Completion
- [x] T010 [FR-006] Run full backend, frontend contracts/build/i18n/format, new and existing action browser journeys, spec/Ruff/diff checks; record in `quickstart.md`.
- [x] T011 Review final diff and update `docs/WEB_SPEC.md`, `docs/SPEC_COVERAGE_MATRIX.md`, `docs/V0_CHECKLIST.md` and `docs/ideas/unified-capability-inventory.md` with verified scope.

## Order and coverage
T001–T003 precede implementation. T004 precedes T005–T006; T008 precedes T009. Test authoring for backend and browser can be independent; shared production files are edited sequentially. T010–T011 follow both stories. MVP is own hold/release with scope clarity; all listed tasks are required for completion. Requirement-to-test and implementation mapping is in spec.md; every FR is explicitly covered here.
