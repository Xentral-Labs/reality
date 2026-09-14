# Tasks: Unified Order Entry

## Gates
- [x] T001 Review spec/checklist, resolve scope and Constitution Check in spec.md/plan.md.
- [x] T002 Complete research/data model/contracts and analyze all FR coverage before code.

## US1/US2 — Canonical agreement creation
- [x] T003 [FR-002/003/004/005] Add failing multi-line, validation, source, stale, identity and recovery tests in packages/reality-core/tests/test_unified_order_entry.py.
- [x] T004 [FR-002/004] Extract pure core document/order preview and complete lossless source and attributed snapshot in packages/reality-core/src/reality/services/core.py.
- [x] T005 [FR-003/005] Implement packages/reality-core/src/reality/services/order_actions.py and common delivery_actions.py early dispatch, exact proof and recovery.
- [x] T006 [FR-003/006] Extend web/api.py allowlist and test HTTP/auth/practice plus existing canonical Chat confirmation in tests/test_unified_order_entry.py and tests/test_chat_mcp_orders.py.

## US3 — Shared order entry
- [x] T007 [FR-001/006/007] Add failing apps/web/scripts/unified-order-entry-browser.mjs for all entry points, line editing and localized layouts.
- [x] T008 [FR-001/006/007] Build apps/web/src/unified/OrderCard.tsx; connect api.ts, ActionCard.tsx, OrdersPage.tsx, UnifiedApp.tsx, ActionLauncher.tsx, ChatPage.tsx, DecisionsPage.tsx and localization.tsx.
- [x] T009 [FR-003/005/006] Verify reload/edit/reject, exact confirmation, unknown recovery, observations and downstream links in the new browser proof.

## Completion
- [x] T010 Run full backend, frontend contracts/build/i18n/format, new and existing action browsers, spec/Ruff/diff; record results in quickstart.md.
- [x] T011 Review all FRs and update docs/WEB_SPEC.md, docs/V0_CHECKLIST.md, docs/SPEC_COVERAGE_MATRIX.md, docs/ideas/unified-capability-inventory.md; restart shared preview and verify reads only.

## Dependencies and coverage
T001/T002 precede code; T003 before T004–T006; T007 before T008/T009; all precede T010/T011.
FR-001: T007/T008; FR-002: T003/T004; FR-003: T003/T005/T006/T009;
FR-004: T003/T004; FR-005: T003/T005/T009; FR-006: T006–T009; FR-007: T007/T008/T010.
Backend and browser test authoring are independently parallelizable, but implementation is sequential.
Analyze: all seven requirements and three stories covered; no critical findings, no ambiguous scope,
no new schema and no Constitution exceptions. Requirements checklist: 6/6 satisfied.
