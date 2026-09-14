# Implementation Plan: Specialized Workspace Views

**Branch**: `049-specialized-workspace-views` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Extend the validated workspace catalog with business destinations backed by the existing fulfillment queue, fulfillment blockers, and item supply/demand projections. Add one bounded tenant-scoped projection-page adapter and one reusable business-table page. Keep five direct View links and add one shared searchable launcher over the complete catalog.

## Technical Context

**Language/Version**: Python 3.12+ and TypeScript 5
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, FastAPI, Pydantic v2, React/Vite
**Storage**: Existing PostgreSQL projection tables; no schema changes
**Testing**: pytest catalog/HTTP tests; Node frontend contracts; i18n audit; TypeScript/Vite build
**Project Type**: Shared Python application services/API plus independent Product Web
**Constraints**: Existing projection builders remain authoritative; tenant filtering precedes limit; browser performs presentation only
**Scale/Scope**: Five workspaces, three existing projections, four specialized business destinations, 50 rows per default page

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Existing projections retain their Reality inputs and evidence identifiers; no write flow changes. | PASS |
| Reality owns operational state | Projection rows remain disposable answers and no status moves onto Documents. | PASS |
| Proven schema only | No table, column, relationship, or migration is added. | PASS |
| Tenant + shared service boundaries | The adapter delegates to tenant-scoped `projection_page`; browser never queries storage. | PASS |
| Spec/test traceability | Catalog, HTTP, frontend, localization, and build proofs map to every FR/DR before implementation. | PASS |
| Explainable web behavior | Business columns lead; existing opaque references remain available for inspection. | PASS |
| Smallest coherent design | One bounded endpoint, generic page, and launcher reuse existing catalogs and projections. | PASS |

Planning may continue: every row is PASS and no exception is requested.

## Repository Structure and Layer Changes

```text
packages/reality-core/config/workspace_catalog.yaml
packages/reality-core/src/reality/catalogs.py
packages/reality-core/src/reality/web/api.py
packages/reality-core/tests/test_application_catalog.py
packages/reality-core/tests/test_http_boundary.py
apps/web/src/api.ts
apps/web/src/App.tsx
apps/web/src/localization.tsx
apps/web/src/tailwind.css
apps/web/scripts/workspace-actions-contract.test.mjs
specs/049-specialized-workspace-views/
```

Catalog metadata is validated in the composer; the existing service read is exposed by a bounded API adapter; Product Web consumes only that adapter. Domain, projection calculation, tools, persistence, and migrations are unchanged.

## Design

### Reality flow

The existing flow remains `SourceRecord → Document/DocumentLine → Commitment/Reservation/Movement → Business Event → disposable ProjectionRow`. This feature only makes existing derived answers discoverable and readable. Projection results never validate commands.

### Service and adapter flow

`Workspace catalog → application reference → Sidebar/More views` supplies discovery. A shared specialized page calls a bounded Web endpoint. The endpoint allowlists the three projections and delegates filtering, ordering, count, and paging to existing `projection_page`.

Four destinations are classified: Orders and Warehouse Queue both reuse `fulfillment_queue`; Fulfillment blockers uses `fulfillment_blockers`; Supply & demand uses `item_supply_demand`. Column definitions are presentation metadata keyed by trusted routes, not inferred from arbitrary payloads.

### Data and migration impact

No migration or backfill. Rolling back removes routes, metadata, and the adapter without changing business data.

### Failure, security, and tenant behavior

Membership remains enforced by the tenant router. The endpoint accepts only the three supported names, caps page size at 100 with 50 as default, filters before limit, and returns 404 for excluded names. Empty projections produce shared empty states.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001-FR-003, FR-011 | catalog unit | Extend `test_application_catalog.py` for specialized classification, alias reuse, and exclusions | Definitions and routes are absent. |
| FR-004-FR-007, FR-012 | frontend contract | Extend `workspace-actions-contract.test.mjs` for five direct Views and complete launcher | All Views render directly; no launcher exists. |
| FR-008-FR-009, DR-001-DR-004 | HTTP/service story | Add bounded, tenant-isolated projection-page cases to `test_http_boundary.py` | No bounded adapter exists. |
| FR-009-FR-010 | frontend contract/build | Assert generic page, columns, paging/search states, then build | Specialized routes and renderer are absent. |
| SC-001-SC-005 | acceptance/quality | Run quickstart matrix, complete gates, and diff review | Current product cannot complete the journeys. |

Tests are added and observed failing before implementation where practical.

## Rollout and Rollback

The reference change is additive. Existing workspace routes and the legacy technical projection endpoint retain compatibility. No migration is required. Rollback reverts the feature commit; projection rows remain untouched.

## Review Risks

- Exposing tenant usage or the price cache as a daily register.
- Letting a generic endpoint accept arbitrary projections or return unbounded rows.
- Showing JSON payloads instead of deliberate business columns.
- Hiding an active specialized route outside the five direct entries.
- Duplicating fulfillment calculation for Orders and Warehouse Queue.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
