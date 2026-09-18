# Implementation Plan: Order journey timeline

**Date**: 2026-09-18 | **Spec**: [spec.md](spec.md)

## Summary
Replace the active FlightRecorder presentation with a business-lane timeline and a chronological detail panel. Reuse timeline_activity event projection and Inspector. Add a small shared order_journey service for bounded sales-order discovery and authoritative record membership. No persistence or migration.

## Technical Context
Python 3.12+, SQLAlchemy 2, PostgreSQL; existing FastAPI adapters and React/TypeScript with Tailwind tokens. No dependencies added. pytest for service/HTTP tests, node:test for pure layout, existing browser harness for interactions. Each event page is at most 250 records; order search at most 30. Subject membership uses SQL subqueries rather than loading an unbounded graph. Edges are emitted for loaded event subjects and direct parents only; event pagination determines history coverage.

## Constitution Check
| Principle | Before design | After design | Evidence |
|---|---|---|---|
| Source → Evidence → Reality | PASS | PASS | Terminal provenance remains inspectable; typed edges preserve shortest links. |
| Reality authority | PASS | PASS | No document fulfillment fields or browser state calculation. |
| Proven schema | PASS | PASS | No schema changes. |
| Tenant/service boundary | PASS | PASS | Membership and search live in shared services; every subquery scoped. |
| Specification/tests | PASS | PASS | Accepted concept, spec233; tests precede code; tasks trace requirements. |
| Explainable UI | PASS | PASS | Record/event Inspectors and explicit relation labels. |
| Simplicity/storage | PASS | PASS | SQL subqueries, existing projection, no graph store or dependency. |
| Received values | PASS | PASS | Existing event presentation; no recomputed prices/totals. |

## Project Structure
- `packages/reality-core/src/reality/services/order_journey.py`: search, membership SQL predicates, event page and loaded-record edges.
- `packages/reality-core/src/reality/services/core.py`: optional internal subject criterion for timeline_activity, applied before LIMIT.
- `packages/reality-core/src/reality/web/api.py`: GET `/order-journeys` and `/order-journeys/{id}`.
- `apps/web/src/api.ts`: typed reads.
- `apps/web/src/unified/OrderJourneyTimeline.tsx`: new presentation, selection, order search, paging and refresh.
- `apps/web/src/unified/orderJourneyLayout.ts`: recording-time viewport and collision layout only.
- `apps/web/src/unified/FlightRecorder.tsx`: retain old utility source initially or replace entrypoint; active page mounts new timeline.
- `apps/web/src/localization.tsx`, `tailwind.css`: translations and theme-aware styles.
- Tests: `packages/reality-core/tests/test_order_journey.py`, `apps/web/scripts/order-journey-layout.test.mjs`, `apps/web/scripts/order-journey-browser.mjs` and affected existing contracts.

## Design and sequencing
Domain unchanged → service regression stories → read composition → HTTP adapters → layout tests → browser integration. Every displayed event uses the existing event serializer. Source/evidence are terminal context, not a traversal path to other orders. Relationships use current held FKs and are labeled record relationships, not historic causation. Source Inspector handles further provenance.

Selection keeps a pinned event and selected order. Tenant changes remount state. Order changes abort/ignore prior requests. Paging merges by event ID, newest refresh reuses paging with a forward cursor to avoid missing bursts. Existing 30-second visible-tab refresh is sufficient; no new health polling or background scheduling. The chart starts fit to business events; explicit ranges remain fixed until the user changes them. Collision grouping is based on pixel distance, not business grouping. The detail list includes all loaded source/evidence and business events.

## Verification and rollback
Run meaningful failing tests first, then targeted service/adapter/layout/browser checks, followed by `make lint`, `make test`, `make web-build`, `make spec-check`, and docs catalog checks as applicable. PostgreSQL migration checks are in the existing suite; no new migration. Keep review evidence honest if environment blocks a gate. Revert the adapter/presentation change to restore prior behavior; no stored state needs rollback. Do not alter V0 completion status.

## Risks
Incomplete event coverage is explicit. Unknown event times are never synthesized. No sales-order invoice/payment traversal; a shared invoice must not become an order balance. Wide layout changes spec162 intentionally. Browser tests for the retired active recorder must be updated to assert the new contract rather than preserve obsolete selectors.

## Complexity Tracking
No constitutional exceptions. No new dependency, table or business tool catalog entry.
