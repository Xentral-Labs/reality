# Contract: Blocked Stock

## Services (`services/stock_blocks.py`)

- `block_stock(session, tenant, item_id, location_id, quantity, reason_code, note="", *, handling_unit_id, lot_id, serial_unit_id, action_id, _movement_id)`
  - Refuses with `stock_block_exceeds_available` and `stock_block_reason_unsupported`.
  - Item and location must be stocked and stock-capable.
- `release_stock_block(session, tenant, block_id, quantity=None, *, reason, action_id)`
  - Refuses with `stock_block_not_active`, `stock_block_quantity_exceeds_block` and `stock_block_reason_required`.
- `scrap_stock_block(session, tenant, block_id, quantity=None, *, reason, action_id)`
  - Records an outbound adjustment with that reason and consumes the block.
- `stock_blocks(session, tenant, *, item_id, location_id, status="active")` is a read.
- `blocked_quantity(...)` lives in `services/core.py`, beside `stock_at`.

## Tools, MCP, Web, CLI

- **Delivery actions** with review: `stock_block`, `stock_block_release`, `stock_block_scrap`. The review shows physical, reserved, blocked and available at the identity.
- **MCP:** `stock_block_propose`, `stock_block_release_propose`, `stock_block_scrap_propose`, and the read `stock_blocks`.
- **Receipt:** `movement_create` receipt and `shipment_receive` movements accept `blocked_quantity` and `block_reason`.
- **Web:**
  - The warehouse stock view shows "Blocked" and offers "Block" per position.
  - A blocks list with "Release" and "Scrap".
  - The receipt form gets "Of which blocked" with a reason.
  - The "Stock expired" finding offers "Block".
- **CLI:** `reality stock-block block|release|scrap|list` (`reality stock` already reads stock).
