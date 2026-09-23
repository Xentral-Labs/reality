# Feature Specification: Stock at a location

**Feature Branch**: `262-stock-at-location`
**Language**: English
**Created**: 2026-09-23
**Status**: Approved (scope accepted by the owner 2026-09-23, with the three decisions below)
**Input**: In Warehouse, clicking a quantity on an item never arrives at that item in that place. It arrives at the whole warehouse. Decide what a warehouse clerk expects behind each number and let the clicks lead there.

## Context and Intent

### Problem
A warehouse clerk works at the intersection of one item and one place: "three Beacon Desk Organizers, two of them in Rotterdam — where did those two come from, and who is holding them?" That intersection is visible nowhere in the product.

The item stock preview lists one quantity per location (`operational_previews.py:312-327`). The quantity is a link, and the link says `kind="location"`. `operational_preview` has no location branch (`operational_previews.py:553-574`), so the generic location inspector answers instead: every item in that warehouse and the warehouse's recent movements (`web/api.py:5546-5599`). The item the clerk came from is not passed along and is not shown. The way back is equally broken: the location inspector's stock rows link to the item across all locations, never to the item here.

The register cannot repair it either. `warehouse_register` takes a search term, a state and an item scope, and no place scope at all (`web/api.py:827-846`, `web/warehouse_reads.py:33-45`); Stock, Reservations and Movements are company-wide in all three tabs. A clerk who works in one warehouse has no way to ask for it.

The two views also show different quantities, and only one of them says so. The item preview shows **available** stock per location and names it, in the section title and again under each location (`held - assigned`, `operational_previews.py:312-327`). The location inspector shows **physical** stock per item under the neutral title "Current stock", with no quantity name and no unit (`web/api.py:5577-5586`). Today both read 2 for ITEM-012 in Rotterdam because nothing is reserved. The first reservation makes them differ, and the location side gives the reader nothing to notice it by.

The intersection is not missing from the system — only from the web. `location_inventory_rows` already derives physical, reserved, available, incoming and projected for one item at one location from Movements and Reservations (`services/read_contracts.py:194-246`), and `inventory_read` exposes it to the agent in location view (`command_catalog.yaml:3960-3982`). An agent can already ask what a clerk cannot.

### Principle
A quantity is always a quantity of one thing in one place, at one moment. A screen that shows such a quantity owes the reader three things: which quantity it is, in which unit, and the records that produce it. The shortest true link from "2 pcs in Rotterdam" is not the warehouse and not the item — it is the pair.

### Scope
Make the item/location pair a first-class destination in the web: reachable from the item's per-location quantities, reachable from the location's per-item quantities, and available as a scope on all three Warehouse registers. Every number keeps the derivation it already has.

### Non-Goals
No new entity, table, column or projection: the pair is derived at read time from Movements and Reservations, as it is today (Hard rule 11). No stock or fulfilment status on documents (Hard rule 2). No new MCP tool — `inventory_read` already answers this question for agents. No location roll-up: quantities stay recorded at the exact location, and a parent location does not sum its children. No change to how physical, reserved or available are computed. No redesign of the three clickable quantities in the stock table, which all open the same preview today; that stays as it is and is corrected separately. The unit and item name missing from the location inspector's movement rows, and its unbounded per-item stock derivation (`services/core.py:11419-11422`, one pair of queries per item of the company), are named here as context and fixed separately.

## Inventory of the current clicks (read 2026-09-23, `origin/main` at 71e4b1d7)

