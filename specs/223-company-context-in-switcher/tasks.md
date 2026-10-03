# Tasks

## Setup and foundational review

- [x] T000 Review user scope and Constitution in specs/223-company-context-in-switcher/spec.md and plan.md.

## US1 - Company management and the simulation leave the navigation

- [x] T001 [US1] Update the navigation assertions in apps/web/scripts/demo-live-browser.mjs and apps/web/scripts/retirement-browser.mjs to the switcher footer and the integrations card, before implementation.
- [x] T003 [US1] Remove the Companies and Demo Data entries in apps/web/src/unified/Shell.tsx; add the simulation state line and the Manage companies / New company footer in apps/web/src/unified/CompanySwitcher.tsx and apps/web/src/tailwind.css.

## US2 - The creation form has an address

- [x] T002 [US2] Add `new` to the settings section union and allow-list in apps/web/src/unified/routing.ts.
- [x] T004 [US2] Drive the creation form from the address in apps/web/src/unified/SettingsPage.tsx and apps/web/src/unified/CompanySettings.tsx.

## US3 - The simulation joins the systems

- [x] T005 [US3] Add apps/web/src/unified/DemoDataSource.tsx and render it in apps/web/src/unified/DataSourcesPage.tsx with the company passed from apps/web/src/unified/UnifiedApp.tsx.

## Verification and review

- [x] T006 Add the new strings to German, Dutch and Spanish in apps/web/src/localization.tsx; update docs/WEB_SPEC.md; run the gates and record the result in specs/223-company-context-in-switcher/review.md.

## Dependencies and execution

T000 → T001/T002 → T003/T004/T005 → T006. Assertions first; routing before the form
that reads it; the card after the company reaches the integrations page.

## Current-company settings refinement

- [x] T007 [US1] Add routing and presentation regression contracts for FR-006–008 before implementation in apps/web/scripts/unified-app-contract.test.mjs; update retirement-browser.mjs overview label.
- [x] T008 [US1] Add the current settings destination, sidebar entry, scoped company cards, page context and four-language labels in routing.ts, Shell.tsx, CompanySwitcher.tsx, SettingsPage.tsx, CompanySettings.tsx, pageIntroduction.ts, commandPaletteTargets.ts, CompanyDangerZone.tsx and localization.tsx (FR-006–008).
- [ ] T009 Verify frontend contracts, localization, build, formatting and spec checks; update docs/WEB_SPEC.md and review.md (FR-006–008).

- [x] T010 Apply the user-approved removal of the duplicate company-name line (FR-008); update the existing presentation/browser assertions and verify the focused contract suite.
