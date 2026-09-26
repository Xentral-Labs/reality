# Implementation Plan: Consolidated invoices across orders

**Branch**: `280-consolidated-invoices` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

## Summary

Lift the one-order rule of the shared invoice preview and replace it with an explicit
same-direction, same-party, same-currency rule. Add one read that lists a party's billable
order positions. Make the three reads that assume one order per invoice truthful: invoice
review state, prepayment readiness and payment matching by order reference. The web invoice
card picks positions from the party-wide list. No schema, no new document type, no new event.

## Technical Context

**Language/Version**: Python 3.12, TypeScript/React (apps/web)
**Primary Dependencies**: SQLAlchemy 2, Pydantic v2, FastAPI, existing MCP runtime
**Storage**: PostgreSQL; no migration
**Testing**: pytest on isolated PostgreSQL; apps/web node contract tests and the Playwright
browser script `apps/web/scripts/unified-invoice-entry-browser.mjs`
**Constraints**: stated values recorded unchanged (Constitution VIII); one confirmation writes
one source, one invoice, N lines and one posting group atomically; review token must go stale
when any selected position changes
**Scale/Scope**: a collective invoice of 50+ positions from 12+ orders within existing input
bounds; the billable-positions read is bounded and reports a truthful total

## Constitution Check

| Principle | Evidence | Result |
| --- | --- | --- |
| I Source → Evidence → Reality | One manual source per confirmation, one invoice, one DocumentLine per position linked by `billed_document_line_id`, one balanced posting group | PASS |
| II Reality authority, shortest links | Order ↔ invoice stays the existing line link; no order FK on the invoice, no billing status on documents | PASS |
| III Proven schema | No field added; spec 076 already made the line relation carry consolidated invoices | PASS |
| IV Tenant and services | Preview/record, billable read, readiness and matching are shared services; HTTP, MCP, Chat and web call them; every query tenant-scoped | PASS |
| V Test evidence | Tasks put failing service, readiness, matching and browser proofs before each implementation | PASS |
| VI Explainable web | Review lists every order; Inspector groups referenced positions by order with links both ways | PASS |
| VII Simplicity | Extends the existing `lines` input and review lifecycle; the only new surface is one read | PASS |
| VIII Received values | No amount is summed, split or rounded; prepayment release waits for full settlement instead of splitting a payment | PASS |

No exception; Complexity Tracking is empty.

## Design

### Core preview and record (`packages/reality-core/src/reality/services/core.py`)

- `_preview_order_invoice`, multi branch (today L9185–9282): remove the same-order refusal
  (L9234–9241). Refuse, before any write, when the selected positions differ in party
  (`order.party_id`), currency (`order.currency`) or direction; each position keeps its own
  per-line validation (remaining, direction, tenant) through the existing recursive preview.
- The preview result gains `orders: [{id, number}]` in first-selection order. The top-level
  `order_line_id` stays for legacy consumers of the single shape only.
- `_record_multi_order_invoice` is unchanged in shape: it already locks every selected line
  in sorted order, re-previews, records one source/invoice/lines and posts once.
- `delivery_guard` stays single-line only (FR-009).

### Review, stale detection, recovery (`services/invoice_actions.py`)

- `_review_invoice`: for the `lines` shape, build `state.orders[]` and `state.party` from the
  validated preview instead of the first position's order; derive `item` per position (no
  failure when the first line has no item). Keep `state.order` for the single shape so legacy
  proposals and receipts hash and verify exactly as today (FR-009).
- The token already hashes `state`; it goes stale when any selected position's billing
  changes. `_assert_no_unresolved_invoice` and `_invoice_evidence` are already per line.

### Billable positions read (new, FR-006)

- `services/invoice_billing.py::billable_positions(session, tenant_id, *, direction,
  party_id, currency, limit=200)`: open order lines of that party and currency whose
  `_order_line_billing` reports `can_invoice` and `remaining > 0`, grouped by order, ordered
  by order date then line position, with `total` counted before the limit. `_order_line_billing`
  becomes a shared helper in the same module (moved, not duplicated) and core keeps a
  re-export.