| Where | Click | What a clerk expects | What happens today |
|---|---|---|---|
| Warehouse · Stock, item preview | location row "Rotterdam Warehouse · 2 pcs" | this item in Rotterdam: what is held, what is reserved, which movements and reservations produce it | the location inspector: 15 other items, the warehouse's last movements; the item context is dropped |
| Warehouse · Stock, item preview | the per-location quantity itself | available here, and what it is made of | available only; physical and reserved at that location are nowhere |
| Warehouse · Stock, item preview | "Reservations" / "Movements" | from a location row: this item, here | the register scoped to the item across all locations |
| Warehouse, any tab | scope to one warehouse | list only what is in my warehouse | not possible; `warehouse_register` has no location filter |
| Reality Inspector · location | stock row "Aurora Notebook 10" | this item here | the item inspector across all locations; the number has no unit and no quantity name |
| MCP · `inventory_read` | `view=location`, `item_id`, `location_id` | the pair | already answers it, with physical, reserved, available, incoming, projected and unit |

## User Scenarios & Testing

### User Story 1 — The pair, from the item (Priority: P1)
A clerk opens an item in Warehouse · Stock, reads that two of three pieces are in Rotterdam, clicks that quantity and sees the item in Rotterdam: what is held there, what is reserved there, what is available there, which movements carried it in and out, and which reservations hold it. One click returns to the item.

**Independent Test**: seed one item with movements into two locations and one active reservation in one of them; open the item preview; opening a location row shows only that item's records at that location, and its three quantities equal what `inventory_read` returns for the same pair.

**Acceptance Scenarios**:
1. **Given** an item with 2 pcs in Rotterdam and 1 pc in Singapore, **When** the clerk opens its stock preview, **Then** each location row shows the available quantity at that location, named as available, in the item's unit.
2. **Given** that preview, **When** the clerk opens the Rotterdam row, **Then** the panel shows this item at Rotterdam only: the three quantities there, the movements of this item into and out of Rotterdam newest first, and the active reservations of this item at Rotterdam — no other item appears.
3. **Given** that panel, **When** the clerk goes back, **Then** they are in the item preview they came from, with the same row open.
4. **Given** the same pair, **When** `inventory_read` is called with that `item_id` and `location_id`, **Then** its physical, reserved and available equal the ones on screen.

---

### User Story 2 — A warehouse as a scope (Priority: P1)
A clerk scopes Warehouse to one location and works there: the stock that lies in it, the reservations held in it, the movements in and out of it. The scope is visible, clearable and survives a reload, exactly as the item scope does today.

**Independent Test**: call each of the three register views with a location scope and with item plus location; compare the rows against the records at that location; reload the page and confirm the scope is restored from the URL.

**Acceptance Scenarios**:
1. **Given** Warehouse · Stock, **When** a location scope is applied, **Then** physical, reserved and available are the quantities *at that location*, the heading states the scope in words, and a chip clears it.
2. **Given** Warehouse · Reservations under a location scope, **When** the list is read, **Then** it holds exactly the reservations whose location is that one.
3. **Given** Warehouse · Movements under a location scope, **When** the list is read, **Then** it holds exactly the movements with that location as origin or destination, and each row says which of the two it is for this scope.
4. **Given** an item scope and a location scope together, **When** any tab is read, **Then** both are applied and both chips are shown.
5. **Given** a scoped register, **When** the page is reloaded or the link is shared, **Then** the scope is restored from the URL.
6. **Given** the state filter `shortage` under a location scope, **When** the list is read, **Then** it holds the items whose available quantity *at that location* is negative.

---

### User Story 3 — The pair, from the location (Priority: P2)
A clerk looking at Rotterdam sees which items lie there and, for any of them, reaches the same item-at-location panel — not the item across the company.

**Independent Test**: open a location in Reality Inspector; each stock row states its quantity kind and unit and leads to the pair panel of US1.

**Acceptance Scenarios**:
1. **Given** a location inspector, **When** the clerk reads the stock section, **Then** its title names the quantity as physical stock and every row shows the item's unit.
2. **Given** a stock row, **When** the clerk opens it, **Then** the item-at-location panel of US1 opens for that item and this location.
3. **Given** a location in Master data, **When** the clerk wants the full list, **Then** Open warehouse opens Warehouse · Stock scoped to that location.

