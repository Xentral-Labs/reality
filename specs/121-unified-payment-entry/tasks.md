# Tasks: Unified Payment Entry

## Foundation and failing proof
- [x] T001 [FR-002/003/004/005] Add failing service and HTTP proofs in `packages/reality-core/tests/test_unified_payment_entry.py`; update reviewed confirmations in `tests/test_finance_payment_atomicity.py`.
## US1 — Record and allocate payment
- [x] T002 [US1] [FR-002/004] Share pure validation and serialization locks in `packages/reality-core/src/reality/services/core.py`.
## US2 — Safe shared review and recovery
- [x] T003 [US2] [FR-003/005] Implement `services/payment_actions.py`, common dispatch in `services/delivery_actions.py` and prepare allowlist in `web/api.py`.
## UI for both stories
- [x] T004 [US1] [FR-001/006/007] Add browser proof in `apps/web/scripts/unified-payment-entry-browser.mjs` before building its adapter.
- [x] T005 [US1] [FR-001/006/007] Implement `apps/web/src/unified/PaymentCard.tsx`, Finance/global/Chat/Decisions integration, api.ts and localization.tsx.
## Final verification and review
- [x] T006 [FR-001/002/003/004/005/006/007] Run full core/web/browser/spec/lint gates and final review; update `docs/WEB_SPEC.md`, `docs/V0_CHECKLIST.md`, `docs/SPEC_COVERAGE_MATRIX.md` and capability inventory only with passing evidence.

Dependencies: T001 → T002 → T003; T004 precedes T005; T006 follows all work.
US1 proves partial/full settlement; US2 proves stale/replay/reversal/unknown safety.
Browser fixture authoring may run independently of core work. Freeze core source before full tests.
