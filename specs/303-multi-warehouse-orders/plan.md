# Implementation Plan: Orders Served From Several Warehouses

**Branch**: `303-multi-warehouse-orders` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

One order can now be served from several warehouses:
- A person reserves the rest of a line at another warehouse they name.
- Readiness and shipping count every reservation with the stock at its own warehouse.
- Each warehouse ships its part as its own package against the one promise.

When the order's warehouse cannot cover a line but another can, "Stock in another warehouse" names where the stock is and offers to reserve there or to prepare a transfer, both through the review. No schema changes.

See [research.md](research.md), [data-model.md](data-model.md) and [contracts/several-warehouses.md](contracts/several-warehouses.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Primary Dependencies**: SQLAlchemy 2, FastAPI, Typer, pytest

**Storage**: PostgreSQL; no migration

**Testing**:
- service, exception, adapter and business-story tests
- the existing readiness, queue and shipment suites as regression
- web `test:i18n`, the audit, the build and the browser suite fixtures
- the full backend suite

**Target Platform**: Backend, Web, MCP, CLI

**Project Type**: Domain rule change with one derived class and adapters

**Performance Goals**: Readiness and the queue read reservations and stock grouped by location, as they already do by item. The class reads every open promise's stock in grouped queries, and a test pins the statement count.

**Constraints**:
- Unchanged results when every reservation is at home.
- Tenant-scoped.
- Reviewed tools.
- No automatic distribution.

**Scale/Scope**: the reservation service and its review, one readiness rule in three readers, the dispatch gate, one class, the reserve form and two prefilled actions, and three stories.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Reservations and movements are Reality; nothing new is interpreted. |
| II. Reality is the operational authority | PASS | No document status; readiness is read from reservations and stock. |
| III. Proven schema only | PASS | No new field: `Reservation.location_id` already holds the location. |
| IV. Tenant and service boundaries | PASS | One service path behind MCP, Web and CLI; locations resolved per tenant. |
| V. Specification and test evidence | PASS | Tests planned before each phase, with regression on the existing readiness suites. |
| VI. Explainable Web product | PASS | The finding traces to the promise and each location's stock; the delivery shows reservations per location. |
| VII. Simplicity and storage discipline | PASS | One shared readiness rule; no routing, flag or suggestion table. |
| VIII. Received values are recorded, never recomputed | PASS | Stated quantities are untouched; proposed quantities are read-time suggestions. |

## Design

1. **Reservation**: an optional `location_id` through `_preview_reservation`, `reserve`, the delivery review (`delivery_actions` "reserve") and the MCP schema. A serving-location check comes first, then availability at the named location.
2. **Readiness rule**: one helper, `ready_by_location(reserved_by_location, physical_by_location)`, used by:
   - `fulfillment_readiness`;
   - the fulfilment queue and blockers projection (physical per (item, location) for the locations reservations hold);
   - the packaged dispatch gate and the reviewed shipment preview (per movement's `from_location_id`).
3. **Class `stock_in_another_location`**: in `services/exceptions.py`, with grouped reads of open customer promises, active reservations per (item, location), and stock per (item, location) for serving locations. It is registered everywhere the class gates name, ordered after `outgoing_commitment_at_risk` in severity order (it is normal). The catalog entry, German label and translations follow.
4. **Web**:
   - The reserve form gets a location choice.
   - The attention page gets "Reserve there" and "Prepare transfer", prefilled from the trace.
   - The delivery case lists reservations by location.
5. **Stories**:
   - D02: 6 at home and 4 in Munich are reserved, shipped as two packages, and the promise is fulfilled.
   - B06: all stock in Munich. The finding appears, a reviewed transfer is made, it clears, and the line is reserved at home.
   - A02: a multi-line order with lines served from two warehouses, ready and shipped.
   - Then the Guide promotion, coverage, roadmap and matrix.

## Project Structure

```text
specs/303-multi-warehouse-orders/{spec,plan,research,data-model,quickstart,tasks}.md, contracts/several-warehouses.md
packages/reality-core/src/reality/services/{core.py, fulfillment_readiness.py, projections.py, shipments.py, shipment_actions.py, delivery_actions.py, exceptions.py}
packages/reality-core/src/reality/mcp/catalog.py, cli/app.py, config/*
packages/reality-core/tests/{test_multi_warehouse_reservations.py, test_stock_in_another_location.py, test_multi_warehouse_adapters.py}, scenarios/test_catalog_orders_and_shipments.py
apps/web/src/unified/{ActionCard.tsx, AttentionPage.tsx, DeliveryCase.tsx}, localization.tsx
```

## Rollback

Code only. Reservations made at another location stay valid records. Rolled back, readiness would again read the own location only, and those promises would show as not ready.

## Complexity Tracking

No Constitution violations.
