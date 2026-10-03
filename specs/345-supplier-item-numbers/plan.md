# Implementation Plan: Supplier Item Numbers

**Branch**: `345-supplier-item-numbers` | **Spec**: [spec.md](spec.md)

## Summary

Mirror spec 308 for suppliers. A `supplier_item_number` table (migration `0134_supplier_item_number`) keeps per supplier one number per item with the supplier's name; statements are versions of one source stream per supplier and number. Manual line normalization (`core._normalize_manual_line_input`) resolves `supplier_item_number` for purchase orders, supplier invoices and supplier credit notes against the document's party, and the line payload keeps the stated number like `customer_item_number`.

**Storage**: one new table, `supplier_item_number` (migration 0134). No new column on existing tables; the stated number lives in the line payload.

## Constitution Check

- Source → Evidence → Reality: each statement is a source record version; lines keep the number as stated (VIII).
- No document status (II).
- Typed table justified (III, DR-001): purchase and supplier-invoice entry resolve lines by `(tenant, party, match_key)` on every entry, and lists filter by supplier and item.
- Shortest true relationship: the mapping names party and item only.
- Tenant scope on every query; mutations reviewed through the shared tools (`supplier_item_number_set`, `supplier_item_number_remove`).

## Design

- `services/supplier_item_numbers.py`: validate, set, remove, list, resolve, review; `stated_number` and `line_supplier_item` for reads. Shares `match_key` with spec 308.
- `core.STATED_LINE_NUMBER_KEYS` names the payload-held line numbers so consumers that compare normalized lines (credit proof) read them from the payload, the trap spec 308 hit.
- Adapters: MCP propose/read tools and the strict order and document line schemas, CLI `supplier-item`, Web API `/supplier-item-numbers`, web section on the supplier and a supplier-number field on purchase order lines.
- Reads: document preview labels and `purchase_match` lines show the stated number.

## Tests

Service, entry, adapter tests and business story O06, written before or with each part.
