# Contract: Shop Order Changes and Refunds

## Interpretation of a later Shopify order version

Input: a stored `("shopify", "order")` source record with `version > 1`.

Output, one of:
- `interpreted` with produced references to the revised or cancelled commitments (possibly none,
  when only uninterpreted fields changed);
- `needs_review` with `reason_code` in `cancelled_after_shipment`, `reduces_shipped_quantity`,
  `quantity_increased`, `line_added`, `price_changed`, `address_changed`, `currency_changed`,
  `closed_line_changed`, `reservation_choice_required`, `unassigned_line_changed`, or
  `shopify_changes_require_review` when several apply. The summary lists every code with the
  Shopify line id and number. Nothing changes.

Replaying the same version returns the same outcome and changes nothing.

## Interpretation of a Shopify refund

Input: a `("shopify", "refund")` source record: the refund object with `order_id`.

- Order not interpreted yet: the job fails with `shop_refund_order_missing` and retries.
- A refund line naming an unknown order line: `needs_review`, `shop_refund_line_unknown`.
- Otherwise `interpreted`: one `sales_refund` Document and its lines; return announcements for
  shipped `return` lines.

## Tool `order_line_item_assign` (reviewed, delivery review)

Input: `{"document_line_id": "lin_…", "item_id": "itm_…"}`.

Effect: the line gets the item; a `customer_delivery` promise for the line's quantity, due date and
location of the order is created; `money_moves: false`.

Refusals: `order_line_item_assign_not_sales_order`, `order_line_item_already_assigned`,
`order_line_item_not_item_line`, `order_line_item_order_closed`.

Surfaces: MCP `order_line_item_assign_propose`, Web prepare/confirm through the delivery-action
endpoints, CLI `order-line-item-assign-propose` / `-confirm`.

## Exception class `order_line_item_unknown`

One finding per sales-order item line without an item; names the stated SKU, quantity and order;
clears when an item is assigned or the order is cancelled. Clearing tool: `order_line_item_assign`.
