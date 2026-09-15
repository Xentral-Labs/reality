# Tasks: Collapsible primary navigation

## Design gates
- [x] T001 Review spec.md; user scope accepted and clarifications resolved.
- [x] T002 Review plan.md Constitution PASS and cross-artifact coverage in analysis.md.

## User Story 1
- [x] T003 [US1] [FR-001] [FR-002] [FR-003] [FR-004] Add failing browser acceptance in apps/web/scripts/collapsible-navigation-browser.mjs.
- [x] T004 [US1] [FR-001] [FR-002] [FR-003] [FR-004] Implement local preference, toggle and reusable icon rail in apps/web/src/unified/Shell.tsx, apps/web/src/unified/ProfileMenu.tsx and apps/web/src/tailwind.css.
- [x] T005 [US1] [FR-004] Add translations in apps/web/src/localization.tsx.

## Verification
- [x] T006 Document behavior in docs/WEB_SPEC.md; run frontend and browser gates; record review in verification.md.

## Dependencies
T001 → T002 → T003 → T004 → T005 → T006. One independently testable story is the whole feature. Localization can be prepared alongside CSS after the design gate, but execution is sequential.

## Requested visual refinement
- [x] T007 [US1] [FR-005] [FR-006] Extend apps/web/scripts/collapsible-navigation-browser.mjs with custom tooltip and heading alignment acceptance.
- [x] T008 [US1] [FR-005] [FR-006] Add apps/web/src/unified/SidebarTooltip.tsx and refine Shell.tsx, ProfileMenu.tsx and tailwind.css.
- [x] T009 Re-run frontend/browser checks and update docs/WEB_SPEC.md and verification.md.
