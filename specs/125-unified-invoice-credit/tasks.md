# Tasks
- [x] T001 [US1/US2] [FR-001–004] Add failing tests in packages/reality-core/tests/test_unified_invoice_credit.py for capacity, no-return, netting, provenance, atomicity, stale/concurrent work and exact recovery.
- [x] T002 [US1] [FR-001–003] Implement private credit context/preview/recording in packages/reality-core/src/reality/services/credit_actions.py; extend core.py typed target validation/legacy entitlement/command shape and shared lock coverage.
- [x] T003 [US2] [FR-004] Implement review/proof/recovery routing in services/credit_actions.py and services/delivery_actions.py; preserve Playground readers and exact existing tool policy.
- [x] T004 [US1] [FR-002/005] Add Inspector typed position traversal in services/delivery_reads.py and web/api.py, then expose web/api.py context/prepare shape and mcp/catalog.py existing proposal schema; update application catalog artifacts only when required by signature.
- [x] T005 [US1/US2] [FR-005] Add apps/web/scripts/unified-credit-entry-browser.mjs proof before UI; implement CreditCard.tsx, api.ts, FinancePage/UnifiedApp/ActionCard/ActionLauncher/ChatPage/DecisionsPage and localization.tsx.
- [x] T006 [FR-001–005] Run complete backend/web/browser checks and final review; update docs/WEB_SPEC.md, SPEC_COVERAGE_MATRIX.md, V0_CHECKLIST.md and capability inventory only after green.
Service paths are under packages/reality-core/src/reality; UI paths under apps/web/src/unified. Dependencies T001→T002→T003→T004→T005→T006. Tests cover every FR through T001/T005 and implementation through T002–005.
