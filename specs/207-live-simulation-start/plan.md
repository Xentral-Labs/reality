# Implementation Plan: Live simulation start and header

**Date**: 2026-09-15 | **Spec**: [spec.md](spec.md)
**Language**: English

## Summary and Technical Context

Python 3.12, SQLAlchemy 2/PostgreSQL and existing shared scheduling services; React/TypeScript/Vite. No dependency or database migration. Two bounded slices: an opt-in initial interval sequence and a read-only header link.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Existing enqueue_source/process_import_job_bound | PASS |
| Reality owns operational state | No document state added | PASS |
| Proven schema only | Existing JSON scheduling envelope; no business columns | PASS |
| Tenant + shared services | Existing locks, scoped queries, authorization and Demo Data reader | PASS |
| Spec/test traceability | Tests precede both slices, mapping below | PASS |
| Explainable web | Link to existing live activity and source drilldowns | PASS |
| Received values not recomputed | Existing synthetic producer and intake | PASS |
| Smallest coherent design | Opt-in shared timing, no new job type, queue or process | PASS |

Post-design check: all PASS. Product scope is explicitly authorized in the conversation. The scheduling extension is reviewed here: it adds finite initial offsets within existing timing infrastructure, not a new scheduler or external-effect handler.

## Repository Structure and Layer Changes

- `packages/reality-core/src/reality/scheduling/timing.py`: validate bounded offsets and calculate coalesced next eligibility.
- `packages/reality-core/src/reality/services/scheduled_jobs.py`: optional `initial_offsets_seconds` on internal create_schedule; persist activation anchor in the existing envelope; freeze an initial marker per run. The existing preview includes initial offsets; ordinary callers remain unchanged.
- `packages/reality-core/src/reality/services/demo_data.py`: fresh Start requests offsets 0/12/24 only.
- `packages/reality-core/src/reality/jobs/handlers/demo_data.py`: initial occurrences call existing produce once, all later occurrences call existing stochastic plan.
- `apps/web/src/unified/LiveSimulationIndicator.tsx`, `HeaderControls.tsx`, `Shell.tsx`: compact link beside header controls, visible on mobile outside the overflow menu.
- `apps/web/src/api.ts`: optional AbortSignal on existing status read only.
- `apps/web/src/localization.tsx`, `tailwind.css`: reuse existing Live simulation translation, pulse/reduced-motion styling.

## Design

### Reality and service flow

Confirmed setup → Demo Start → shared schedule → durable occurrence → existing synthetic source producer → normal intake → Document/Line → Commitment. Amounts remain source-stated. No header mutation.

### Timing and failure semantics

Use ascending absolute offsets (0,12,24), interval-only, bounded to ten slots and one hour, with minimum five-second spacing. Store offsets and first activation time in the existing configuration envelope outside validated job arguments. Assign new dictionaries to preserve frozen run inputs. Initial activation is immediate; materialization skips past initial slots and transitions to the regular grid after the last slot. One unfinished run, tenant queue cap, retries, claim fencing and transaction rollback remain unchanged. Pause and timing updates discard remaining initial metadata; ordinary resume never re-arms it. Retry uses the frozen occurrence marker. Old schedules have no metadata and keep current behavior.

### Header

Read existing Demo Data status only for owner Playground companies. Fresh read required; bootstrap state is not authority. Poll every five seconds while visible with an eight-second abort, no overlapping requests, cancellation on unmount/company change; failed reads hide indicator. Refresh on local source controls via a tenant-scoped notification. Show only `state=running` and `derived_state` absent/running. Link uses existing routing with current tenant, text Live simulation and a small pulse dot; text can collapse on narrow screens while accessible name remains. No health probes or business activity polling added.

### Data and migration impact

No migration. Existing JSON scheduling metadata is coordination, not business authority. API/MCP input schemas and executable catalogs do not change.

## Test Strategy and Traceability

| Requirement | Tests | Expected initial failure |
|---|---|---|
| FR-001, DR-001 | `tests/test_demo_data_startup.py`, existing company setup/intake suites | first arrival waits and random zero emits nothing |
| FR-002, DR-002 | `tests/test_scheduled_job_startup.py`, timing/security/recovery suites | optional initial timing unsupported |
| FR-003–006, DR-003 | `apps/web/scripts/live-simulation-header-browser.mjs` | indicator absent |

Run complete pytest, Ruff, spec policy, frontend contracts/build/format/i18n, docs catalog check, focused browser acceptance, migration tests as part of pytest. Inspect screenshots at desktop/mobile and reduced-motion behavior. Record actual results without marking red gates complete.

## Rollout and Rollback

Rebuild scheduler/worker with API code; frontend reloads locally. Existing simulations retain normal timing, only new starts opt in. Reverting code leaves old readers ignoring envelope metadata and the already scheduled next occurrence; later timing returns to normal. No source deletion or database downgrade.

## Review Risks

- Frozen JSON accidentally shared across schedule/run; prove with retry test.
- Catch-up burst or initial re-arm on resume; prove with clock-controlled tests.
- Cross-company late read or stale positive state; prove browser transitions.
- Narrow header collision and reduced motion; inspect actual browser layout.

## Complexity Tracking

None; no constitutional exception.
