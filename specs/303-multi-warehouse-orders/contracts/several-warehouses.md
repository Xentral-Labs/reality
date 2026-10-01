# Contract: Orders Served From Several Warehouses

## Services

- `reserve(session, tenant_id, commitment_id, quantity=None, *, location_id=None, ...)`: reserves at `location_id`, or at the promise's location when it is empty.
  - Refusals: `reservation_location_not_stock` for an inactive location or one without stock. A location of another company is `NotFound`.
- `_preview_reservation(..., location_id=None)` returns `location_id` and the availability there.
- `fulfillment_readiness(...)`: `ready_quantity` and its blockers follow the per-location rule. A new `locations` list carries `{location_id, reserved, physical}`.
- The packaged dispatch and the reviewed shipment check per movement that its quantity is reserved and on hand at its `from_location_id` (`movement_location_not_reserved`).

## Tools

- `reserve` (delivery action) and the MCP `reservation_propose` accept the optional `location_id`. The review shows the location and what is available there.
- A transfer is the existing `movement_create` with `movement_type: transfer`, `from_location_id` and `to_location_id`. It is proposed from the finding.

## Exception class `stock_in_another_location`

- **Labels:** "Stock in another warehouse" / "Bestand in anderem Lager".
- **Severity:** normal.
- **Owner:** Warehouse.
- **Clears through:** reserving at another warehouse, transferring the stock to the order's warehouse, receiving there, or the promise being reserved, shipped or cancelled.

## Web

- Attention: for `stock_in_another_location`, "Reserve there" opens the reserve form with the location and quantity prefilled, and "Prepare transfer" opens the movement form with type transfer, from, to, item and quantity prefilled. Both go through the existing review.
- The reserve form gains a location choice, defaulting to the order's location.
- The delivery case shows its reservations with their location.

## CLI

`reality commitment reserve COMMITMENT_ID [--quantity] [--location-id]`, if the command exists; otherwise the generic propose path.
