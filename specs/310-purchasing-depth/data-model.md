# Data Model: Supplier Confirmations, Minimum Quantities and Three-Way Match

## `commitment_revision` (one new column)

| Column | Type | Notes |
|---|---|---|
| unit_price | Numeric(18,4), nullable | Confirmed unit price in the order line's unit; only on purchase promises; the latest stated one is in force |

Check: `unit_price IS NULL OR unit_price >= 0`.

## `supplier_item_terms` (new)

| Column | Type | Notes |
|---|---|---|
| id | String, PK with tenant | |
| tenant_id | FK tenant | |
| party_id | FK party (tenant) | The supplier |
| item_id | FK item (tenant) | |
| minimum_quantity | Numeric(18,4), nullable | In the item's purchase unit |
| order_multiple | Numeric(18,4), nullable | In the item's purchase unit |
| source_record_id | FK source_record (tenant) | The statement in force (spec 320 pattern) |
| created_at, updated_at | DateTime(tz) | |

Checks:
- unique `(tenant_id, party_id, item_id)`;
- at least one of the two values is set;
- both, when set, are positive.

Indexes on `(tenant_id, item_id)` and `(tenant_id, source_record_id)`.

## Events

- `commitment.revised` gains `unit_price` when stated.
- `supplier_item_terms.set` and `supplier_item_terms.removed`.
