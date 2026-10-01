# Data Model: Blocked Stock and Best-Before Dates

## New: `stock_block`

| Field | Type | Why |
|---|---|---|
| `tenant_id`, `id` | text, PK | Tenant-scoped opaque identity. |
| `item_id`, `location_id` | text, FK | Where the blocked goods are. |
| `handling_unit_id`, `lot_id`, `serial_unit_id` | text, FK, nullable | The exact identity blocked, when stated. |
| `quantity` | numeric(18,4) > 0 | Blocked while the row is active. |
| `reason_code` | text, check in (quality, damage, expiry, inspection) | Why it is blocked; filtered and shown. |
| `note` | text | As stated. |
| `status` | text, check in (active, released, scrapped) | Excluded from availability while active. |
| `created_at`, `created_by` | | Who blocked it. |
| `resolved_at`, `resolved_by`, `resolution_reason` | nullable | Who released or scrapped it, and why. |
| `previous_block_id` | FK self, nullable | The block a partial release or scrap split this one from. |
| `movement_id` | FK movement, nullable | The receipt that created it, or the adjustment that scrapped it. |

**Indexes:** FKs, and `(tenant_id, item_id, location_id, status)`.

**Typed, not payload:** every availability read filters active blocks by item, location and identity and subtracts the quantity (Constitution III).

**Events:**
- `stock_block.created`
- `stock_block.released` (with quantity and reason)
- `stock_block.scrapped` (with quantity, reason and the adjustment movement)

## Rule

- **Available at L** = physical at L − active reservations at L − active blocks at L, likewise per identity.
- **Item-wide available** subtracts all active blocks.
