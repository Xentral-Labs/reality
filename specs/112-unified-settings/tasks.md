# Tasks: Unified Settings

## Gates
- [x] T001 Review spec.md, plan.md, research.md and quality checklist; analyze requirements before implementation.

## US1 — Personal preferences
- [x] T002 [US1] [FR-001 FR-002 FR-003 FR-004 FR-007] Add failing route contract in apps/web/scripts/unified-app-contract.test.mjs and interaction coverage in apps/web/scripts/unified-settings-browser.mjs.
- [x] T003 [US1] [FR-001 FR-002 FR-003] Add apps/web/src/unified/SettingsPage.tsx personal form and routing.ts/UnifiedApp.tsx/App.tsx wiring.
- [x] T004 [US1] [FR-004] Synchronize apps/web/src/theme.ts and unified/Shell.tsx appearance listeners.

## US2/US3 — Company configuration
- [x] T005 [US2] [US3] [FR-005 FR-006] Add owner/member/read-failure/company-switch assertions to apps/web/scripts/unified-settings-browser.mjs before owner summaries.
- [x] T006 [US2] [US3] [FR-005 FR-006] Add access and AI child views in apps/web/src/unified/SettingsPage.tsx using existing APIs only.
- [x] T007 [US1] [FR-007] Localize apps/web/src/localization.tsx; verify keyboard, theme and viewport matrix in browser harness.

## Completion
- [x] T008 Run complete required checks; record evidence and final review in specs/112-unified-settings/quickstart.md.
- [x] T009 [FR-001 FR-007] Update docs/WEB_SPEC.md, WEB_UX_MATRIX.md, SPEC_COVERAGE_MATRIX.md and apps/docs/content/product-guides/daily-control.md; update V0 status only after green checks.

## Dependencies and Requirement Coverage
T001 → T002/T005 failing proof → T003/T004/T006 → T007 → T008/T009.

| Requirement | Tests | Implementation |
| --- | --- | --- |
| FR-001 | T002 | T003 T009 |
| FR-002 FR-003 | T002 | T003 |
| FR-004 | T002 | T004 |
| FR-005 FR-006 | T005 | T006 |
| FR-007 | T002 T007 | T007 T009 |
