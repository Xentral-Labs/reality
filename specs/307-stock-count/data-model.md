# Data Model: Stock Count Sessions

## `stock_count` (new)

| Column | Type | Notes |
|---|---|---|
| `id` | text | PK with `tenant_id` |
| `tenant_id` | text | Tenant FK |
| `location_id` | text | The counted location; composite FK |
| `note` | text | As stated |
| `source_record_id` | text | The count statement (`internal_stock_count`); composite FK, required |
| `created_at` | timestamptz | When it was confirmed |

## `stock_count_line` (new)

| Column | Type | Notes |
|---|---|---|
| `id` | text | PK with `tenant_id` |
| `tenant_id` | text | Tenant FK |
| `stock_count_id` | text | Composite FK |
| `item_id` | text | Composite FK |
| `lot_id` | text, null | For a lot-tracked item; composite FK |
| `counted_quantity` | numeric(18,4) | ≥ 0, as stated |
| `counted_at` | timestamptz | As stated; the book is read up to it |
| `movement_id` | text, null | The adjustment that posted the free part; composite FK |

**Constraints:** unique `(tenant_id, stock_count_id, item_id, lot_id)` with nulls not distinct, and a check `counted_quantity >= 0`.

**Index:** `(tenant_id, movement_id)`.

The block part of a loss is the scrap's own resolution and adjustment, linked from the line by the reason and the `stock_count.posted` event.

**Event:** `stock_count.posted`, the history of the posting, naming each line's movements. The detail reads each line from the line and its movements, and reads from the event only which block scraps belong to the line.

**Read at read time, never stored:** the book quantity, the difference, and the reservations left uncovered.
