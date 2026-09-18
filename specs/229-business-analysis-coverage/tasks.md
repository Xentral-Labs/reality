# Tasks: Business analysis coverage

## Setup and foundations
- [x] T001 Record approved requirements and design in specs/229-business-analysis-coverage/.
- [x] T002 Add failing boundary regressions in packages/reality-core/tests/test_reporting_graph_expansion.py (FR-005/006).
- [x] T003 Repair parent scope and same-table edge direction in packages/reality-core/src/reality/services/analytics/compile_sql.py; validate parents and scoped values in graph_model.py (FR-003/005).

## US1 — Sales, purchase, payments
- [x] T004 [US1] Declare explicit documents/lines, relationships and received measures in packages/reality-core/config/reporting_graph.yaml (FR-001/003).
- [x] T005 [US1] Prove subtype, tenancy, signs and fan-out behavior in packages/reality-core/tests/test_reporting_graph_expansion.py (FR-006).

## US2 — Warehouse and details
- [x] T006 [US2] Declare supported warehouse/terms/partner/account nodes and edges in packages/reality-core/config/reporting_graph.yaml (FR-002/003).
- [x] T007 [US2] Update packages/reality-core/tests/test_reporting_graph_coverage.py and data_model.yaml; prove every new node queries and key links work (FR-006).

## US3 — Discovery
- [x] T008 [US3] Add catalog categories/aliases through domain/reporting_graph.py, services/analytics/graph_model.py and apps/web/src/api.ts (FR-004).
- [x] T009 [US3] Group/search explorer and builder choices in apps/web/src/unified/analytics/{DataExplorer,GraphSteps}.tsx; test via apps/web/scripts/graph-steps.test.mjs (FR-004).

## Verification and documentation
- [x] T010 Update docs/features/analytics.md, docs/WEB_SPEC.md, coverage matrix and generated catalog reference; run backend/web/build/localization/lint/spec/docs checks and Chrome review; record specs/229-business-analysis-coverage/verification.md (FR-001–006).

## Dependencies and strategy
T001 → T002 → T003 → T004/T005 → T006/T007 → T008/T009 → T010.
US1 is the first independently useful slice. UI work follows stable catalog metadata.
No concurrent edits to shared graph declaration; independent read-only research completed.
