# Research: Reorder Point and Replenishment Proposal

## R1. Today

- **No reorder concept.** `src/` has no reorder point, minimum or safety stock, and no purchase suggestion. G02 is `partial`: "the purpose of a stock purchase can be stated" (supply assignment purpose `stock_replenishment`, `services/supply_assignments.py`).
- **Item.** It holds `unit`, `purchase_unit`, `conversion_factor` and `lead_time_days`, but no per-location settings. No item/location table exists.
- **Stock per location.**
  - Physical stock is the sum of movement legs, so `to_location_id` adds and `from_location_id` subtracts.
  - Reservations carry `location_id`, and active ones are subtracted. `inventory_detail_rows` (`services/inventory_positions.py`) already reads `available = physical − reserved` per location.
  - The item-wide `inventory_rows` (`services/core.py`) and the `item_supply_demand` projection aggregate across all locations.
- **Incoming.** This is the open quantity of open `supplier_delivery` promises (`commitment_terms(...).open`). Promises carry `location_id`, and since spec 301 they are in the stock unit for new purchases (`commitment.unit`).
- **Purchase prices.**
  - Price lists carry `direction` "purchase" or "sales". `PriceListEntry` holds item, min quantity, unit price, unit and validity.
  - A list reaches a supplier through `PartyPriceList` or `PartyGroupPriceList`.
  - `resolve_price(session, tenant, party, item, quantity, direction, currency, unit, at=)` is the one lookup.
  - There is no preferred supplier.
- **Purchase order.**
  - The reviewed `order_create` path runs `review_order` (`services/order_actions.py`), then the MCP tool `order_create_propose`, or the Web `POST /delivery-actions/prepare` followed by `/change-proposals/{id}/approve`.
  - The web `OrderCard` opens with a blank draft and takes only `direction`.
- **Exceptions in the web.** `AttentionPage` already offers one class-specific action (`order_line_item_unknown` → "Assign item"). That is the pattern for "Prepare purchase order".

## R2. Design (owner decisions, 2026-10-01)

- **Storage**: a typed table `item_reorder_point`, one row per item and location. It holds `reorder_point` (≥ 0) and `reorder_quantity` (> 0), both in the item's stock unit.
- **Condition**: available at the location plus incoming to the location ≤ reorder point. This is derived at read time.
- **Supplier**:
  - Candidates are the suppliers that have, directly or through their group, a purchase-direction price list that prices the item now.
  - With exactly one candidate, the entry names it with `resolve_price` for the proposed quantity and unit.
  - With several or none, it names none, and the entry says why.
- **Quantity**: the stated reorder quantity.
  - It is expressed in the purchase unit when the item states one and the quantity divides into it (`domain/units.in_unit`, spec 301).
  - Otherwise it stays in the stock unit. It is never rounded.
- **Surface**:
  - The operational exception class `reorder_point_reached`.
  - In the web, its "Prepare purchase order" opens `OrderCard` prefilled from the entry. The purchase is created only when the buyer confirms the reviewed `order_create`.
- **Settings**:
  - Reviewed tools `reorder_point_set` and `reorder_point_remove`, plus a read `reorder_points`.
  - They are shared by MCP, Web and CLI.
  - A change since the review is refused.

## R3. Alternatives rejected

- **Fields on `Item`**: one point for the whole company cannot say "Hamburg runs low while Munich is full".
- **A stated fact**: proposals filter and compare on it on every read (Constitution III), and a fact has no unique key per item and location.
- **A proposal table**: this would store a derivation as authority (DR-002). The entry disappears by itself once an order or a receipt covers it.
- **A new master-data family** in `reference_workspace`: that framework assumes named, activatable records, and a reorder point is neither.

## R4. Gates to pass

- Classes: `CLASS_ORDER`, `DERIVATION_REGISTRY`, the catalogs tuple, the YAML order and the test lists, plus `commitment_classes` if it is derived there. It is not: it is derived per reorder point.
- `reference_catalog` consumers and the counts in `test_reference_integrity`.
- Isolation catalog and its pinned counts.
- `service_refusals.json` plus de/nl/es.
- `command_catalog` parameter descriptions.
- `data_model.yaml` plus the docs field rows.
- `resource_catalog.yaml` membership and German labels.
- The MCP topic.
- `SPEC_COVERAGE_MATRIX` rows.
- `make docs-generate`, `docs-catalog-check` and `spec-check`.
- The narrowed/incremental exception refresh, if it applies: `reorder_point.*`, movement, reservation and supplier-promise events must invalidate the class.
- The old-schema trap does not apply: a new table, not a column on an existing one.
- The cost census reads only movement columns and is unaffected.
