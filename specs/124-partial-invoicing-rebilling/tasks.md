# Tasks: Partial invoicing and rebilling
## Foundation
- [x] T001 Add failing FR-001–004/006 tests in packages/reality-core/tests/test_partial_invoicing_rebilling.py; revise superseded no-repeat assertions in test_unified_invoice_entry.py and test_multi_position_invoices.py.
## US1 — Remaining quantity
- [x] T002 [US1] Implement FR-001/002/003 shared billing derivation/guards in services/core.py and serialization in services/business_locks.py.
## US2 — Reversal and history
- [x] T003 [US2] Implement FR-003/004/006 billing snapshots in services/invoice_actions.py and projected reversal billing in services/financial_reversal_actions.py.
## Shared UI
- [x] T004 [US1] Add FR-005 browser proofs in apps/web/scripts/unified-invoice-entry-browser.mjs and unified-financial-reversal-browser.mjs before UI edits.
- [x] T005 [US1] Implement FR-005 Inspector fields in web/api.py and apps/web/src/api.ts, InvoiceCard.tsx, FinancialReversalCard.tsx and localization.tsx.
## Verify/review
- [x] T006 Verify FR-001–006 with complete core/web/browser gates and final review; update docs/WEB_SPEC.md, docs/SPEC_COVERAGE_MATRIX.md, docs/V0_CHECKLIST.md and capability inventory.
Paths under services/ and web/ are relative to packages/reality-core/src/reality/; UI cards are under apps/web/src/unified/. Dependencies: T001→T002→T003, T004→T005, T006 after all. Browser proof authoring is independent of core work. US1 proves partial/remainder; US2 proves reversal/rebilling and historical receipts.
