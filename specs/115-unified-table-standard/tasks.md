# Tasks
- [x] T001 Review spec/plan/research and Constitution in specs/115-unified-table-standard/.
- [x] T002 [US3] [FR-005 FR-006] Add failing global sort/size/invalid-key tests in packages/reality-core/tests/test_unified_table_queries.py.
- [x] T003 [US3] [FR-005 FR-006] Implement db/query_order.py and ordering in services/delivery_reads.py, services/reference_workspace.py, web/read_models.py, web/warehouse_reads.py, web/fact_reads.py, web/source_reads.py and web/api.py.
- [x] T004 [US1] [US2] [FR-001 FR-002 FR-003 FR-004 FR-007] Add preference/URL contracts and browser geometry/action coverage in apps/web/scripts/unified-table-contract.test.mjs and unified-tables-browser.mjs.
- [x] T005 [US1] [US2] [FR-001 FR-002 FR-003 FR-004] Build apps/web/src/unified/RegisterTable.tsx, tablePreferences.ts and shared CSS in apps/web/src/tailwind.css.
- [x] T006 [US1] [US3] [FR-001 FR-002 FR-003 FR-005 FR-006] Migrate OrdersPage.tsx, WarehousePage.tsx, FinancePage.tsx, MasterDataPage.tsx, FactsPage.tsx, DataSourcesPage.tsx; thread api.ts/routing.ts/UnifiedApp.tsx table state.
- [x] T007 [US2] [FR-004 FR-007] Localize structural copy in apps/web/src/localization.tsx; verify browser persistence, variants, dimensions and languages.
- [x] T008 Run complete backend/frontend/browser/docs gates and final review; record specs/115-unified-table-standard/quickstart.md.
- [x] T009 Update docs/WEB_SPEC.md, WEB_UX_MATRIX.md, SPEC_COVERAGE_MATRIX.md and V0_CHECKLIST.md after green checks.

All FRs map to test tasks T002/T004/T007 and implementation T003/T005/T006/T007. Dependencies: T001 → T002/T004 → T003/T005 → T006 → T007 → T008 → T009.
