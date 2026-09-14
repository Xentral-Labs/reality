# Tasks: Customer refunds from open credits
## Design gates
- [x] T001 Review approved scope and requirements in spec.md; Constitution PASS in plan.md.
- [x] T002 Analyze spec/plan/tasks: all 10 requirements mapped, no ambiguity, duplication or critical findings.
## Test-first service work
- [x] T003 [US1] [FR-001, FR-002, FR-003, DR-001, DR-002, DR-003] Add partial/netting/precision/tenant/atomicity proofs in packages/reality-core/tests/test_unified_customer_refund.py; observe failing shared refund preparation.
- [x] T004 [US2] [FR-004, FR-005, FR-007] Add stale/unresolved/concurrent/proof-corruption/recovery/reversal tests in packages/reality-core/tests/test_unified_customer_refund.py.
- [x] T005 [US1] [FR-001, FR-002, FR-003, DR-001, DR-002, DR-003] Implement preview and locked canonical refund validation in packages/reality-core/src/reality/services/core.py and business_locks.py.
- [x] T006 [US2] [FR-004, FR-005, FR-007] Extend payment_actions.py, delivery_actions.py and financial_reversal_actions.py for exact refund proof, overlap and recovery, preserving adjacent actions.
## Shared UI
- [x] T007 [US3] [FR-006, FR-007, DR-003] Add HTTP proof in tests/test_unified_customer_refund.py and browser coverage in apps/web/scripts/unified-refund-entry-browser.mjs.
- [x] T008 [US3] [FR-006, FR-007, DR-001] Add API allowlist/types and RefundCard.tsx; wire FinancePage/UnifiedApp/ActionCard/ActionLauncher/ChatPage/DecisionsPage; translate in apps/web/src/localization.tsx.
## Verification and review
- [x] T009 [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, DR-001, DR-002, DR-003] Run focused and complete backend, web build/contracts/i18n/format/browser and adjacent regression gates; root lint/spec/diff checks.
- [x] T010 Review exact source/evidence/ledger/allocation links, no schema changes, rollback and final diff; update docs/WEB_SPEC.md, docs/SPEC_COVERAGE_MATRIX.md, docs/V0_CHECKLIST.md and docs/ideas/unified-capability-inventory.md only with verified results.
## Dependencies
T003/T004 before T005/T006; T007 before T008. Domain/service then tool/API then UI. T009 only after code freeze; T010 after green checks.
## Requirement Coverage
| Requirement | Test tasks | Implementation tasks |
|---|---|---|
| FR-001, FR-002, FR-003, DR-002 | T003 | T005 |
| DR-001 | T003, T007 | T005, T008 |
| DR-003 | T003, T007 | T005, T008 |
| FR-004, FR-005 | T004 | T006 |
| FR-006 | T007 | T008 |
| FR-007 | T004, T007 | T006, T008 |
