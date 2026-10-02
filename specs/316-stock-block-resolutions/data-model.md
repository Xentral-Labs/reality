# Data Model: Stock Blocks Keep What Was Stated

## Changed: `stock_block` (18 → 13 columns)

| Field | Change | Why |
|---|---|---|
| `tenant_id`, `id`, `item_id`, `location_id`, `handling_unit_id`, `lot_id`, `serial_unit_id`, `quantity`, `reason_code`, `note`, `created_at`, `created_by` | unchanged; never updated after insert | `quantity` is the quantity as stated. |
| `receipt_movement_id` | renamed from `movement_id` | The receipt that stated the block, and nothing else. |
| `status`, `resolved_at`, `resolved_by`, `resolution_reason`, `previous_block_id` | dropped | Derived from resolutions, or moved to them. |

**Indexes**: `(tenant_id, item_id, location_id)` replaces the status index; FK indexes as before, without `previous_block_id`.

## New: `stock_block_resolution` (9 columns)

| Field | Type | Why |
|---|---|---|
| `tenant_id`, `id` | text, PK | Tenant-scoped opaque identity. |
| `block_id` | text, FK `stock_block` | The block this resolves; shortest true link. |
| `kind` | text, check in (`release`, `scrap`) | Shown; decides whether a movement exists. |
| `quantity` | numeric(18,4) > 0 | Subtracted from the stated quantity by every availability read. |
| `reason` | text, non-blank | As stated. |
| `resolved_at`, `resolved_by` | timestamptz, text | Who and when. |
| `movement_id` | text, FK `movement`, deferred, unique, nullable | The adjustment a scrap recorded; set iff `kind = 'scrap'`. |

**Indexes**: `tenant_id`, `(tenant_id, block_id)`, `(tenant_id, movement_id)`.

## Rule

- **Open quantity** of a block = `quantity` − Σ `stock_block_resolution.quantity`.
- **Open** iff open quantity > 0; the list's `status` is this derivation (`active` / `resolved`).
- **Blocked at L** = Σ open quantity of blocks at L, likewise per identity (unchanged meaning from spec 304).

## Events

Unchanged types. `stock_block.released` and `stock_block.scrapped` carry `resolution_id` and `open_quantity` instead of `remainder_block_id`; the subject stays the block.
