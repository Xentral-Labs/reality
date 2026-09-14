# Tasks: Integration preparation catalog

## Setup and foundation
- [x] T001 Review accepted scope and record Constitution PASS in specs/144-integrations-catalog/plan.md.
- [x] T002 Write failing browser proof in apps/web/scripts/integrations-catalog-browser.mjs for FR-001–006.

## US1: Find a provider
- [x] T003 [US1] Add categorized searchable catalog in apps/web/src/unified/IntegrationPreparation.tsx (FR-001/004).

## US2: Prepare an instance
- [x] T004 [US2] Implement validated native modal and scoped session draft lifecycle in apps/web/src/unified/IntegrationPreparation.tsx (FR-002/003/004).
- [x] T005 [US2] Pass user ID from apps/web/src/unified/UnifiedApp.tsx and integrate the preparation surface in DataSourcesPage.tsx (FR-003).

## US3: Preserve source inspection
- [x] T006 [US3] Retain source register/CSV/record routes separately in apps/web/src/unified/DataSourcesPage.tsx (FR-005).

## Polish and review
- [x] T007 Translate new UI in apps/web/src/localization.tsx and validate modal/mobile/theme behavior (FR-006).
- [x] T008 Run planned gates, update docs/WEB_SPEC.md and record evidence in specs/144-integrations-catalog/quickstart.md (FR-001–006).

## Dependencies and strategy
T001 → T002 → T003 → T004 → T005/T006 → T007 → T008. Sequential implementation; translation and documentation could be prepared independently once copy stabilizes. MVP is provider choice, extended by session preparation, with existing source access preserved throughout.

- [x] T009 Restore shared footer for non-selectable registers in apps/web/src/unified/RegisterTable.tsx; prove both source tabs in apps/web/scripts/unified-sources-browser.mjs (FR-007).

- [x] T010 Add service/browser regressions, source-linked Inspector sections in packages/reality-core/src/reality/services/delivery_reads.py, two-tab navigation in apps/web/src/unified/DataSourcesPage.tsx and translations; verify scoped reads and preserved document URLs (FR-008).
