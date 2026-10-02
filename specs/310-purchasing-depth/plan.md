# Implementation Plan: Supplier Confirmations, Minimum Quantities and Three-Way Match

**Branch**: `310-purchasing-depth` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

Four small pieces on existing purchasing records:

- **Confirmed price:** `commitment_revision.unit_price`. The price in force on a purchase line is the latest stated one, the same rule as quantity and date.
- **Supplier terms:** a new table `supplier_item_terms`, per supplier and item, holding the minimum order quantity and the order multiple. Each statement is a version of `internal_supplier_item_terms` (spec 320 pattern). Order previews read the terms and name a violation.
- **Cancellation charge:** the free supplier invoice already records a charge line with `billed_document_line_id`. The purchase exception classes skip cancelled promises and charge lines.
- **Three-way match:** a read `purchase_match` per order. Each line shows ordered and in force, received, billed and agreed against billed price, then `matched` or the differences, derived at read time.

See [research.md](research.md), [data-model.md](data-model.md) and [contracts/purchasing-depth.md](contracts/purchasing-depth.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Storage**: PostgreSQL; migration `0117_purchasing_depth`

**Testing**:
- revision, terms, exception, match, adapter and story tests;
- the commitment-revision, invoice, exception and purchasing suites as regression;
- web checks and the full suite.

**Performance Goals**: The match read is bounded by one order: one read each for lines, promises, revisions, receipts, invoice lines and returns.

**Constraints**:
- unchanged results without confirmed prices or terms;
- tenant-scoped;
- reviewed tools.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | A confirmed price is part of a revision, which names its source; terms are source versions. |
| II. Reality is the operational authority | PASS | No document status; "matched" is derived from promises, movements and invoice lines. |
| III. Proven schema only | PASS | The confirmed price is compared on every invoice-price check and copied by the guided invoice. Terms are read on every purchase preview. |
| IV. Tenant and service boundaries | PASS | Composite tenant FKs; one shared rule per read. |
| V. Specification and test evidence | PASS | Tests planned per phase, with positive controls. |
| VI. Explainable Web product | PASS | The purchase line shows ordered and confirmed values, terms, cancellation, charge and match. |
| VII. Simplicity and storage discipline | PASS | One nullable column and one small table; the match is a read. |
| VIII. Received values are recorded, never recomputed | PASS | Confirmed prices and terms are kept as stated. |

## Design

1. **Schema:** migration `0117`:
   - `commitment_revision.unit_price` (Numeric 18,4, nullable);
   - table `supplier_item_terms`.
2. **Confirmed price:**
   - `revise_commitment` takes `unit_price` for purchase promises only, refused otherwise (`commitment_price_purchase_only`).
   - `commitment_terms` gains `unit_price` in force, which falls back to the order line's stated price.
   - `commitment_revise` and its review accept it and show ordered and confirmed price.
   - The guided supplier invoice preview (`_order_line_billing`) uses the price in force and the quantity in force.
   - `invoice_price_differs` compares against the price in force.
3. **Supplier terms:** `services/supplier_item_terms.py`.
   - `set_supplier_item_terms` and `remove_supplier_item_terms` are reviewed; `supplier_item_terms` reads them.
   - `order_terms_check(session, tenant, supplier, item, quantity)` returns the violation and the next valid quantity.
   - The manual purchase order preview, the `order_create` review and the reorder suggestion carry `supplier_terms`.
4. **Cancellation charge:**
   - The free supplier invoice accepts a charge line naming a purchase line.
   - `_order_line_promises` and `invoice_price_differs` leave out cancelled promises and charge lines.
   - The purchase line's read shows `cancelled_at`, the cancellation reason and the charges billed for it.
5. **Match read:** `services/purchase_match.py`, `purchase_match(session, tenant, document_id)`.
   - Per line: ordered, in force, received net of returns, billed net of credits, agreed and billed unit price, charges, cancelled.
   - `matched` is true, or `differences` lists the codes `received_short`, `received_over`, `billed_short`, `billed_over` and `price_differs`.
   - The order is matched when every line is.
6. **Adapters:**
   - tools `supplier_item_terms_set` and `supplier_item_terms_remove` (reviewed), `supplier_item_terms` and `purchase_match` (reads);
   - the `unit_price` argument on `commitment_revise`;
   - MCP, Web endpoints and CLI.
7. **Web:**
   - On a purchase order: a match column per line with the differences, and ordered and confirmed price.
   - In the revision card: a confirmed price field.
   - On the supplier: minimum and multiple per item.
   - In the purchase order entry: the terms hint.
   - Translations.
8. **Stories and Guide:** G09, G06, G12 and I01, then the promotion, coverage, roadmap, matrix and docs.

## Rollback

The downgrade refuses while confirmed prices or terms exist. Without them, every read and finding is unchanged.
