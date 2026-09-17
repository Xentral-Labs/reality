# Tasks: Refined workspace shell

## Setup and requirements
- [x] T001 Review approved scope, requirements checklist and Constitution Check (FR-001–007).

## Tests first
- [x] T002 [US1] Add failing layout, title and draft checks in `apps/web/scripts/refined-shell-browser.mjs` (FR-001/002/005).
- [x] T003 [US2] Add utility, company and simulation reachability checks in the same browser script (FR-003/004).
- [x] T004 [US3] Add rail/mobile/theme/language geometry and keyboard checks in the same script (FR-005/006/007).

## Web adapter
- [x] T005 [US1] Rearrange `Shell.tsx`, `CompanySwitcher.tsx`, `ChatPage.tsx` and shell CSS for aligned surfaces and description disclosure (FR-001/002/005).
- [x] T006 [US2] Relocate utilities with `ActionLauncher.tsx` and `ProfileMenu.tsx`; preserve simulation reads (FR-003/004).
- [x] T007 [US3] Apply neutral typography, responsive/rail styles and bounded menus in `tailwind.css` (FR-005/006/007).

## Verify and review
- [x] T008 Update superseded browser/contract expectations; run full required gates and relevant regression browsers (FR-001–007).
- [x] T009 Update `docs/WEB_SPEC.md`, inspect screenshots, review diff and record evidence in `verification.md` (FR-001–007).

T001 precedes T002–T004; tests precede T005–T007; verification follows all changes.
No domain, service or tool work is required by this adapter-only feature.

## Activities consolidation follow-up (FR-008)
- [x] T010 Update navigation contract and shell/browser expectations before implementation.
- [x] T011 Rename the history destination, remove shell-only activity code and update web documentation.
- [x] T012 Run frontend gates and shell/shared-drawer browsers; review dependency removal and record results.

## Action translation regression (FR-007)
- [x] T013 Add failing coverage for all executable discovery labels and translated launcher search.
- [x] T014 Translate the five missing shipping/tracking labels in German, Dutch and Spanish.
- [x] T015 Run frontend gates and launcher browser coverage; review and record results.

## Command palette presentation (FR-009)
- [x] T016 Add keyboard, focus, centering, query reset and placement browser checks.
- [x] T017 Restyle/reposition the existing launcher and add the platform shortcut.
- [x] T018 Verify frontend gates and launcher browsers; inspect visual result and review scope.

## Quiet shell boundaries (FR-010)
- [x] T019 Remove four decorative boundaries while preserving chat divider and active tabs.
- [x] T020 Run frontend gates and existing shell browser; visually review and record evidence.

## Sidebar head grouping (FR-011)
- [x] T021 Update placement contracts and navigation browser expectations.
- [x] T022 Group company controls, refine search field and remove redundant heading.
- [x] T023 Run frontend gates and shell/navigation browsers, inspect and document results.

## Unified tab header (FR-012)
- [x] T024 Update shared header contracts and route/count browser expectations before implementation.
- [x] T025 Integrate tab/action/count slots in the header with compact responsive controls.
- [x] T026 Run frontend gates and shell/introduction/count browsers; review screenshots and record results.

## Commitments header regression (FR-012)
- [x] T027 Update daily-work header expectations, route legacy side tabs through RegisterHeader and preserve counts.
- [x] T028 Verify frontend gates and daily-work browser matrix; review screenshots and record results.

## Inbox consolidation (FR-013)
- [x] T029 Add Inbox route membership tests and adapt browser placement checks.
- [x] T030 Consolidate sidebar and header tabs, retaining local side/rule controls and translations.
- [x] T031 Run frontend/browser gates, review navigation/count behavior and record results.
