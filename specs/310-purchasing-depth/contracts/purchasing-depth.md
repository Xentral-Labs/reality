# Contract: Supplier Confirmations, Minimum Quantities and Three-Way Match

## Confirmed price

`commitment_revise` takes an optional `unit_price` (decimal string, order line unit).
- It is refused on a promise that is not a supplier delivery (`commitment_price_purchase_only`) and when negative (`commitment_price_invalid`).
- The review shows `ordered_unit_price`, the price in force and the confirmed price.

## Supplier item terms

- `supplier_item_terms_set` (reviewed): `{party_id, item_id, minimum_quantity?, order_multiple?}`.
  - The review shows the terms now and after.
  - Refusals:
    - `supplier_item_terms_party_not_supplier`;
    - `supplier_item_terms_empty`;
    - `supplier_item_terms_invalid`;
    - `supplier_item_terms_changed_since_review`.
- `supplier_item_terms_remove` (reviewed): `{party_id, item_id}`.
- `supplier_item_terms` (read): `{party_id? , item_id?}` returns rows.
- Order previews of purchase orders carry `supplier_terms` per line: `{minimum_quantity, order_multiple, below_minimum, off_multiple, suggested_quantity}`.

## Cancellation charge

A free supplier invoice line with `line_type: "charge"` and `billed_document_line_id` of a cancelled purchase line is accepted. No purchase finding is raised for it.

## Purchase match

`purchase_match` (read): `{document_id}` returns the following.
- `{document_id, number, matched, lines: [...]}`
- Each line:
  - `document_line_id`, `item`, `unit`;
  - `ordered` and `in_force` quantities;
  - `received` (net of returns) and `billed` (net of credits);
  - `agreed_unit_price` and `billed_unit_prices`;
  - `cancelled`;
  - `charges`;
  - `matched`;
  - `differences`, a list of codes: `received_short`, `received_over`, `billed_short`, `billed_over`, `price_differs`, `cancelled_unbilled`.

Interfaces: tool `purchase_match`, MCP `purchase_match`, Web `GET /purchase-orders/{document_id}/match`, CLI `purchase match DOCUMENT_ID`.
