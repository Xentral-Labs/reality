# Contract: Reorder Points and the Replenishment Proposal

## Services (`services/reorder_points.py`)

- `reorder_points(session, tenant_id, *, item_id=None, location_id=None) -> list[dict]` returns each point with its item, location and values. It is read-only.
- `set_reorder_point(session, tenant_id, item_id, location_id, reorder_point, reorder_quantity, *, action_id=None, _expected=None) -> ItemReorderPoint` creates or changes the point.
  - `_expected` holds the values the review saw, or `None` when there was no point. A difference is refused with `reorder_point_changed_since_review`.
- `remove_reorder_point(session, tenant_id, item_id, location_id, *, action_id=None, _expected=None) -> dict` removes the point.

## Application tools (`tools/application.py`)

| Tool | Mutating | Arguments |
|---|---|---|
| `reorder_points` | no | `item_id?`, `location_id?` |
| `reorder_point_set` | yes, confirmed | `item_id`, `location_id`, `reorder_point`, `reorder_quantity` |
| `reorder_point_remove` | yes, confirmed | `item_id`, `location_id` |

The review of each mutating tool states the current values, or none, and the new ones. Executing it re-checks them.

## MCP

- `reorder_points`: a read in MCP topic `orders` (group Purchasing), next to `supply_coverage`.
- `reorder_point_set_propose` and `reorder_point_remove_propose`: strict schemas (`additionalProperties: false`).
- `order_create_propose` is unchanged. An agent reading a `reorder_point_reached` entry fills it from the causal values.

## Web

- `GET /api/tenants/{tenant}/reorder-points?item_id=&location_id=`
- `POST /api/tenants/{tenant}/reorder-points/proposals` with `{operation: "set" | "remove", item_id, location_id, reorder_point?, reorder_quantity?}` returns the proposal with its review (`preview.reorder_point`: current and proposed values).
- `POST /api/tenants/{tenant}/change-proposals/{id}/approve` is unchanged.
- UI:
  - The master-data item detail gets a "Reorder points" section: one row per location with set, change and remove, through the review.
  - The exception "Reorder point reached" gets "Prepare purchase order". It opens `OrderCard` prefilled with direction purchase, the location, the supplier when one is named, and one line with the item, the proposed quantity and unit, and the price when one is named.

## CLI

- `reality reorder-point list [--item-id] [--location-id]`
- `reality reorder-point set ITEM_ID LOCATION_ID --point N --quantity N [--yes]`
- `reality reorder-point remove ITEM_ID LOCATION_ID [--yes]`
- Both print the review and ask before confirming, unless `--yes` is given.

## Exception class `reorder_point_reached`

- **Labels:** "Reorder point reached" / "Meldebestand erreicht".
- **Severity:** normal.
- **Owner:** Purchasing.
- **Clears through:** ordering (the open supplier promise counts as incoming), receiving, releasing reservations, or changing or removing the reorder point.
