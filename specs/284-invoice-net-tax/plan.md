# Implementation Plan: Invoices state net and tax

**Branch**: `284-invoice-net-tax` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

The received detail contract `reality_finance_v1` already travels through the
multi-position invoice path. The web form always uses that path, but it never asks for net
or tax. The single-position path used by MCP, chat and the CLI cannot carry the detail at
all: `record_sales_invoice(**arguments)` would reject the key.

This plan:
1. adds `reality_finance_v1` to the single-position path (sales and supplier);
2. adds one shared check of the stated amounts in the invoice preview;
3. adds per-position net and tax fields to the web form and its review.

There is no schema change, and the ledger posting stays on gross.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript (React/Vite)
**Storage**: PostgreSQL. No migration: `DocumentLine.payload.reality_finance_v1` and the
invoice SourceRecord payload carry the values.
**Testing**: pytest service and review tests; `node --test` contract; Playwright fixture
browser test (`unified-invoice-entry-browser.mjs` or a new one); live walk-through for SC-001
**Constraints**: Decimal; four-decimal bound; values recorded as stated, compared, never
derived
**Scale/Scope**: two service paths, one preview check, one form, one review

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The stated amounts enter the invoice SourceRecord payload (lossless, as today for `lines`) and each invoice line's `reality_finance_v1`. Reality records nothing derived. | PASS |
| Reality owns operational state | No document status fields. | PASS |
| Proven schema only | No new column: the existing versioned payload contract carries the values. | PASS |
| Tenant + shared service boundaries | Web, MCP, chat and CLI use `record_sales_invoice` / `record_supplier_invoice` and `_preview_order_invoice`. No adapter fills a missing amount. | PASS |
| Spec/test traceability | Every FR and DR maps to tasks. | PASS |
| Explainable web behavior | The review shows the stated net and tax. The line's received detail stays inspectable through the existing cost evidence reads. | PASS |
| Received values not recomputed | The check compares net + tax with the stated gross and refuses a contradiction. It never computes a missing value, rounds or adjusts. | PASS |
| Smallest coherent design | Rejected: (1) a tax rate or code to derive net, which violates VIII and is a non-goal; (2) typed net/tax columns, which have no calculation need beyond the payload contract; (3) the check in the generic line normalization, which would newly refuse imported documents whose sources legitimately differ. | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py                 # record_*_invoice + _record_order_invoice take reality_finance_v1; _stated_invoice_amounts check in _preview_order_invoice
packages/reality-core/src/reality/services/invoice_actions.py      # review keeps and returns the stated amounts
packages/reality-core/src/reality/mcp/catalog.py                   # single-position schemas gain reality_finance_v1 (sales, supplier)
packages/reality-core/tests/test_invoice_stated_amounts.py         # NEW service and review tests
apps/web/src/api.ts                                                 # InvoiceInput line type: optional reality_finance_v1 {net, tax}
apps/web/src/unified/InvoiceCard.tsx                                # per-position net/tax inputs; review shows them
apps/web/src/localization.tsx                                       # de/nl/es
apps/web/scripts/invoice-net-tax-contract.test.mjs                  # NEW contract
apps/web/scripts/unified-invoice-entry-browser.mjs                  # extend with net/tax (or a new focused script)
docs/features/order_to_cash.md, procure_to_pay.md                   # contract note
```

## Design

### Stated amounts check (`_stated_invoice_amounts`)

It is called in `_preview_order_invoice` for the single position and for each selected
position. It takes the position's `reality_finance_v1` (optional) and the position's stated
gross, and it:

- accepts a dictionary with keys drawn from the existing contract only (`version` (1), `net`,
  `tax`, `base`, `gross`, `currency`, `codes`); anything else is refused;
- requires `net`, `tax`, `base` and `gross` to be decimals of at most four places, with
  `net`, `base` and `gross` at least 0 and `tax` at least 0 (a credit note is not this path);
- refuses a detail `gross` that differs from the position's gross;
- refuses a detail `currency` that differs from the invoice currency;
- **when net and tax are both given, refuses `net + tax != gross`** with "Net plus tax
  differs from the invoice gross." (FR-004);
- returns the detail normalized to exact decimal strings, without adding a single key: no
  version, no computed value.

The check lives in the invoice preview only, not in `_preview_manual_line`, so imports and
other manual documents keep their current behavior (FR-006).

### Single-position path (FR-002)

- `record_sales_invoice(..., reality_finance_v1=None)` and
  `record_supplier_invoice(..., reality_finance_v1=None)` pass it to
  `_record_order_invoice(..., finance_detail=...)`.
- `_record_order_invoice` includes it in the `require_decision_finance` intent, the preview
  arguments and the source payload, so the decision binds the stated values.
- `_preview_order_invoice` already writes `reality_finance_v1` into the created line.
- The MCP single-position schemas (`sales_invoice_record_propose`,
  `supplier_invoice_record_propose`) gain the top-level `reality_finance_v1`
  (`RECEIVED_FINANCE_DETAIL`), and `make docs-generate` follows.

### Multi-position path (FR-003)

- The preview keeps each selection's `reality_finance_v1` into `creation["lines"]` (verify),
  and the source payload stores `arguments` losslessly.
- `creation["selections"]` currently lists only order line, quantity and gross. It gains
  the stated detail when present, so the review token and the post-execution verification
  (`invoice_actions` canonical compare) bind it too. Selections without detail keep their
  exact current shape, so existing review tokens do not change.

### Review and web (FR-001, FR-005)

- `_review_invoice` already embeds `creation`. The web review reads each position's stated
  net and tax from `review.state.creation.lines[i].reality_finance_v1` and shows them next
  to gross.
- **Position fields:** `InvoiceCard` adds "Net (as stated on the invoice)" and "Tax (as
  stated on the invoice)" to each position. They are optional, and the fields that are
  filled become `reality_finance_v1: {net, tax}`.
- **Gross stays as entered:** the form never fills gross from net + tax. A read-time hint
  may show "net + tax = …" as an observation next to the gross the person entered.

### Data and migration impact

None. Rollback is revert. Old invoices stay gross-only.

### Failure, security, and tenant behavior

- Contradictions are refused before anything is recorded.
- A retried request with the same amounts is the same proposal, because the amounts are
  part of the intent.
- Tenant scope is unchanged.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | node + browser | `invoice-net-tax-contract.test.mjs`; browser: fields sent as `reality_finance_v1` | fields absent |
| FR-002 | service | `test_invoice_stated_amounts.py::test_single_position_records_stated_net_and_tax` (sales + supplier, via tool and MCP) | TypeError / key refused |
| FR-003 | service | `::test_multi_position_keeps_each_positions_amounts`, `::test_position_without_detail_stays_gross_only` | selections drop detail from binding |
| FR-004 | service | `::test_net_plus_tax_contradiction_is_refused_and_records_nothing` (paired with a consistent positive control) | not refused |
| FR-005 | browser | the review shows gross, net and tax | not shown |
| FR-006 | service | the existing `test_unified_invoice_entry.py`, `test_multi_position_invoices.py` and `test_consolidated_invoices.py` stay green; `::test_gross_only_is_unchanged` | — |
| FR-007 | service | `::test_stated_net_makes_the_contribution_a_candidate` | `received_net_missing` |
| DR-001 | service | the source payload and line detail equal the stated strings exactly | — |
| DR-002 | review | no migration in the diff | — |
| DR-003 | service | the MCP single-position proposal and the web multi-position path give the same line detail | — |
| DR-004 | service | ledger entries identical to a gross-only invoice | — |
| SC-001 | live | the spec 282 walk-through with an invoice carrying net and tax reaches DB1 (needs 282 merged or a local integration of both branches) | blocked today |

## Rollout and Rollback

The field is additive, and old clients send no detail. Run `make docs-generate` for the MCP
schema change. For SC-001, the live stack runs a local integration of 282 and 284 until 282
is merged.

## Review Risks

- **Review token stability.** Adding detail to `selections` must not change tokens of
  invoices without detail. A test pins an unchanged token for a gross-only invoice.
- **Credit notes.** They share `_record_order_invoice` (`credit=True`). This feature passes
  no detail for credits; a test confirms credit behavior is unchanged.
- **Semantic confusion.** A clerk might type a unit price as net. The labels say "as stated
  on the invoice", and the review shows the three amounts side by side.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
