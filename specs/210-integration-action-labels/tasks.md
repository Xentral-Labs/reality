# Tasks: Visible integration actions

## Setup and foundation
- [x] T001 Record approved scope, reviewed requirements and Constitution PASS in specs/210-integration-action-labels/spec.md and plan.md.

## US1 - Choose the intended action
Independent proof: sources browser fixtures expose four visible labels and unchanged destinations.
- [x] T002 [US1] Add and observe failing rendered-label regression in apps/web/scripts/unified-sources-browser.mjs (FR-001–003).
- [x] T003 [US1] Add shared labeled presentation in apps/web/src/unified/RegisterTable.tsx and apps/web/src/tailwind.css (FR-003–004).
- [x] T004 [US1] Enable source/record labels in apps/web/src/unified/DataSourcesPage.tsx and translations in apps/web/src/localization.tsx (FR-001–002).
- [x] T005 [US1] Verify all destinations, both densities and localized layouts in apps/web/scripts/unified-sources-browser.mjs; update apps/web/scripts/unified-source-configuration-browser.mjs selectors (FR-001–004).

## Verification and review
- [x] T006 Update docs/WEB_SPEC.md, run gates from plan.md and record results/diff review in specs/210-integration-action-labels/verification.md (FR-001–004).

## Dependencies and delivery
T001 → T002 → T003 → T004 → T005 → T006. One coherent user story is the MVP. No parallel implementation is needed; independent validation commands may run concurrently after implementation.
