# Contract: Stock Counts

## `stock_count` (reviewed, mutating)

**Arguments:** `location_id`, `note`, and `lines: [{item_id, lot_id?, counted_quantity, counted_at?}]`. A missing `counted_at` defaults to the review time.

**Review:** per line the item, the lot, the book at the counting time, the counted quantity, the difference, and how much of a loss is scrapped from blocks. It also shows the reservations at the location left uncovered after the loss, per item.

**Refusals:**
- `stock_count_location_not_stock`;
- `stock_count_lines_required`;
- `stock_count_item_not_found`, `stock_count_item_not_stocked`, `stock_count_serial_item`, `stock_count_lot_required`, `stock_count_lot_not_for_item`;
- `stock_count_quantity_invalid`, `stock_count_time_in_future`;
- `stock_count_line_twice`;
- `stock_count_loss_exceeds_stock`;
- `stock_count_changed_since_review`.

**Adapters:**
- MCP `stock_count_propose`;
- Web `POST /api/tenants/{t}/stock-counts/proposals`;
- CLI `reality stock-count record LOCATION --line ITEM[:LOT]=QTY ... [--note] [--yes]`.

## `stock_counts`, `stock_count_detail` (reads)

**Returns:**
- the counts of a location, newest first;
- one count with its lines, book, difference and the movements that posted it.

**Adapters:**
- MCP `stock_counts` and `stock_count_detail`;
- Web `GET /stock-counts?location_id=` and `GET /stock-counts/{id}`;
- CLI `reality stock-count list|show`.
