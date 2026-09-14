# Tasks: Unified Orders and Deliveries

## Gates
- [x] T001 Review spec, research and Constitution; analyze traceability before implementation.

## US1 — Delivery register
- [x] T002 [US1] [FR-002 FR-004 FR-006] Add failing packages/reality-core/tests/test_unified_orders_api.py tests for direction, revisions, corrections, exact order/line scope and API validation.
- [x] T003 [US1] [FR-002 FR-004] Extend services/delivery_reads.py and web/api.py; preserve customer defaults and case boundary.
- [x] T004 [US1] [FR-001 FR-006] Add failing route/browser contracts in apps/web/scripts/unified-app-contract.test.mjs and unified-orders-browser.mjs.

## US2/US3 — Order investigation and execution entry
- [x] T005 [US2] [FR-003 FR-004] Add order-type/paging tests in test_unified_orders_api.py and order drilldown in unified-orders-browser.mjs before UI.
- [x] T006 [US1] [US2] [FR-001 FR-002 FR-003 FR-004] Add apps/web/src/unified/OrdersPage.tsx, typed api.ts register and routing.ts/Shell.tsx/UnifiedApp.tsx/CaseAssistant.tsx wiring.
- [x] T007 [US3] [FR-005 FR-006] Wire existing customer cases and Inspector; test keyboard/reload, supplier boundary, retry/empty/company reset and no writes in unified-orders-browser.mjs.
- [x] T008 [US1] [FR-007] Translate apps/web/src/localization.tsx and verify48 visual combinations.

## Completion
- [x] T009 Run all backend/web/browser/docs gates and authenticated sample proof; record review in quickstart.md.
- [x] T010 Update docs/WEB_SPEC.md, WEB_UX_MATRIX.md, SPEC_COVERAGE_MATRIX.md and apps/docs/content/product-guides/daily-control.md; update V0 only when required checks pass.

## Dependencies and coverage
T001 → T002/T004/T005 failing proof → T003 → T006/T007 → T008 → T009/T010.

| Requirement | Tests | Implementation |
| --- | --- | --- |
| FR-001 | T004 | T006 |
| FR-002 | T002 | T003 T006 |
| FR-003 | T005 | T006 |
| FR-004 | T002 T005 | T003 T006 |
| FR-005 | T007 | T007 |
| FR-006 | T002 T004 T007 | T006 T007 |
| FR-007 | T008 | T008 |
