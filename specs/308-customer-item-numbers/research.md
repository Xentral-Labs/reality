# Research: Customer Item Numbers

## What exists

- **Order file import:** the `sales_order` profile resolves each line by our `sku` (`file_interpreters._item`) and refuses the whole file on an unknown SKU.
- **Shopify:** since spec 296, an order keeps a line with an unknown SKU without an item and without a promise; `order_line_item_unknown` reports it, and `order_line_item_assign` assigns the item through the review.
- **Manual order entry:** `_normalize_manual_line_input` takes `item_id` per line. The line payload carries extra stated detail (`reality_finance_v1`).
- **Party settings:** party-level settings with history follow the spec 320 pattern: a source stream with the row naming the version in force (spec 306 delivery rules).

## Decisions

- **One table, `customer_item_number`.** It holds the party, the item, the number as stated, its normalized key (case- and space-insensitive) and the customer's name, and names the source version in force. It is unique on `(tenant, party, key)`.
- **Resolution in one place.** `resolve_customer_item(party, number)` serves order entry, the import and the assignment.
- **Stated number in the payload.** It is displayed and never acted on again, so it stays in the line's lossless payload. No column on `document_line`; a new `document` column breaks the historical migration tests, and the line is no different.
- **Import with unknown numbers.** A row naming a customer number that does not resolve is kept as an item line without an item, as in spec 296, so `order_line_item_unknown` and the assignment apply unchanged.
- **Remembering on assignment.** The assignment can state the mapping in the same confirmation, so a clerk teaches the number once.
