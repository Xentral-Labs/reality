# Plan: Stock at a location

The item/location pair is already derived by `location_inventory_rows`
(`services/read_contracts.py:194`). Nothing new derives a quantity; the work is to give
that pair an address in the web and a place scope to the three registers.

## The pair as an Inspector kind
Add the Inspector kind `stock` with the composite identity `"{item_id}:{location_id}"` —
the key `location_inventory_rows` already uses for its rows, so no new identity scheme is
invented and both halves stay opaque FKs (Hard rule 6). `stock_inspector` in
`web/api.py` reads the pair through that contract (physical, reserved, available, incoming,
projected, unit), and lists the item's movements at that location and its active reservations
there through `movement_page`/`reservation_page` with both filters — the same reads the
register uses, so the panel and the register cannot drift. `operational_preview` gains a
`stock` branch with the same sections for the inline preview. `stock` joins the Inspector
kind set in `get_inspector` and the Playground-readable kinds in
`require_tenant_surface_access`; it is strictly narrower than the item and location
inspectors already readable there. No catalog entry: no stored record type appears.

The Inspector is generic over `{kind, id}`, so the item preview's location rows only change
their link target, and Back already returns to the item.

## Location scope on the registers
`inventory_page`, `reservation_page` and `movement_page` in `web/read_models.py` take
`location_id`. Stock constrains its four aggregate subqueries (movements in by
`to_location_id`, out by `from_location_id`, reservations by `location_id`, open supplier
promises by `Commitment.location_id`) and, per FR-007, restricts the item set to those with
a movement or an active reservation at that location through one `IN` subquery — still one
statement, no pair-by-pair loop (FR-010). Reservations match `location_id`; movements match
either side. `warehouse_register` validates the location, passes it through and reports it in
`scope`; the endpoint takes `location_id`.

Web: `Selection.location` with the `location` URL parameter beside `item`, the client passes
it, `WarehousePage` renders a clearing chip beside the item chip and states the scope in the
register heading (FR-009). A scoped movement row prefixes the route with In, Out or Internal
relative to the scope (FR-006).

## The way back
`location_inspector`'s stock section is retitled to name its quantity, its values carry the
item's unit, and its rows link to `stock` with the pair key instead of to the item
(FR-011). A row label cannot carry a hint in this contract, which is why the quantity name
goes in the section title. Master data · Locations gains Open warehouse with the location
scope, mirroring the item family's existing button.

## Constitution Check
PASS. No schema, migration, table, column or projection (Hard rules 1, 11): the pair stays a
read-time observation. No document status (Hard rule 2). Shortest true relationship (Hard
rule 5): the pair is addressed by its two opaque FKs, and movements and reservations keep
their own links. Opaque identity (Hard rule 6). No new business rule in a transport — the
web reads the same contract as `inventory_read`, which keeps Web UI invariant and Hard
rule 7. Tenant scope: every new query goes through the existing tenant-scoped page builders
and `_tenant_record`. Read-only, so no confirmation boundary applies (Hard rule 10). No new
MCP tool; agent parity already exists.

## Verification and rollback
`packages/reality-core/tests/test_stock_at_location.py`: the pair inspector against
`inventory_read` for the same pair, zero and negative pairs, an unknown half as not-found, a
location that forbids stock, exact-location attribution with a parent and a child, the three
scoped registers, item plus location, the `shortage` state under a scope, FR-007's item set,
and a statement-count assertion that a scoped stock page keeps the unscoped page's shape.
`test_operational_previews.py` and `test_inspector_register.py` cover the preview sections and
the location rows. `apps/web/scripts/stock-at-location-browser.mjs` walks the click path in
both editions and both themes; `stock-at-location-contract.test.mjs` pins the chip, the URL
and the restored scope. Then `make lint`, `make test`, `make spec-check`, `make web-build`,
`npm run test:i18n`, `npm run i18n:audit`, `make docs-catalog-check`, and the scoped page
measured back to back against the unscoped one on a quiet machine (SC-004).

Rollback is reverting the commits: no migration, no stored data, no retired surface.
