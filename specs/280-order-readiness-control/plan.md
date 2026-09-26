# Implementation Plan: Order Readiness Control

**Branch**: `280-order-readiness-control` | **Date**: 2026-09-26 | **Spec**: [spec.md](./spec.md)

## Summary

Add a Sales `Readiness` tab that calls the existing bounded `fulfillment_queue` projection view,
renders only server-provided readiness, line quantities, payment observations, blockers and
metadata, and links to existing Document/Commitment inspectors. Extend only routing, typed client
contracts and presentation. No projection, schema or business-rule change is required.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React
**Primary Dependencies**: existing projection service/API, React/Vite, shared register components
**Storage**: PostgreSQL projection rows, unchanged
**Testing**: pytest projection/API tests; Node presentation/routing/i18n tests; Web build
**Project Type**: existing API plus independent Product Web
**Constraints**: server-side tenant scope/paging; no browser derivation; no GET refresh; four locales
**Scale/Scope**: one new Orders subview over the existing 50-row bounded projection endpoint

## Constitution Check *(blocking gate)*

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Document and Commitment IDs retain Inspector/source traversal. | PASS |
| Reality owns operational state | UI reads the existing Reality projection; no Document status. | PASS |
| Proven schema only | No schema change. | PASS |
| Tenant + shared service boundaries | Existing tenant-scoped projection endpoint and services only. | PASS |
| Spec/test traceability | FR/DR map to backend and UI tests in tasks. | PASS |
| Explainable web behavior | Rows expose blockers, lines, metadata and Inspector links. | PASS |
| Received values not recomputed | Received dates/money pass through; derived values are labelled observations. | PASS |
| Smallest coherent design | Reuse endpoint, projection, router and table primitives. | PASS |

## Repository Structure and Layer Changes

```text
apps/web/src/api.ts                         # typed projection row contract
apps/web/src/unified/routing.ts             # readiness subview
apps/web/src/unified/OrdersPage.tsx          # read + presentation + inspector links
apps/web/src/unified/RegisterTable.tsx       # default column metadata if required
apps/web/src/localization/*                  # four-language labels
apps/web/scripts/*.test.mjs                  # presentation/routing contracts
packages/reality-core/tests/                 # projection/API parity regression
```

## Design

### Reality flow

`SourceRecord → Document/Line → Commitment → Reservation/Movement/Ledger allocation → fulfillment_queue observation`.

### Service and adapter flow

The page calls `GET /projection-views/fulfillment_queue` through `api.specializedProjection`.
The response already carries bounded rows, page data and projection metadata. React renders exact
payload values and routes opaque `document_id` and `commitment_id` values to existing inspectors.

### Data and migration impact

None. Missing snapshots remain missing; reads never build or refresh projections.

### Failure, security, and tenant behavior

Existing API tenant scope and pagination remain authoritative. Pending metadata marks the last
completed rows as stale. Read failure uses shared retry without mutation. Unknown/malformed nested
values render as unavailable rather than producing a browser calculation.

## Test Strategy and Traceability

| Requirement | Test level | Planned proof |
|---|---|---|
| FR-001–FR-006 | UI contract | readiness tab and exact row/line values |
| FR-007–FR-010 | API/UI | current, stale, missing, error and bounded paging |
| FR-011–FR-012 | UI regression | exact Inspector routes; no mutation request |
| FR-013–FR-014 | UI gates | i18n audit, responsive/keyboard structural tests |
| FR-015, DR-001–DR-004 | backend parity | projection endpoint equals shared service/tool output |

## Rollout and Rollback

Additive route/subview with no migration. Rollback removes the tab and typed presentation only.

## Review Risks

- Browser aggregation could become a second rule; tests require exact payload rendering.
- Projection metadata may be absent before first refresh; this must not look like an empty queue.
- Nested rows are untyped today; the client contract must be bounded without changing public API.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Post-design Constitution Check

All rows remain PASS.
