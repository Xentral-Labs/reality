# Tasks: Unified Invoice Entry

## Foundation and failing proof
- [x] T001 [FR-002/003/004/005] Add failing isolated service and adapter tests in `packages/reality-core/tests/test_unified_invoice_entry.py`.
## US1 — Record invoice evidence
- [x] T002 [US1] [FR-002/004] Share pure validation and attributed invoice receipt in `packages/reality-core/src/reality/services/core.py`; register event in `config/business_event_catalog.yaml`.
## US2 — Reliable shared review
- [x] T003 [US2] [FR-003/005] Add invoice proof/review/guard in `services/invoice_actions.py`; common dispatch in `services/delivery_actions.py` and `web/api.py`.
## UI integration for both stories
- [x] T004 [US1] [FR-001/006/007] Add failing browser journey in `apps/web/scripts/unified-invoice-entry-browser.mjs`.
- [x] T005 [US1] [FR-001/006/007] Implement `apps/web/src/unified/InvoiceCard.tsx`, shared entry dispatch, Finance entry, api types and localization.
## Cross-cutting verification
- [x] T006 [FR-001/002/003/004/005/006/007] Run complete core/web/action browser/spec/lint gates, review diff and update `docs/WEB_SPEC.md`, `docs/SPEC_COVERAGE_MATRIX.md`, `docs/V0_CHECKLIST.md`.

Dependencies: T001 → T002 → T003; T004 precedes T005; T006 follows all implementation.
US1 independently proves exact atomic invoice creation; US2 proves stale/replay/unknown safety.
Browser fixture authoring and service implementation may run independently; no concurrent source
edits during full-suite execution. Deliver both stories together before exposing local entry.
