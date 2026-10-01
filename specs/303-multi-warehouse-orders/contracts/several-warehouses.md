# Contract: Orders Served From Several Warehouses

## Services

- `reserve(session, tenant_id, commitment_id, quantity=None, *, location_id=None, ...)`: reserves at `location_id`, or at the promise's location when it is empty.
  - Refusals: `reservation_location_not_stock` for an inactive location or one without stock. A location of another company is `NotFound`.
- `_preview_reservation(..., location_id=None)` returns `location_id` and the availability there.
- `fulfillment_readiness(..., from_location_id=None)`: its blockers follow the per-location rule (`stock_cover`). With `from_location_id` it judges what is reserved and on hand there only. The fulfilment queue line carries `ready_by_location`: `{location_id, location, quantity}` per warehouse, the order's own first.
- The packaged dispatch and the reviewed shipment check per movement that its quantity is reserved and on hand at its `from_location_id`; otherwise they refuse with `shipment_blocked_readiness`.
- A shipment that fulfils a customer promise releases the reservations it still holds elsewhere (`reservation.released`, cause `commitment_fulfilled`).
- A transfer review warns when the quantity takes reserved stock at its warehouse (`transfer_takes_reserved_stock`).

## Tools

- `reserve` (delivery action) and the MCP `reservation_propose` accept the optional `location_id`. The review shows the location and what is available there.
- A transfer is the existing `movement_create` with `movement_type: transfer`, `from_location_id` and `to_location_id`. It is proposed from the finding.

## Exception class `stock_in_another_location`

- **Labels:** "Stock in another warehouse" / "Bestand in anderem Lager".
- **Severity:** normal.
- **Owner:** Warehouse.
- **Clears through:** reserving at another warehouse, transferring the stock to the order's warehouse, receiving there, or the promise being reserved, shipped or cancelled.

## Web

- Attention: for `stock_in_another_location`, "Serve from another warehouse" opens a card with the named warehouses: "Reserve there" or "Prepare transfer", both through the review.
- The fulfilment queue offers one shipment per warehouse with ready stock.
- The reserve form gains a location choice, defaulting to the order's location.
- The delivery case shows its reservations with their location.

## CLI

`reality commitment reserve COMMITMENT_ID [--quantity] [--location-id]`, if the command exists; otherwise the generic propose path.
