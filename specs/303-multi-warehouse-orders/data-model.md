# Data Model: Orders Served From Several Warehouses

## Schema

No change.
- `Reservation.location_id` already exists, is not null, and is where a reservation's stock is held.
- Today it always equals the promise's location. From now on it may be another serving location (active, `allows_stock`).

## Rules

- **Serving location**: `Location.is_active` and `Location.allows_stock`.
- **Available at L**: physical stock of the item at L less its active reservations at L, the same expression as today's own-location check.
- **Ready quantity of a promise**: `Σ over its active reservations' locations L of min(reserved at L, physical at L)`, capped by the open quantity. With every reservation at home this equals today's `min(reserved, physical at own location)`.
- **Shipment from L**: needs what is reserved for the promise at L and on hand at L. It consumes the reservations at L, unchanged from today.

## Derived, never stored: `stock_in_another_location`

One entry per open customer promise for which:
- rest = open − active reservations (all locations) > 0;
- own available = available at the promise's location < rest;
- Σ available at other serving locations > 0.

| Causal value | Meaning |
|---|---|
| `unreserved_quantity` | The rest, in the item's unit. |
| `own_available_quantity` | What the promise's own location still has available. |
| `elsewhere` | Readable: `Munich 40 · Berlin 10`, the other serving locations with available stock, most first. |

**Trace:** `commitment_id`, `item_id`, `location_id`, and `locations`: `[{location_id, name, available, proposed}]`, where `proposed = min(rest − own available, available there)`.

**Record:** `record_type: commitment` and `record_id` = the promise, so the delivery opens from it.
