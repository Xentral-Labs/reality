# Tasks: Unified Receipt and Reservation Release

## Design gates
- [x] T001 Review accepted scope and requirements in `spec.md`.
- [x] T002 Complete Constitution PASS and research in `plan.md` and `research.md`.
- [x] T003 Analyze `spec.md`, `plan.md`, `tasks.md` before implementation.

## US1 — Supplier receipt
- [x] T004 [US1] [FR-001] [FR-003] Add failing receipt, invalid/stale/foreign and replay tests in `packages/reality-core/tests/test_unified_receipt_release.py`.
- [x] T005 [US1] [FR-001] [FR-003] Extend shared case/review/verification in `packages/reality-core/src/reality/services/delivery_reads.py` and `delivery_actions.py`.

## US2 — Reservation release
- [x] T006 [US2] [FR-002] [FR-003] Add failing full-release, inactive/stale/foreign and unchanged-stock tests in `packages/reality-core/tests/test_unified_receipt_release.py`.
- [x] T007 [US2] [FR-002] [FR-003] Extend release resolver/snapshot and validation in `packages/reality-core/src/reality/services/delivery_actions.py`.

## US3 — Shared actions and recovery
- [x] T008 [US3] [FR-004] Add event reconciliation, conflicting pool, tool/API parity tests in `packages/reality-core/tests/test_unified_receipt_release.py`.
- [x] T009 [US3] [FR-003] [FR-004] Extend execution resolver and API allowlist in `packages/reality-core/src/reality/tools/application.py` and `web/api.py`.
- [x] T010 [US3] [FR-005] [FR-006] Add register/launcher/review/recovery browser proof in `apps/web/scripts/unified-receipt-release-browser.mjs` before UI changes.
- [x] T011 [US3] [FR-001] [FR-002] [FR-004] [FR-005] Extend `apps/web/src/unified/ActionCard.tsx`, `ActionLauncher.tsx`, `UnifiedApp.tsx`, `OrdersPage.tsx`, `WarehousePage.tsx`, `ChatPage.tsx`, `DecisionsPage.tsx` and `apps/web/src/api.ts`.
- [x] T012 [US3] [FR-006] Complete shared translations and keyboard/empty/error states in `apps/web/src/localization.tsx` and `unified/ActionCard.tsx`.

## Verification and review
- [x] T013 Run full backend suite, frontend contracts/build/i18n, relevant browser journeys, spec/Ruff/diff checks; record results in `quickstart.md`.
- [x] T014 [FR-005] Review diff and update `docs/WEB_SPEC.md`, `docs/V0_CHECKLIST.md` and `docs/ideas/unified-capability-inventory.md` only when checks pass.

## Dependency and coverage
T001–T003 precede all implementation. T004/T006/T008 may be authored together before T005/T007/T009. T010 precedes T011/T012; T013–T014 follow both stories. Backend test authoring and browser test authoring are independent work opportunities; implementation stays sequential where files overlap.

| Requirement | Tests | Implementation |
| --- | --- | --- |
| FR-001 | T004, T010 | T005, T011 |
| FR-002 | T006, T010 | T007, T011 |
| FR-003 | T004, T006, T008 | T005, T007, T009 |
| FR-004 | T008, T010 | T009, T011 |
| FR-005 | T010, T013 | T011, T014 |
| FR-006 | T010, T013 | T012 |
