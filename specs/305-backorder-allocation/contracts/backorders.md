# Contract: Serving Backorders

## `backorders_serve` (reviewed, mutating)

Arguments: `item_id`, `location_id`, optional `supplier_commitment_id` (the received purchase), optional `lines: [{commitment_id, quantity}]`.

The review shows:
- the item, unit, location and what is available there;
- the proposed lines in serving order, each with promise, customer, due date, need, quantity and why it stands there (`assigned` or `due`);
- the promises under a hold, which are not served;
- what is reserved in total and what stays free.

Refusals:
- `backorder_serving_item_not_found`, `backorder_serving_location_not_stock`, `backorder_serving_tracked_item`;
- `backorder_serving_line_not_waiting` (a promise that is not waiting here), `backorder_serving_line_exceeds_need`, `backorder_serving_exceeds_available`, `backorder_serving_nothing_to_serve`;
- `backorder_serving_changed_since_review` on confirmation.

Adapters: MCP `backorders_serve_propose`, Web `POST /api/tenants/{t}/backorders/proposals`, CLI `reality backorders serve ITEM LOCATION [--purchase ID] [--yes]`.

## `available_to_promise` (read)

Arguments: `item_id`.

Returns `{item, unit, now: {physical, reserved, blocked, waiting_uncovered, free}, purchases: [{commitment_id, supplier, due_at, overdue, open, assigned_to_come, adds, total}]}`.

Adapters: MCP `available_to_promise`, Web `GET /api/tenants/{t}/items/{item_id}/available-to-promise`, CLI `reality backorders promise ITEM`.

## `supply_coverage` (extended read)

Each item row gains `arrived` and `still_to_come`; the customer block gains `arrived` and `still_to_come`. `protecting_supply` stays the total.