### Edge Cases
- **Pair with no stock**: an item that once lay at a location and netted to zero stays reachable and shows zero with the movements that cancel out. Zero is an answer, not an absence.
- **Overallocated pair**: available below zero at one location is shown as a negative quantity and is found by the `shortage` state under that scope. It is never clamped to zero.
- **Location that stopped allowing stock**: `record_movement` refuses a location with `allows_stock` false, so the case arises when the flag is turned off after records exist. Those records stay readable and the place scope keeps accepting the location. Configuration changes later than history and does not erase it.
- **Parent and child locations**: quantities are recorded at the exact location. A parent location shows what is recorded at the parent, not the sum of its children, and the panel says so where a hierarchy exists.
- **Transfer inside the scope**: a movement whose origin and destination are both the scoped location appears once, and its direction line names both.
- **Unknown identity**: an unknown item or location in a scope is a not-found, distinct from an empty result.
- **Item scope plus location scope with no shared records**: an empty list, not an error.
- **Company-wide and location sums**: the company quantity counts every movement with an origin or destination; the sum of the location quantities equals it only where every movement names a location on the counted side. Where they differ, the item view keeps showing both without silently reconciling them.

## Requirements

### Functional Requirements

- **FR-001**: The item stock preview keeps available stock as its per-location headline and keeps naming it; physical and reserved at that location are reached through FR-002. A quantity inside an Inspector row cannot carry a translated word, so three named quantities per location would mean three rows per location against a twenty-row section; the pair panel is where they belong.
- **FR-002**: Opening a location row from the item stock preview opens an item-at-location explanation: the three quantities at that location, the movements of that item with that location as origin or destination newest first, and the active reservations of that item at that location. No record of another item appears. It opens where the location inspector opens today, and one action returns to the item preview with the same row open.
- **FR-003**: The item-at-location quantities come from the existing shared read contract for the pair (`location_inventory_rows`), the same rows `inventory_read` returns in location view. No second derivation rule is written.
- **FR-004**: The item-at-location panel offers one action each to Warehouse · Movements and Warehouse · Reservations scoped to that item **and** that location.
- **FR-005**: `warehouse_register` accepts an optional location scope on all three views, combinable with the existing item scope, and rejects an unknown location as not-found.
- **FR-006**: Under a location scope, Stock reports physical, reserved and available at that location; Reservations reports the reservations whose location is that one; Movements reports the movements with that location as origin or destination and names the direction per row. Existing state filters apply to the scoped quantities.
- **FR-007**: Under a location scope, Stock lists the items that hold a movement or an active reservation at that location, including those that net to zero, rather than the whole item catalogue. Without a location scope, Stock keeps listing every item as today (spec 254 FR-002).
- **FR-008**: The location scope is shown as a named chip that clears it, it is written to the URL like the item scope, and it is restored on reload and from a shared link.
- **FR-009**: Every screen carrying the location scope states it in words, so a location quantity is never read as a company quantity.
- **FR-010**: The location-scoped stock list is derived set-based, in the query shape the unscoped list already uses. Deriving a register page pair by pair is not acceptable: the shared pair contract issues at least three statements per (item, location) pair, which is right for one pinned pair and wrong for a page of them.
- **FR-011**: The location inspector's stock section names its quantity in its title, each row carries the item's unit, and each row leads to the item-at-location explanation for that item and this location instead of the item across all locations. Master data · Locations offers Open warehouse scoped to that location, where the item family offers it today.
- **FR-012**: Quantities are attributed to the exact location recorded on the movement or reservation. No screen sums a parent location's children or implies that it does.
- **FR-013**: No new MCP tool, projection, table or column is added. The agent reaches the same rows through `inventory_read` in location view, and the web reads the same contract, so both answer the same three quantities for the same pair.
- **FR-014**: New wording exists in both editions, in the agreed German ERP vocabulary (Lagerort, Bestand, physischer Bestand, reserviert, verfügbar, Warenbewegung, Reservierung), and passes the i18n audit.

### Key Entities
No new entity. The feature reads `Movement`, `Reservation`, `Item` and `Location`, tenant-scoped, and names the item/location pair as a read-time observation, never a stored one.

