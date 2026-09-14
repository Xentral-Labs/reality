# Tasks
- [x] T001 Specify/review FR-001..004 and Constitution; no open clarification.
- [x] T002 Add table browser acceptance for footer, selection/export/reset before implementation.
- [x] T003 Implement compact workspaces, consistent action placement and shared table footer (FR-001..004).
- [x] T004 Verify planned checks and visually review; record evidence.

- [x] T005 Implement FR-005 shared header/toolbar/action-menu arrangement, update affected browser entry/geometry expectations, verify and review.

- [x] T006 Implement FR-006 actual-header portal and compact filter dropdowns; verify header ancestry, native filter/density controls and localized layouts.

- [x] T007 Implement FR-007 consistent Inspector/Company header placement and verify header uniqueness, existing navigation and localized browser layouts.

- [x] T008 Apply FR-008 Commitments label and explanatory hint; verify frontend checks.

## FR-009 Page introductions
- [x] T009A Add route/subview introduction coverage tests in apps/web/scripts/page-introduction.test.mjs and observe failure.
- [x] T009B Implement shared descriptions/header fallback, remove duplicated page introductions, preserve contextual help in apps/web/src/unified and translate all text in localization.tsx.
- [x] T009C Verify contracts, build, localization, formatting, spec policy and desktop/mobile layout; review diff and record evidence.

- [x] T009D Refine FR-009 to the approved compact information box; update browser geometry assertions, verify responsive layouts/build, and update PR 168.

- [x] T010A Cover FR-010 header/subview and action placement in existing frontend/browser tests.
- [x] T010B Implement two-line global header, action portals and remove duplicate introductions.
- [x] T010C Verify populated desktop/mobile pages, unchanged action flows, build/contracts/i18n/spec and review; update PR 168 and local web.

- [x] T010D Move the shared introduction/actions to the first middle-content surface; restore compact top header and verify responsive placement and unchanged actions.

- [x] T011 Style global-header subview controls as underlined tabs; verify selected geometry, desktop/mobile layout and existing switching; update PR 168.

- [x] T012 Normalize outer content corners and remove embedded activity company label; verify build/contracts and browser appearance.

- [x] T013 Keep page register footers at the viewport bottom; verify populated Finance geometry and frontend checks.

FR-013 verification: TypeScript/Vite build, 61 contracts and spec policy passed. register-footer-browser.mjs passed three Finance views at desktop/mobile widths with 50 rows: footer bottom within viewport, independent row scroll, stable footer position and no horizontal document overflow. Local frontend rebuilt on port 8080.

FR-013 full-width refinement verified: all three Finance views at 1440px/390px with 50 scrollable rows; exact footer/main left and right alignment and viewport bottom alignment; desktop chat open/closed transitions; unchanged scroll position of footer. Build/contracts/spec checks passed.

- [x] T014 Remove six redundant page notes, preserve contextual indicators, verify frontend checks and submit separate PR.

FR-014 verification: focused diff reviewed at all six locations; TypeScript/Vite build, 61 frontend contracts, Prettier and spec policy passed. Reports observation time and contextual errors/limitations remain.

- [x] T015 Split Sales/Purchasing navigation and tabs; verify direction, reload and frontend/browser checks.

FR-015 verification: production build, 62 frontend contracts, four-language audit, formatting and spec policy passed. Browser checks passed customer/supplier tabs, delivery direction, reload and desktop/mobile layout.

- [x] T016 Replace timezone text input with a real select and verify profile persistence.

FR-016 verification: build, 62 frontend contracts, i18n audit and spec policy passed. PROFILE_ONLY browser checks passed selection/save/reload, rejection and recovery. Broader pre-existing member-management fixture is blocked by an open Manage users dialog and is not claimed verified.
