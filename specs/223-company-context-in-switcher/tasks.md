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
