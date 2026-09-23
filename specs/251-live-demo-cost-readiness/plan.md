# Implementation Plan: Live Demo Cost Readiness

**Branch**: `251-live-demo-cost-readiness` | **Date**: 2026-09-22 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Extend the canonical `international_demo` profile so every positively stocked item is
covered by explicit source-backed acquisition evidence and one final batch inventory
review. Verify that bounded coverage before the setup run can become ready, and publish
the existing inventory/contribution generations from the same worker transaction. For
continuous Demo Data, make freshness depend only on relevant physical and reviewed-cost
events: normal order and settlement intake remains current, while changed authority is
truthfully stale until explicit owner review. Reads and UI continue to use the existing
costing services and freshness models; no demo calculator, browser timer, automatic
financial authority, or second queue is introduced.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript where frontend is in scope
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite as applicable
**Storage**: PostgreSQL; immutable object storage only for proven source binaries
**Testing**: pytest business stories/integration/unit; frontend build and focused UI tests
**Project Type**: backend services/API/CLI plus independent frontend
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope
**Scale/Scope**: One canonical 18-item profile, its declared contribution portfolio,
and the relevant-event behavior of one bounded synthetic intake occurrence.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Demo acquisition values remain in immutable `SourceRecord` payloads and are linked through movements and retained cost review members. | PASS |
| Reality owns operational state | Stock, consumption, freshness and contribution stay derived from movements, allocations, reviews and event cutoffs; no document status is added. | PASS |
| Proven schema only | Existing source, review, generation, setup-progress and scheduled-run structures are sufficient; no schema change is planned. | PASS |
| Tenant + shared service boundaries | Profile initialization and freshness reads call tenant-scoped costing services; Web/MCP/Chat/CLI/API remain readers of those services. | PASS |
| Spec/test traceability | The table below maps FR/DR groups to story, service, job and browser proofs. | PASS |
| Explainable web behavior | Existing cost explanation and freshness components expose evidence, cutoff and failure reason; setup adds only truthful progress from the setup receipt. | PASS |
| Received values not recomputed | Authored demo purchase/acquisition values are recorded as received; DB1/DB2 remain disposable observations produced by existing algorithms. | PASS |
| Smallest coherent design | Reuse batch reviews and shared relevant-event reads; reject a demo-only calculator, automatic financial review and client polling as a trigger. | PASS |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/domain/       # pure rules, if needed
packages/reality-core/src/reality/services/demo_profile.py
packages/reality-core/src/reality/services/company_setup.py
packages/reality-core/src/reality/services/costing.py
packages/reality-core/src/reality/services/scheduled_jobs.py
packages/reality-core/src/reality/jobs/handlers/company_setup.py
packages/reality-core/tests/test_demo_costing_profile.py
packages/reality-core/tests/test_demo_data_intake.py
packages/reality-core/tests/test_company_setup_jobs.py
apps/web/src/unified/setupProgress.ts
apps/web/src/components/CompanySetup.tsx
apps/web/scripts/company-setup-browser.mjs
docs/features/company-setup-demo.md
```

**Files/layers affected**: No new domain model or adapter-side business rule. The
profile authors evidence, services derive/validate bounded scope, registered workers
execute it, and the Web renders receipt state only. Exact filenames may narrow after
the failing tests identify the existing service seam.

## Design

### Reality flow

For initial stock, the profile records a lossless acquisition-evidence source for each
receipt/opening movement. One batch inventory review binds those movements to the
company owner and explicit positive cost. Existing commercial-match and contribution
reviews bind declared invoice lines to the reviewed consumed slices and received
selling evidence. Existing generation builders publish disposable observations at an
exact event cutoff.

For live intake, interpreted SourceRecords create normal documents and Reality records.
Shared costing reads compare a review only with relevant physical and reviewed-cost
events for its opaque scope. Orders, invoices, credits and payments that do not change
that authority leave the observation current. A new movement or withdrawn selling-cost
attribution makes the current result stale; only the existing confirmed review path can
establish replacement authority.

### Service and adapter flow

`company_setup.initialize` seeds the profile, establishes calculation readiness,
verifies coverage, then starts live simulation only after the verified cutoff and
rebuilds ordinary projections. Inline retry calls the same orchestration service.
`demo.generate_orders` and `demo.settle_orders` remain ordinary source-intake handlers;
they do not manufacture a financial review. All interactive adapters keep calling
existing costing read/action services.

### Data and migration impact

No migration. Reuse `PlaygroundRun.initialization_progress` for a compact immutable
readiness summary, existing retained review/generation tables for evidence and results,
and existing event history for freshness. Historical tenants are unchanged.

### Failure, security, and tenant behavior

Every lookup carries the tenant and opaque subject identity. Foreign identities are
refused as not found. Initial readiness is atomic with setup: failure leaves the receipt
retryable and not ready. Setup retry relies on existing leases and idempotent builders.
No intake handler may turn a newer event into an unconfirmed financial review.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-004, DR-001–DR-003 | story/service | `test_demo_costing_profile.py`: full positive-stock census and declared contribution portfolio are current and explainable at readiness | Existing seed reviews only its bounded P03/P05 portfolio. |
| FR-005–FR-006, FR-012, FR-014 | job/API/browser | `test_company_setup_jobs.py` and `company-setup-browser.mjs`: calculation stage, cutoff, failure/retry and visible terminal state | Setup currently rebuilds projections and may start live intake before cost coverage is verified. |
| FR-007–FR-010, DR-004–DR-005 | service/story | Relevant-event, batch-review and selling-cost tests prove unrelated intake remains current and changed authority becomes stale | The prior company-wide cursor made unrelated events stale. |
| FR-011 | adapter parity | Existing Web/API/MCP/CLI costing contract tests plus a fresh-demo parity story | Some demo scopes are uninitialized, so parity cannot prove current values. |
| FR-013 | service | Historical demo tenant remains byte-for-byte unchanged until an explicit confirmed repair path is invoked | A broad startup repair would violate the non-goal. |
| DR-006–DR-007 | isolation/schema | Existing cross-tenant costing tests and migration/schema diff check | Relevant-event reads must preserve tenant scope. |

## Rollout and Rollback

Ship core, scheduler, worker, API and Web from one revision. No migration or backfill is
required. Setup failures expose a bounded diagnostic and background runs retain normal
job history/logging. Rollback removes the new readiness/freshness orchestration and profile
coverage; existing sources, reviews and generations remain valid evidence. New companies
created by the newer profile stay readable by the older code.

## Review Risks

- A live event can advance the tenant event sequence without changing a reviewed scope;
  freshness must use the shortest relevant links rather than the company-wide cursor.
- Starting Demo Data before the verified cutoff would immediately stale the initial
  generation; transaction ordering and first occurrence timing need an explicit test.
- Cost evidence for all 18 items must describe received demo values, not manufacture a
  fallback from selling prices or current stock.
- Setup must not become permanently blocked when a real evidence gap exists; it must
  retain a retryable failure and concise scope diagnostics.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
