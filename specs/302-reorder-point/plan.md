# Implementation Plan: Reorder Point and Replenishment Proposal

**Branch**: `302-reorder-point` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

A company states, per item and location, the stock level at which it reorders and how much it then orders.

When available stock at a location plus what is on its way there falls to that level, "Reorder point reached" names the item and location with the proposed quantity. It also names the supplier and price when exactly one purchase price list states them.

From the entry the buyer prepares a purchase order through the existing reviewed `order_create`. Once the order is placed, its open promise counts as incoming and the entry is gone.

Nothing is stored but the stated point.

See [research.md](research.md), [data-model.md](data-model.md) and [contracts/reorder-points.md](contracts/reorder-points.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Primary Dependencies**: SQLAlchemy 2, Alembic, FastAPI, Typer, pytest

**Storage**: PostgreSQL; migration `0107_item_reorder_point`

**Testing**:
- service, exception, adapter and business-story tests
- migration test
- web `test:i18n`, the audit and the build
- the full backend suite

**Target Platform**: Backend, Web, MCP, CLI

**Project Type**: New typed setting, one derived class, adapters

**Performance Goals**: The class reads every reorder point and its stock, reservations, incoming and price candidates in grouped queries. The statement count does not grow with the number of points, and a test pins this bound. The one exception is the shared price rule: `resolve_price` runs once for each reported entry with exactly one supplier, rather than re-implementing the rule here.

**Constraints**:
- derived at read time;
- tenant-scoped;
- reviewed tools;
- `order_create` unchanged;
- the spec 301 unit rule for proposed cartons and old promises.

**Scale/Scope**: one table, one service module, three tools, one class, two web surfaces, a CLI group and a story.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The reorder point is a company statement. The proposal reads stock, reservations and promises. |
| II. Reality is the operational authority | PASS | No document status. Coverage by an order is read from its open promise. |
| III. Proven schema only | PASS | Every read of the class filters and compares on `reorder_point` and proposes `reorder_quantity`. The unique key per item and location is a constraint a fact cannot carry. |
| IV. Tenant and service boundaries | PASS | One service path behind MCP, Web and CLI. Composite tenant FKs. |
| V. Specification and test evidence | PASS | Tests are planned before each phase. |
| VI. Explainable Web product | PASS | The entry traces to the point, the stock, the promises and the price list entry. |
| VII. Simplicity and storage discipline | PASS | No proposal table, no forecast, no preferred-supplier field. |
| VIII. Received values are recorded, never recomputed | PASS | Point and quantity are kept as stated. The carton figure is the stated factor applied once, at read. |

## Design

### Schema

Migration `0107_item_reorder_point` creates the table described in `data-model.md`. The downgrade refuses while points exist.

### Services (`services/reorder_points.py`)

- Read, set and remove the points.
- Validation: active stocked item, stock-capable location, and values in range.
- Concurrency: the review check against `_expected` under the tenant's business lock.
- Events `reorder_point.set` and `reorder_point.removed`.

### Derivation (`services/exceptions.py`, `_reorder_point_reached_exceptions`)

1. Read all points of the tenant with their items in one query.
2. **Physical stock** per (item, location): grouped movement legs, less corrected movements, the same correction-aware rule as `_movement_quantities`.
3. **Reserved** per (item, location): active reservations.
4. **Incoming** per (item, location): open supplier promises.
   - The open quantity uses `fulfillment_expressions` and the effective (revised) quantity.
   - The held unit comes from `promise_held_unit`, converted with `in_unit` for promises recorded before spec 301.
   - A promise that cannot be converted is left out. Units not comparable already names it.
5. **Price candidates** per item: suppliers with a purchase-direction list that prices the item at the evaluation time.
   - Lists reach a supplier directly (`PartyPriceList`) or through a group (`PartyGroupPriceList` × members).
   - With exactly one candidate, `resolve_price` runs once for the proposed quantity and unit.
6. Report available plus incoming ≤ point. The proposed quantity goes through `in_unit(item, quantity, item.unit, item.purchase_unit)`.

**Registration:**
- `CLASS_ORDER` after `item_oversold`, and `DERIVATION_REGISTRY`.
- The catalogs tuple, the YAML entry and the test lists.
- The reference catalog: `traces_only` on `ItemReorderPoint`.
- `resource_catalog.yaml`: item and location resources, with the German label "Meldebestand erreicht".
- Narrowed refresh: the class is not in `CLASS_DEPENDENCIES`, so every change re-evaluates it. Price list, entry, assignment and group events now invalidate Operational Exceptions too.
- `next_clock_moment`: none, beyond the price-validity boundaries if the shared rule offers them. Otherwise this is recorded as a limitation.

### Tools and adapters

- Application tools `reorder_points`, `reorder_point_set` and `reorder_point_remove`, with reviews.
- MCP tools per the contract, plus the MCP topic and capability guidance.
- Web endpoints `GET /reorder-points` and `POST /reorder-points/proposals`.
- CLI group `reorder-point`.
- Command catalog descriptions.

### Web

- **Master-data item detail**: a "Reorder points" section, one row per location, with `ReorderPointCard` (set, change, remove → review → confirm).
- **`AttentionPage`**: a "Prepare purchase order" button for `reorder_point_reached`. `OrderCard` gains an optional `initial` draft.
- Translations in de/nl/es.

### Story and Guide

- **G02** in `tests/scenarios/test_catalog_purchasing.py`:
  1. Hamburg holds 12 with a point of 20 and a quantity of 48 in cartons of 12.
  2. The entry proposes 4 cartons from the one supplier at the list price, while Munich, full, is not reported (control).
  3. The buyer prepares and confirms the reviewed `order_create`, and the entry clears.
  4. A reservation that brings stock back under the point brings the entry back.
- Then the catalog promotion with story-first evidence, coverage, roadmap, coverage matrix and `make docs-generate`.

## Project Structure

```text
specs/302-reorder-point/{spec,plan,research,data-model,quickstart,tasks}.md, contracts/reorder-points.md
packages/reality-core/
├── migrations/versions/0107_item_reorder_point.py
├── src/reality/db/core.py (ItemReorderPoint)
├── src/reality/services/{reorder_points.py (new), exceptions.py}
├── src/reality/tools/application.py, mcp/catalog.py, cli/app.py, web/api.py
├── config/{operational_exception_catalog.yaml, service_refusals.json, data_model.yaml, resource_catalog.yaml, reference_catalog, business_journey_catalog.yaml}
└── tests/{test_reorder_points.py, test_reorder_point_reached.py, test_reorder_point_adapters.py}, scenarios/test_catalog_purchasing.py
apps/web/src/unified/{AttentionPage.tsx, OrderCard.tsx, ReorderPointCard.tsx (new), master-data item detail}, api.ts, localization.tsx
```

## Rollback

The downgrade drops the table and refuses while points exist. Nothing else depends on it: purchase orders prepared from an entry are ordinary orders.

## Complexity Tracking

No Constitution violations.
