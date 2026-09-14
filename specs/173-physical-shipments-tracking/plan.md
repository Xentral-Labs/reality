# Implementation Plan: Physical Shipments and Tracking

**Branch**: `173-physical-shipments-tracking` | **Date**: 2026-09-11 | **Spec**: [spec.md](spec.md)

## Summary

Add logistics context above immutable Movements: Shipment groups one direction, purpose and
counterparty; ShipmentPackage carries optional received carrier/tracking; Movement optionally
names its exact Package; append-only ShipmentEvent and supersession records retain logistics
observations. Current state derives from effective Movements and current events. Five reviewed
commands and two reads serve Web, CLI, API, MCP and Chat. Existing stock, fulfillment and return
rules remain authoritative.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React
**Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite
**Testing**: pytest unit/service/story/adapter; frontend contract, i18n, build and browser tests
**Constraints**: Decimal, UTC, opaque IDs, lossless source, tenant scope, no document state
**Scale**: Page size 1–100; benchmark a representative 10,000-Shipment tenant; no carrier connector

## Constitution Check *(blocking gate)*

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Lossless SourceRecord; optional Evidence; Shipment/Package context; Movement truth; attributed events | PASS |
| Reality owns operational state | Movement owns stock/fulfillment; shipment observations are derived | PASS |
| Proven schema only | Direction/purpose validate/filter; Package groups contents; tracking/events search, reconcile and explain | PASS |
| Tenant + shared boundaries | Tenant-scoped records/queries; every adapter calls shared services/tools | PASS |
| Spec/test traceability | FR groups map to failing-first tests and tasks | PASS |
| Explainable Web | Detail exposes effective Movements, events, sources and shortest links | PASS |
| Received values not recomputed | Carrier/events recorded as stated; comparisons are derived | PASS |
| Smallest coherent design | No announced-line table, status, Document FK, connector or history backfill | PASS |

Post-design check remains all PASS. No exception is requested.

**Architecture/domain approval**: Owner-approved on 2026-09-11, including the new tables,
Movement → ShipmentPackage shortest link, derived-state boundary, command inventory and
no-backfill migration.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/db/core.py
packages/reality-core/migrations/versions/
packages/reality-core/src/reality/domain/shipments.py
packages/reality-core/src/reality/services/shipments.py
packages/reality-core/src/reality/services/shipment_actions.py
packages/reality-core/src/reality/tools/application.py
packages/reality-core/src/reality/web/api.py
packages/reality-core/src/reality/cli/app.py
packages/reality-core/src/reality/mcp/catalog.py
packages/reality-core/config/*.yaml
packages/reality-core/tests/test_shipments_*.py
apps/web/src/api.ts
apps/web/src/unified/
apps/web/scripts/unified-shipments-browser.mjs
docs/DATA_MODEL.md
docs/WEB_SPEC.md
docs/features/shipments.md
```

Dependency order is domain → services → tools → adapters. Transports validate shape only.

## Design

### Reality flow

```text
SourceRecord ────────────────┐
  └─ Document/Line (optional)├─> Commitment / ReturnAnnouncement
                             │          │
SourceRecord ─> Shipment ─> Package <─ Movement
                  │                    └─ existing Commitment/return links
                  └────── ShipmentEvent ─> optional supersession
```

Movement → Package is the shortest exact contents link and does not replace Movement's existing
business-purpose links. Shipment stores no Document/Line FK. An external statement may link
directly to SourceRecord without fabricated Evidence.

### Service and adapter flow

`shipments.py` owns reads, validation, derivation and atomic primitives.
`shipment_actions.py` owns prepare/review/execute/reconcile and invokes existing Movement services
inside the transaction. Application tools expose `shipments_list`, `shipment_explain`,
`shipment_notice_record`, `shipment_dispatch`, `shipment_receive`, `shipment_event_record` and
`shipment_event_supersede`. CLI, FastAPI, MCP, Chat and Web only translate these contracts.

### Data and migration impact

Add `shipment`, `shipment_package`, `shipment_event`, `shipment_event_supersession`, and nullable
`movement.shipment_package_id`; see [data-model.md](data-model.md). All use opaque IDs and tenant
indexes. No backfill: null means no Package was recorded. Existing FK style is retained, with
tenant equality enforced by services and proven by tests.

### Failure, security, and tenant behavior

Use existing delivery/inventory locks before validation. Review fingerprints bind direction,
purpose, party, package/tracking, source/event revision, every Movement argument, commitments,
returns, stock/capacity and tracking identities. Any failure rolls back. Existing action receipts
give replay and lost-response recovery. Foreign IDs are not found; logs omit raw payloads.

### Derived observations

Announced comes from current events; dispatched/received and their times come from effective
Movements; externally delivered requires a current delivered event for every applicable Package;
exceptions come from current event history. Detail returns components and preserves mixed Package
state. Nothing derived is stored.

## Test Strategy and Traceability

| Requirements | Level | Planned proof | Initial failure |
|---|---|---|---|
| FR-001–011, DR-001–010 | migration/domain/service | `test_shipments_domain.py`, `test_shipments_migration.py` | model/rules absent |
| FR-012–013, 025, 029–030 | service/query | `test_shipment_reads.py` | read absent |
| FR-014–018 | service/story | `test_shipment_actions.py`, `test_shipment_story.py` | actions absent |
| FR-019–021, 028 | Web | contracts and `unified-shipments-browser.mjs` | UI absent |
| FR-022 | CLI | `test_shipment_cli.py` | commands absent |
| FR-023 | API | `test_shipment_api.py` | routes absent |
| FR-024 | MCP/Chat | `test_shipment_tools.py`, catalog/guidance tests | tools absent |
| FR-026–027 | catalog/regression | catalog, migration, Movement/return suites | events absent |
| SC-007 | PostgreSQL | measured plan/budget test | indexes unproven |

Tests are added and observed failing before implementation where practical. Completion requires
backend, migration, Web, browser, localization, lint, build, spec and diff gates green.

## Rollout and Rollback

Deploy additive migration before backend and Web. Old code ignores new tables and nullable link.
Application rollback is safe while tables remain. Database downgrade follows writer shutdown and
explicit acceptance of feature-data removal; it never rewrites pre-feature Movements.

## Review Risks

- Conflating carrier delivery, warehouse receipt and Commitment fulfillment.
- Copying Movement/return rules into shipment orchestration.
- Partial multi-line or duplicate replay effects.
- Cross-tenant tracking/package joins.
- Treating tracking text as unique identity.
- Ambiguous Commitment-versus-Shipment Web labels.

## Complexity Tracking

| Constitution exception | Why | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
