# Tasks: Unified Movement Corrections

## Gates
- [x] T001 Review accepted requirements and quality checklist in `spec.md`.
- [x] T002 Complete research and Constitution Check in `plan.md`.
- [x] T003 Analyze requirement/plan/task coverage before implementation.

## US1/US2 — Shared correction semantics and proof
- [x] T004 [US1] [US2] [FR-002] [FR-003] [FR-004] [FR-006] Add failing correction/chain/projected-stock/identity/stale/tenant/recovery tests in `packages/reality-core/tests/test_unified_movement_corrections.py`.
- [x] T005 [US1] [FR-002] [FR-006] Implement pure projected preview validation and action attribution in `packages/reality-core/src/reality/services/core.py`.
- [x] T006 [US2] [FR-003] [FR-004] Add dedicated state/review/proof and overlap guard in `packages/reality-core/src/reality/services/movement_correction_actions.py`; dispatch early through `services/delivery_actions.py` and canonical `tools/application.py`.
- [x] T007 [US2] [FR-003] [FR-005] Extend `packages/reality-core/src/reality/web/api.py` preparation allowlist and add HTTP/auth/practice parity tests in `tests/test_unified_movement_corrections.py`.
- [x] T008 [US1] [US2] Run targeted new and existing correction stories and record results in `quickstart.md`.

## US3 — Unified correction UI
- [x] T009 [US3] [FR-001] [FR-005] [FR-007] Add failing browser case/global/Chat/Decisions/reload/edit/confirmation/layout proof in `apps/web/scripts/unified-corrections-browser.mjs`.
- [x] T010 [US3] [FR-001] [FR-005] [FR-007] Implement `apps/web/src/unified/CorrectionCard.tsx` and common `ActionCard.tsx` dispatch; extend `api.ts`, `ActionLauncher.tsx`, `UnifiedApp.tsx`, `WarehousePage.tsx`, `ChatPage.tsx`, `DecisionsPage.tsx` and `localization.tsx` with preserved intent and shared actions.
- [x] T011 [US3] [FR-004] [FR-005] [FR-007] Verify read/error/uncertain outcome/Inspector refresh and localized responsive screenshots in `apps/web/scripts/unified-corrections-browser.mjs`.

## Completion
- [x] T012 Run full backend and frontend contracts/build/i18n/format; new and existing action browser journeys; spec/Ruff/diff checks. Record evidence in `quickstart.md`.
- [x] T013 Review all FRs, no schema/source mutations and final diff; update `docs/WEB_SPEC.md`, `docs/SPEC_COVERAGE_MATRIX.md`, `docs/V0_CHECKLIST.md` and `docs/ideas/unified-capability-inventory.md`; restart shared preview and verify reads only.

## Coverage and order
T001–T003 precede code. T004 precedes T005–T007; T009 precedes T010. T008 and T011 prove independent stories; T012–T013 close the increment. FR-001: T009/T010; FR-002: T004/T005; FR-003: T004/T006/T007; FR-004: T004/T006/T011; FR-005: T007/T009/T010/T011; FR-006: T004/T005; FR-007: T009/T010/T011. All tasks are required; no additional feature scope is implied by parallelizable test authoring.