## Success Criteria

### Measurable Outcomes
- **SC-001**: From any quantity shown for an item at a location, a clerk reaches the movements and reservations that produce it in at most two actions, without leaving the item.
- **SC-002**: No screen in scope shows a location quantity without naming which quantity it is and in which unit; where the item view and the location view show the same pair, a reader can tell from the screen why the two numbers differ.
- **SC-003**: The web and `inventory_read` return identical physical, reserved and available for the same pair on the same tenant, proven by a test that calls both.
- **SC-004**: A location-scoped stock page costs the same query shape as the unscoped page and stays within twice its server time on the same tenant, measured back to back on a quiet machine before merge.
- **SC-005**: Every acceptance scenario of US1–US3 is proven by an automated test; the click path of US1 and US3 is proven in a browser script.

## Decisions (owner, 2026-09-23)
1. A location row opens the pair **in place**, in the panel that opens the location today, rather than navigating to the register. The scoped register is one action further (FR-002, FR-004). Reason: the clerk is answering a question about an item and should not lose it.
2. Under a location scope, Stock lists only items with records at that location (FR-007). Reason: the symmetric rule to the existing one on the item side — locations are discovered from the item's own records, never from an unrelated default.
3. The item view keeps one named quantity per location; the location view gains the name and the unit it lacks (FR-001, FR-011). Reason: an Inspector row can compose numbers but not translated words, so the three-way breakdown belongs in the pair panel rather than in three rows per location.

## Assumptions and Dependencies
- Builds on spec 109 (Warehouse registers and their item filter), spec 225 (register workbench, chips, URL state) and spec 254 (Stock lists every item; its shortage warning count). The location scope follows the item scope's existing pattern in all three.
- `location_inventory_rows` and `inventory_read` in location view are treated as the authority for the pair and are not changed. Their cost per pair is acceptable for a pinned pair and is the reason FR-010 forbids using them per row of a register page.
- `stock_at` and `active_reserved` match a location by exact identity; no hierarchy roll-up exists today and none is introduced (FR-012).
- `Reservation.location_id` is recorded on every reservation, so a location scope partitions reservations completely. Movements may carry an origin, a destination or both, which is why the scope matches either side.
- Cost is measured on the local stack against the largest available company, back to back with the unscoped page, on a machine with no other suite running.
- Contracts to update with the behaviour: `docs/WEB_SPEC.md` (one section for this spec), `docs/features/movements.md` and `docs/features/reservations.md` where the location scope changes what is readable, and `docs/SPEC_COVERAGE_MATRIX.md`. If a catalog entry changes, `make docs-generate` runs and its output is committed.

## Requirement Traceability
- FR-001–004 → US1 → `packages/reality-core/tests/test_operational_previews.py` (per-location rows, pair panel, no foreign records), `packages/reality-core/tests/test_stock_at_location.py` (pair parity with `inventory_read`, exact-location attribution, zero and negative pairs), `apps/web/scripts/stock-at-location-browser.mjs` (click path and return).
- FR-005–010 → US2 → `packages/reality-core/tests/test_stock_at_location.py` (scope on three views, combined scopes, state filters, unknown location, statement shape), `apps/web/scripts/stock-at-location-contract.test.mjs` (chip, URL, restored scope).
- FR-011–012 → US3 → `packages/reality-core/tests/test_inspector_register.py` (stock rows name their quantity, unit and scoped target), `apps/web/scripts/stock-at-location-browser.mjs`.
- FR-013 → US1, US2 → `packages/reality-core/tests/test_mcp_read_contract.py` (no new tool; unchanged `inventory_read` surface), `packages/reality-core/tests/test_tool_catalog.py`.
- FR-014 → all → `cd apps/web && npm run i18n:audit`, `make web-build`.
- Full gates: `make lint`, `make test`, `make spec-check`, `make web-build`, `make docs-catalog-check`.
