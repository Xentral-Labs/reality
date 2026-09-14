# Tasks: Unified financial reversal
## Foundation
- [x] T001 Add failing FR-002–005 tests in packages/reality-core/tests/test_unified_financial_reversal.py.
## US1 — Reviewed reversal
- [x] T002 [US1] Implement FR-001/002/004 private choices/effects in services/financial_reversal_actions.py and attribution in services/core.py, tools/application.py and web/api.py.
## US2 — Safe shared lifecycle
- [x] T003 [US2] Implement FR-003/005 review/proof/overlap in services/financial_reversal_actions.py, services/delivery_actions.py and services/payment_actions.py.
## Shared UI
- [x] T004 [US1] Add FR-001/006 browser proof in apps/web/scripts/unified-financial-reversal-browser.mjs before adapter implementation.
- [x] T005 [US1] Implement FR-001/006 apps/web/src/unified/FinancialReversalCard.tsx, FinancePage.tsx, ActionCard.tsx, ActionLauncher.tsx, UnifiedApp.tsx, ChatPage.tsx, DecisionsPage.tsx, api.ts and localization.tsx.
## Verification and review
- [x] T006 Verify FR-001–006 through complete core/web/browser gates and final review; update docs/WEB_SPEC.md, docs/SPEC_COVERAGE_MATRIX.md, docs/V0_CHECKLIST.md and capability inventory.
Dependencies: T001 → T002 → T003; T004 → T005; T006 follows all. Browser fixtures may be authored independently of core. US1 proves inverse/effects; US2 proves stale/recovery/authorization. No source/test edits during the full core suite.
