# Tasks: Data Model Explorer

## Setup and foundation
- [x] T001 Review accepted scope and source contracts in specs/175-docs-data-model/spec.md and research.md (FR-001–FR-006).
- [x] T002 Add schema parity and semantic contract tests in apps/docs/scripts/test_data_model_reference.py and data-model.test.mjs; observe failure (FR-001–FR-006).

## User Story 1: Find the right place
Independent test: nine objects explain their business authority with bilingual example excerpts.
- [x] T003 [US1] Add business annotations and metadata generator in apps/docs/scripts/data_model_reference.py (FR-001, FR-004).

## User Story 2: Inspect real fields
Independent test: exact schema parity; all action references resolve.
- [x] T004 [US2] Integrate generated complete fields and relationships into apps/docs/scripts/generate-catalog-reference.py and apps/docs/Dockerfile (FR-002, FR-003, FR-006).
- [x] T005 [US2] Render meanings, storage requirements, defaults and derived values in apps/docs/.vitepress/theme/components/DataModelExplorer.vue (FR-002–FR-004).

## User Story 3: Read and navigate
Independent test: bilingual direct links, query and Back preserve model context; small screen text wraps.
- [x] T006 [US3] Integrate tab/search/history in apps/docs/.vitepress/theme/components/ToolUsage.vue (FR-005).
- [x] T007 [US3] Link both handbook overviews and summary to the explorer in apps/docs/content/ (FR-006).

## Verification and review
- [x] T008 Run required focused tests, docs build, formatting, schema generation, spec gates; record evidence in specs/175-docs-data-model/verification.md (FR-001–FR-006).
- [x] T009 Review final diff and rebuild the docs preview on 8083; record limits in specs/175-docs-data-model/verification.md (FR-001–FR-006).

## Dependencies and strategy
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009. No parallel implementation required. US1 metadata is the first increment; US2 renders it; US3 completes navigation. Independent read-only source research can run alongside specification work.

## Approved ERP expansion
- [x] T010 [US2] Expand schema coverage expectations and semantic assertions in apps/docs/scripts/test_data_model_reference.py and data-model.test.mjs; observe missing ERP records (FR-007/008).
- [x] T011 [US2] Add researched ERP objects, field meanings, examples and group metadata in apps/docs/scripts/data_model_reference.py (FR-007).
- [x] T012 [US3] Add group navigation and global search in apps/docs/.vitepress/theme/components/DataModelExplorer.vue; update handbook entry links and browser scenarios (FR-008).
- [x] T013 Verify documentation gates, review meanings, run browser checks and rebuild 8083; append evidence in specs/175-docs-data-model/verification.md (FR-007/008).

Expansion dependency: T010 → T011 → T012 → T013. Existing completed tasks remain the verified first increment.

## Field table presentation
- [x] T014 [US2] Add semantic field-table contract and update browser expectations in apps/docs/scripts/data-model.test.mjs and model-browser-check.mjs (FR-009).
- [x] T015 [US2] Render all six field columns with wrapping and a keyboard-scrollable region in apps/docs/.vitepress/theme/components/DataModelExplorer.vue (FR-009).
- [x] T016 Verify docs gates and desktop/mobile navigation, rebuild 8083 and record evidence in verification.md (FR-009).

Order: T014 → T015 → T016.

## Unified visual system
- [x] T017 Add shared-style/header/table-preservation contracts in apps/docs/scripts/data-model.test.mjs (FR-010).
- [x] T018 Implement feature-scoped shared styles, tab headers and compact model guidance in apps/docs/.vitepress/theme/tool-usage.css, index.ts and both explorer components (FR-010).
- [x] T019 Verify all four tabs, themes/locales, responsive navigation and table behavior; build 8083 and record evidence in verification.md (FR-010).

Order: T017 → T018 → T019.

## Compact header and search

- [x] T020 Implement short bilingual search labels and scoped responsive navigation/focus CSS in config.mts and theme/custom.css (FR-011).
- [x] T021 Verify docs tests/build, rendered bilingual headers at mobile/tablet/desktop widths and search focus/keyboard interaction in both themes; review diff and record evidence (FR-011).