- Exposed as MCP read tool `invoice_billable_positions` and HTTP
  `GET /tenants/{tenant_id}/invoice-billable-positions`. Completeness gates for a new read
  surface apply: tenant isolation catalog and pinned counts, MCP topic and capability
  guidance, `config/resource_catalog.yaml` membership with `labels.de`, command catalog read
  entry, `make docs-generate`.

### Prepayment readiness (`services/fulfillment_readiness.py`, FR-004)

- Replace the ambiguous rule (L300–312): an invoice of the same party and currency that also
  bills other orders' lines is a consolidated invoice, not ambiguous.
- For a consolidated invoice, the order qualifies only when the invoice's open amount is zero.
  While open, a new blocker `prepayment_consolidated_invoice_open` names the invoice and its
  open amount; `_blocker_links` links the invoice. Single-order invoices keep today's rule.
- `prepayment_attribution_ambiguous` remains for any residual case that cannot be attributed
  (e.g. an invoice line whose order cannot be read); it is no longer produced by consolidation.
- Blocker vocabulary: add the code to `DELIVERY_BLOCKER_TYPES` (`services/projections.py`
  L440–448), its detail text, and web labels in four languages.

### Payment matching by order reference (`services/payment_intake.py`, FR-005)

- `resolve_references` (L323–445): when the invoice found through an order reference also bills
  lines of other orders, it is not `unambiguous`; the payment becomes a candidate with the
  reason "invoice {number} also bills other orders". Matching by the invoice reference itself
  is unchanged.

### Web (`apps/web/src`)

- `unified/InvoiceCard.tsx`: choose invoice type, party and currency; load
  `billable_positions`; pick positions grouped by order with quantity and stated line amount;
  stated total stays separate. The one-order picker stays available as "From one order".
- Review header lists every order with an Inspector link (`state.orders`); `edit()` restores
  party, currency and positions; legacy proposals restore through `state.order`.
- `api.ts`: `InvoiceProposal.state.orders`, `billablePositions()` client, types.
- `localization.tsx`: new strings in en/de/nl/es; replace "Select one or more positions from
  this order…" for the party mode.
- Inspector (`web/api.py document_inspector`, L5361–5380): group an invoice's referenced
  positions by order and link each order (FR-008). Order → invoice already exists via
  `billing.evidence`.

### Catalogs and docs

- `config/command_catalog.yaml`: effect text of "Record sales invoice" / "Record supplier
  invoice" becomes "against one or more order lines of one party"; add the read.
- `docs/features/order_to_cash.md` and `procure_to_pay.md`: consolidated invoices; 
  `docs/scenarios/coverage.md` rows I05 and E02 once proven.
- `make docs-generate` output committed.

### Unchanged on purpose

- Playground invoice lessons stay single-line (`playground/actions.py` `PlaygroundInvoiceInput`).
- Order journey (spec 233) keeps not traversing invoices.
- No CLI invoice command exists; none is added.

## Tests to change because they pin the old rule

- `tests/test_multi_position_invoices.py::test_invalid_is_inert[mixed]`: becomes "same party,
  other order is accepted" plus new refusals for another party and another currency.
- `tests/test_fulfillment_readiness.py::test_cross_order_invoice_attribution_blocks_without_guessing`:
  rewritten for the consolidated rule (open → blocked with the new code; settled → released).
- `tests/scenarios/test_catalog_purchasing.py::test_one_supplier_invoice_bills_lines_of_two_purchase_orders`
  (PR #203): its "same order" refusal becomes the guided success path.

## Validation and rollback

Focused suites first (multi-position invoices, unified invoice entry, partial invoicing,
fulfilment readiness, payment intake, invoice actions, catalog scenarios, isolation and MCP
catalog tests), then the full backend suite in CI order, web build, i18n audit, node contract
tests and the invoice browser script. Rollback: revert the preview rule and the web party mode;
consolidated invoices already recorded stay valid, because they use only existing line links
that the free supplier path already writes.
