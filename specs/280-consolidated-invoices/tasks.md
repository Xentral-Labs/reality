# Tasks: Consolidated invoices across orders

Tests come before the implementation they prove. Paths are relative to the repository root.

## Foundation — failing proofs

- [ ] T001 [US1][US2] Write failing FR-001/FR-002 service proofs in
  `packages/reality-core/tests/test_consolidated_invoices.py`: supplier invoice over two
  purchase orders and sales invoice over three orders record one source, one invoice, one line
  per position and one posting group at the stated total; another party, another currency and
  another direction are refused before any write; a failing later position leaves nothing;
  201 positions are refused (FR-010).
- [ ] T002 [US1][US2] Rewrite `test_invalid_is_inert[mixed]` in
  `packages/reality-core/tests/test_multi_position_invoices.py` to the new rule (same party,
  other order accepted; other party refused).
- [ ] T003 [US1] Write failing FR-003 proofs in `test_consolidated_invoices.py`: per order line,
  billed + remaining equals ordered before and after the invoice and after its reversal;
  `shipped_not_billed` and `billed_not_received` clear per line.

## US1/US2 — Core entry

- [ ] T004 [US1][US2] Implement FR-001/FR-002 in
  `packages/reality-core/src/reality/services/core.py` `_preview_order_invoice`: replace the
  same-order refusal with direction/party/currency refusals and the FR-010 bound; add
  `orders[]` to the preview; declare `maxItems: 200` for `lines` in `mcp/catalog.py`.
- [ ] T005 [US3] Write failing FR-007/FR-009 review proofs in
  `packages/reality-core/tests/test_consolidated_invoices.py`: review lists every order; a
  change to any selected position makes the review stale; recovery verifies the exact N-line
  receipt; a legacy single-order proposal hashes and verifies unchanged; a commitment
  cancelled between review and confirmation makes the review stale and nothing is written.
- [ ] T006 [US3] Implement FR-007/FR-009 in
  `packages/reality-core/src/reality/services/invoice_actions.py` `_review_invoice`
  (`state.orders`, `state.party` from the preview, per-position item; `state.order` kept for
  the single shape).

## US2 — Readiness and payment matching

- [ ] T007 [US2] Write failing FR-004 proofs in
  `packages/reality-core/tests/test_fulfillment_readiness.py`: consolidated invoice open →
  blocker `prepayment_consolidated_invoice_open` naming invoice and open amount; paid in part →
  still blocked; settled in full → released. Rewrite
  `test_cross_order_invoice_attribution_blocks_without_guessing` accordingly.
- [ ] T008 [US2] Implement FR-004 in
  `packages/reality-core/src/reality/services/fulfillment_readiness.py` (rule, detail, links)
  and add the code to `DELIVERY_BLOCKER_TYPES` in `services/projections.py`; update
  `tests/test_incremental_derivation.py` blocker list.
- [ ] T009 [US2] Write failing FR-005 proof in
  `packages/reality-core/tests/test_payment_intake.py`: a payment naming one order of a
  consolidated invoice is a candidate with the stated reason, not an allocation; the invoice
  reference still allocates.
- [ ] T010 [US2] Implement FR-005 in
  `packages/reality-core/src/reality/services/payment_intake.py` `resolve_references`.

## FR-006 — Billable positions read

- [ ] T011 [US1][US2] Write failing read proofs in
  `packages/reality-core/tests/test_invoice_billable_positions.py`: grouping by order,
  exclusion of fully billed and cancelled lines, party/currency scope, tenant isolation,
  limit with truthful total, HTTP and MCP parity, and a statement count that does not grow
  per order line.
- [ ] T012 [US1][US2] Implement `billable_positions` in
  `packages/reality-core/src/reality/services/invoice_billing.py` (move `_order_line_billing`
  there, re-export from core); register MCP read `invoice_billable_positions` in
  `mcp/catalog.py` and `tools/application.py`; add HTTP route in `web/api.py`.
- [ ] T013 Complete the new-surface gates: `config/tenant_isolation_catalog.yaml` and pinned
  counts, MCP topic and capability guidance, `config/resource_catalog.yaml` (`labels.de`),
  `config/command_catalog.yaml` read entry and invoice effect texts; run `make docs-generate`.

## US3 — Web and Inspector

- [ ] T014 [US3] Write failing FR-008 Inspector proof in
  `packages/reality-core/tests/test_consolidated_invoices.py`: invoice Inspector groups
  referenced positions by order and links each order; each order's billing evidence names the
  invoice.
- [ ] T015 [US3] Implement FR-008 in `packages/reality-core/src/reality/web/api.py`
  `document_inspector`.
- [ ] T016 [US1][US3] Extend `apps/web/scripts/unified-invoice-entry-browser.mjs` with the party
  mode (pick positions of two orders, review lists both orders, edit restores) before the UI.
- [ ] T017 [US1][US3] Implement FR-006/FR-007 in `apps/web/src/unified/InvoiceCard.tsx`,
  `apps/web/src/api.ts` and `apps/web/src/localization.tsx` (en/de/nl/es, German
  "Sammelrechnung"), including the new blocker detail string.

## Verification and review

- [ ] T018 Update `tests/scenarios/test_catalog_purchasing.py` I05 to the guided path and add E02
  to `tests/scenarios/test_catalog_finance.py` (#203 is on main); update
  `docs/scenarios/coverage.md`, `docs/features/order_to_cash.md`,
  `docs/features/procure_to_pay.md` and `docs/SPEC_COVERAGE_MATRIX.md`.
- [ ] T019 Run focused suites, the full backend suite in CI order, web build, i18n audit, node
  contract tests and the invoice browser script; review the diff against spec and
  Constitution; mark tasks done only on green evidence.

## Dependencies

T001–T003 → T004; T005 → T006 (after T004); T007 → T008; T009 → T010; T011 → T012 → T013;
T014 → T015; T016 → T017 (after T006, T012, T015); T018–T019 last. US2 readiness and
matching (T007–T010) can proceed in parallel with the read (T011–T013).
