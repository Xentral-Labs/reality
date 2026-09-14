# Tasks: Unified Warehouse and Attention

## Gates
- [X] T001 Review spec/plan/requirements checklist and analyze eight requirements before implementation.

## US1 — Warehouse
- [X] T002 [US1] [FR-002 FR-003 FR-005 FR-007] Add failing exact-item/stock/correction/foreign/no-effect tests in packages/reality-core/tests/test_unified_operations_api.py.
- [X] T003 [US1] [FR-002 FR-003 FR-005 FR-007] Extend exact-item filters in web/read_models.py and implement web/warehouse_reads.py with typed GET adapter in web/api.py.

## US2 — Attention
- [X] T004 [US2] [FR-004 FR-005 FR-007] Add canonical/filter/resolved/foreign tests in packages/reality-core/tests/test_attention_reads.py and API tests; register test families in docs/SPEC_COVERAGE_MATRIX.md.
- [X] T005 [US2] [FR-004 FR-005 FR-007] Implement services/attention_reads.py and strict GET adapters in web/api.py.

## US3 — One App
- [X] T006 [US3] [FR-001 FR-005 FR-006 FR-007 FR-008] Add route contracts and apps/web/scripts/unified-operations-browser.mjs for traversal, URL recovery, company isolation and visual/keyboard states.
- [X] T007 [US3] [FR-001 FR-002 FR-003 FR-005 FR-006 FR-008] Build apps/web/src/unified/WarehousePage.tsx; API types, routes, sidebar, delivery and item links.
- [X] T008 [US3] [FR-001 FR-004 FR-005 FR-006 FR-007 FR-008] Build AttentionPage.tsx, Home entry and preserved legacy review paths.
- [X] T009 [US3] [FR-008] Complete localization.tsx and run four-language, two-theme, two-width visual/keyboard review.

## Completion
- [X] T010 Run full backend/frontend/browser/docs, lint/spec and diff gates; record quickstart.md evidence and technical review.
- [X] T011 Update docs/WEB_SPEC.md, WEB_UX_MATRIX.md and product guide; record technical completion separately from owner acceptance and retirement.

## Requirement Coverage
| Requirement | Tests | Implementation |
| --- | --- | --- |
| FR-001 | T006 | T007, T008 |
| FR-002, FR-003 | T002, T006 | T003, T007 |
| FR-004 | T004, T006 | T005, T008 |
| FR-005 | T002, T004, T006 | T003, T005, T007, T008 |
| FR-006 | T006 | T007, T008 |
| FR-007 | T002, T004, T006 | T003, T005, T008 |
| FR-008 | T006, T009 | T007, T008, T009 |

- [x] T009 Add explanation card and shared catalog company context; verify FR-009 browser and frontend gates.
