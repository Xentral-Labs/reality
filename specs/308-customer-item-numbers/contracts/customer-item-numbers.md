# Contract: Customer Item Numbers

## `customer_item_number_set` / `customer_item_number_remove` (reviewed)

**Set:** `party_id`, `item_id`, `customer_item_number`, `customer_item_name?`. The review shows what the number names now and what it will name.

**Remove:** `party_id` and `customer_item_number`.

**Refusals:**
- `customer_item_number_party_not_customer`;
- `customer_item_number_required`;
- `customer_item_number_item_not_found`;
- `customer_item_number_not_found`;
- `customer_item_number_changed_since_review`.

## `customer_item_numbers` (read)

**Arguments:** `party_id` or `item_id`.

**Returns:** the mappings with the item, the number, the name and the source version.

## Order entry

A line may state `customer_item_number` instead of `item_id`.

**Refusals:**
- `customer_item_number_unknown`;
- `customer_item_number_conflicts_with_item`.

## File import

The `sales_order` profile takes the column `customer_item_number`; an unknown number keeps the line for `order_line_item_unknown`.

## `order_line_item_assign`

Takes an optional `remember_for_customer: true`, which also states the line's quoted number for the order's customer.

**Adapters:**
- MCP `customer_item_number_set_propose`, `customer_item_number_remove_propose` and `customer_item_numbers`;
- Web `GET /customer-item-numbers` and `POST /customer-item-numbers/proposals`;
- CLI `reality customer-item list|set|remove`.
