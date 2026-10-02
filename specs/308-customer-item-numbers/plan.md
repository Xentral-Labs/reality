# Implementation Plan: Customer Item Numbers

**Branch**: `308-customer-item-numbers` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

A customer's own article number, with the customer's name for it, is kept per customer and item in `customer_item_number`. Each statement is a version of the mapping's source stream (spec 320 pattern).

- **Resolution:** a line resolves its customer number through one rule, `resolve_customer_item`: per customer, ignoring case and spaces.
  - Order entry (manual, MCP, CLI, Web) accepts `customer_item_number` per line instead of `item_id`.
  - The order file import takes a `customer_item_number` column. An unknown number keeps the line without an item, reported by `order_line_item_unknown` (spec 296).
  - Assigning the item on that line offers to remember the number.
- **Kept as stated:** the quoted number is kept in the line's payload. The order, delivery and invoice reads show it with the customer's name from the mapping; an invoice line reaches it through the order line it bills.

See [research.md](research.md), [data-model.md](data-model.md) and [contracts/customer-item-numbers.md](contracts/customer-item-numbers.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Storage**: PostgreSQL; migration `0114_customer_item_number`

**Testing**:
- service, import, order-entry, read, adapter and story tests;
- the order entry, file import and line-item suites as regression;
- web checks, browser fixtures and the full suite.

**Performance Goals**: The import resolves each order's numbers with one query per order.

**Constraints**:
- unchanged results without mappings;
- Shopify untouched;
- tenant-scoped;
- reviewed tools.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Each mapping statement is a source version; the quoted number stays in the line's lossless payload. |
| II. Reality is the operational authority | PASS | No document status; the mapping only chooses the item a line stands for. |
| III. Proven schema only | PASS | The mapping is joined on every import and order entry and filtered per customer; the quoted number stays in the payload, which only display reads. |
| IV. Tenant and service boundaries | PASS | Composite tenant FKs; one resolution rule behind every path. |
| V. Specification and test evidence | PASS | Tests planned per phase, with positive controls. |
| VI. Explainable Web product | PASS | A line shows the number it was ordered by and the mapping that resolved it. |
| VII. Simplicity and storage discipline | PASS | One table; no column on `document_line`. |
| VIII. Received values are recorded, never recomputed | PASS | The quoted number is kept as stated, also after the mapping changes. |

## Design

1. **Schema and service:**
   - Migration `0114` and the `CustomerItemNumber` model, with uniqueness on the customer and the normalized number.
   - `services/customer_item_numbers.py`:
     - `resolve_customer_item`;
     - `set_customer_item_number` and `remove_customer_item_number` (reviewed, source versions);
     - `customer_item_numbers` (read, per customer or item).
   - The events `customer_item_number.set` and `customer_item_number.removed`, and the refusals.
2. **Order entry:** `_normalize_manual_line_input` accepts `customer_item_number`.
   - For a sales order without `item_id`, it resolves through the order's customer and refuses an unknown number (`customer_item_number_unknown`).
   - With both an item and a number stated, a conflicting mapping is refused.
   - The number is kept in the line payload.
3. **File import:** the `sales_order` profile takes `customer_item_number`. A line is resolved by our SKU, else by the customer's number. An unknown number keeps the line without an item and without a promise (the spec 296 pattern), instead of refusing the whole order.
4. **Assignment:** `order_line_item_assign` takes an optional `remember_for_customer`, which, with the line's quoted number, also states the mapping in the same confirmation.
5. **Reads:** order detail, delivery case and invoice lines gain `customer_item_number` and `customer_item_name`.
6. **Adapters:**
   - tools `customer_item_number_set`, `customer_item_number_remove` (reviewed) and `customer_item_numbers` (read);
   - MCP;
   - Web `GET /customer-item-numbers` and `POST /customer-item-numbers/proposals`;
   - CLI `customer-item list|set|remove`.
7. **Web:**
   - "Kundenartikelnummern" on the customer, with add, change and remove.
   - The number in the order line and invoice line views.
   - "Kundenartikelnr." per line in order entry.
   - "Für den Kunden merken" when assigning an unknown item.
   - Translations.
8. **Stories and Guide:** M02 through manual entry and through the import with an unknown number, then the promotion, coverage, roadmap, matrix and docs.

## Rollback

The downgrade refuses while mappings exist. Without mappings, order entry and import behave as before. One exception: the import keeps an unknown line instead of refusing the order only when a customer item number column is present.

## Complexity Tracking

No Constitution violations.
