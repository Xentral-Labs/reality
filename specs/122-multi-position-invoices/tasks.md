# Tasks: Multi-position invoices
## Foundation
- [x] T001 Add failing FR-002–005 proofs in packages/reality-core/tests/test_multi_position_invoices.py.
## US1 — Multi-position entry
- [x] T002 [US1] Implement FR-002/003/005 core input, pure preview and atomic writer in packages/reality-core/src/reality/services/core.py; expose both shapes in mcp/catalog.py.
## US2 — Review and recovery
- [x] T003 [US2] Implement FR-004/005 plural snapshots, overlap guard and exact N-line proof in packages/reality-core/src/reality/services/invoice_actions.py.
## Shared interface
- [x] T004 [US1] Add FR-001/006 browser proof in apps/web/scripts/unified-invoice-entry-browser.mjs before adapter updates.
- [x] T005 [US1] Implement FR-001/006 multi-position editor and review in apps/web/src/unified/InvoiceCard.tsx, api.ts and localization.tsx.
## Verification and review
- [x] T006 Verify FR-001–006 with complete core/web/browser gates, final review and update docs/WEB_SPEC.md, docs/SPEC_COVERAGE_MATRIX.md, docs/V0_CHECKLIST.md and capability inventory.
Dependencies: T001 → T002 → T003; T004 → T005; T006 after all. Browser fixture work may proceed independently of core work. US1 proves one invoice with multiple lines; US2 independently proves exact recovery and legacy compatibility. Complete both before release.
