# Implementation Plan: Multichannel Oversell, Deadlines and Peak Intake

**Branch**: `300-multichannel-oversell` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

This spec adds two findings and one measurement:
- `item_oversold` reports, per item, open customer demand above stock on hand plus open supplier supply, with the orders grouped by their stated sales channel.
- `outgoing_commitment_due_soon` reports an open customer promise less than one day before its date, reserved or not, ahead of the overdue class.
- A benchmark measures 10,000 Shopify orders through the import-job path with parallel processes and checks the reservations; L07 is promoted only if it meets two hours.

See [research.md](research.md), [data-model.md](data-model.md) and [contracts/findings-and-benchmark.md](contracts/findings-and-benchmark.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React, labels only)

**Primary Dependencies**: SQLAlchemy 2, pytest

**Storage**: PostgreSQL; no migration

**Testing**:
- service and business-story tests
- a small benchmark run as a test
- web `test:i18n` and the audit
- the full backend suite

**Target Platform**: Backend; the Web, MCP and CLI show the findings through the existing exception surfaces

**Project Type**: Derived findings and a developer benchmark

**Performance Goals**:
- `item_oversold` reads demand and supply in grouped queries; the statement count does not grow with items or promises.
- The deadline class adds no query to `_commitment_exceptions`.

**Constraints**: read-time derivation; stated channel and dates; tenant-scoped; no new mutation.

**Scale/Scope**: two classes, one clock change, one benchmark, three stories and the Guide.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Findings read promises, movements and documents; nothing new is recorded. |
| II. Reality is the operational authority | PASS | No status on documents; both findings are derived at read time. |
| III. Proven schema only | PASS | No schema change; the channel is the existing typed `sales_channel`. |
| IV. Tenant and service boundaries | PASS | Shared exception derivation; every query tenant-scoped. |
| V. Specification and test evidence | PASS | Tests planned before each phase, with positive controls. |
| VI. Explainable Web product | PASS | Each finding names its promises, orders and channels. |
| VII. Simplicity and storage discipline | PASS | Two classes in the existing registry; the benchmark is a tool, not a feature. |
| VIII. Received values are recorded, never recomputed | PASS | Quantities and dates are read as stated; only compared. |

## Design

### `item_oversold`

`_item_oversold_exceptions` (in `services/exceptions.py`):
- One grouped query reads, per item and unit, the open quantity of open customer-delivery promises, using the SQL open-quantity expression with revisions applied.
- One query reads the same for supplier-delivery promises, and one reads item-wide stock from movements.
- Items whose demand in the item's own unit exceeds stock plus supply are reported.
- A second read, for those items only, fetches the promises with their order and `sales_channel` for the channel breakdown and the trace.

Gates: `CLASS_ORDER`, registry, dependencies (movement, commitment, reservation and document events), catalogs, labels and the reference catalog.

### `outgoing_commitment_due_soon`

In `_commitment_exceptions`:
- After the overdue branch, a promise with remaining quantity and a date in force within `DUE_SOON_MARGIN` is reported.
- Its causes are `insufficient_reservation` when short and `promise_was_revised` when revised.
- The at-risk branch follows as before.

`next_clock_moment` adds `due_at − DUE_SOON_MARGIN`. `CLOCK_READING` gains the class.

### Benchmark `benchmarks/peak_intake`

The runner:
1. Builds a disposable company with items, stock and a Shopify connection.
2. Enqueues N Shopify order payloads.
3. Works them with `process_pending_import_jobs` from P processes.
4. Reserves every promise from four connections.
5. Checks the invariants and writes JSON and a summary.

`tests/test_peak_intake_benchmark.py` runs it at 50 orders and 2 processes.

### Stories and Guide

- B14 and L02 go in `tests/scenarios/test_catalog_orders_and_shipments.py`.
- L07 is promoted only on a measured pass; otherwise its limitation states the figure.
- Then the catalog, keywords (English and German), the neighbouring-question check, coverage, the roadmap and the coverage matrix.

## Project Structure

```text
specs/300-multichannel-oversell/{spec,plan,research,data-model,quickstart,tasks,results}.md, contracts/findings-and-benchmark.md
packages/reality-core/
├── src/reality/services/exceptions.py, catalogs.py
├── config/operational_exception_catalog.yaml, reference_catalog.yaml, resource_catalog.yaml
├── benchmarks/peak_intake/{__init__,runner,company,report}.py
└── tests/{test_item_oversold.py, test_deadline_due_soon.py, test_peak_intake_benchmark.py}, scenarios/test_catalog_orders_and_shipments.py
apps/web/src/localization.tsx (labels and resolutions)
```

## Rollback

Code only: remove the two classes and the benchmark. Nothing is stored.

## Complexity Tracking

No Constitution violations.
