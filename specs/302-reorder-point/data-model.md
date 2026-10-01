# Data Model: Reorder Point and Replenishment Proposal

## New: `item_reorder_point`

| Field | Type | Why |
|---|---|---|
| `tenant_id`, `id` | text, primary key `(tenant_id, id)` | Tenant-scoped opaque identity (hard rule 6). |
| `item_id` | text, FK `(tenant_id, item_id)` → item | The item replenished. |
| `location_id` | text, FK `(tenant_id, location_id)` → location | The location whose stock is judged. |
| `reorder_point` | numeric(18,4), ≥ 0 | Available plus incoming at or below this is reported. |
| `reorder_quantity` | numeric(18,4), > 0 | Proposed when it is reached. |
| `created_at`, `updated_at` | timestamptz | When it was stated and last changed. |

**Constraints:**
- `uq_item_reorder_point_item_location (tenant_id, item_id, location_id)`.
- `ck_item_reorder_point_values` (`reorder_point >= 0 AND reorder_quantity > 0`).

**Index:** `(tenant_id, location_id)` for the FK.

**Typed, not payload** (Constitution III): every read of the exception class filters on the row and compares stock with `reorder_point`, and every proposal reads `reorder_quantity`.

**Events:**
- `reorder_point.set` carries the item, location and both values. A change also carries the previous values.
- `reorder_point.removed` carries the values it had.
- Removal deletes the row. The events keep the history.

**Service rules:**
- Only an active, stocked item and a stock-capable location can be given a reorder point.
- Refusal codes: `reorder_point_item_not_stocked`, `reorder_point_location_not_stock`, `reorder_point_values_invalid`, `reorder_point_changed_since_review` and `reorder_point_not_found`.

## Derived, never stored: `reorder_point_reached`

One entry per reorder point whose item and location satisfy available plus incoming ≤ reorder point.

| Causal value | Meaning |
|---|---|
| `reorder_point` | As stated. |
| `available_quantity` | Physical stock at the location less its active reservations. |
| `incoming_quantity` | Open quantity of open supplier promises to the location, in the stock unit. Promises recorded before spec 301 in a purchase unit are converted by the item's factor, or left out and named by Units not comparable. |
| `proposed_quantity`, `proposed_unit` | The reorder quantity: in the purchase unit when it divides, otherwise in the stock unit. |
| `supplier` | Name, or empty when none or several suppliers price the item. |
| `supplier_choice` | `single`, `several` or `none`. |
| `unit_price` | From `resolve_price` for the named supplier, or empty. |

**Trace:** `item_id`, `location_id`, `reorder_point_id`, the candidate supplier ids and the price list entry id.

**Record:** `record_type: reorder_point` and `record_id` = the reorder point's id, which is the shortest true link. `item_id` and `location_id` are reached through it.

## Not changed

Item, location, price lists, commitments, movements and reservations.
