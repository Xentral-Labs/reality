# Implementation Plan: Composable Analytics and Reports Workspace

**Feature**: `185-analytics-workspace` | **Date**: 2026-09-13 | **Spec**: [spec.md](spec.md)
**Working branch at planning**: `docs/summary-button`; no feature branch has been created. Spec Kit's feature name is not evidence of a Git branch switch.
**Language**: English.
**Status**: Technical design and schema accepted by the owner on 2026-09-13; nine review criteria evaluated and satisfied. Implementation authorized.

## Summary

Build a cataloged structured query capability and integrated Reports explorer over PostgreSQL. Order evidence uses SQL aggregation with fixed relationship/grain semantics; operational and financial perspectives reuse canonical services with bounded admission. Agent, CLI and Web execute the same definitions. Add one user/company-owned saved-definition table. Retain current Overview/Home contracts, extend the existing chat rather than adding a second assistant, and keep all analytical values transient.

## Technical Context

**Language/Version**: Python 3.12+, TypeScript.
**Dependencies**: Existing SQLAlchemy 2, Pydantic v2, Alembic, PostgreSQL/psycopg, FastAPI, Typer, React/Vite, localization and Lucide. No new runtime package planned.
**Storage**: Existing PostgreSQL; one additive configuration table, no result cache or new database.
**Testing**: Real isolated PostgreSQL pytest, Node contract checks, existing browser-test tooling and visual review.
**Constraints**: Decimal, UTC, opaque IDs, tenant/owner isolation, existing confirmations and typed domain authority.
**Scale**: 100,000 order-line common-query benchmark; bounded derived datasets, query shapes and displays per [contract](contracts/agent-tools.md). Deadline 30 seconds; target p95 under five seconds for specified evidence queries.

## Constitution Check

| Principle | Evidence | Design result |
|---|---|---|
| Source → Evidence → Reality | Contributor paths reuse authoritative record links; report results are observations | PASS |
| Reality owns operational state | Reuse fulfillment/correction/settlement services; no document operational fields | PASS |
| Proven schema only | US3/FR-012–013/DR-006 justify one private saved-definition table; no fact/result storage | PASS |
| Tenant + shared service boundaries | Allowlisted compiler, trusted Principal outside arguments, shared tools/services; tenant-only tokens cannot impersonate report authors | PASS |
| Spec/test traceability | Scope accepted; tests planned first; coverage matrix spans all 30 questions and every FR/DR | PASS |
| Explainable web behavior | Existing Inspector, contributor definitions, explicit unknown coverage and fresh observations | PASS |
| Received values not recomputed | Stated values summed at correct grain; defaulted/missing values not invented | PASS |
| Smallest coherent design | No graph/BI system, SQL interpreter, new chart dependency, report scheduler or snapshot database | PASS |

The owner accepted the concrete table and trusted identity policy on 2026-09-13. Runtime verification remains separately recorded in verification.md. No Constitution exception is used.

## Repository Structure and Layer Changes

| Layer | Planned paths / responsibility |
|---|---|
| Domain | `packages/reality-core/src/reality/domain/analytics.py`: strict definition/predicate/result models, compatibility and time semantics |
| Persistence | `packages/reality-core/src/reality/db/analytics.py`, `db/core.py` import; migration `migrations/versions/0060_analytics_reports.py`, following the scale-foundation migration merged while this branch was in progress |
| Services | `packages/reality-core/src/reality/services/analytics/` modules `catalog.py`, `orders.py`, `operations.py`, `finance.py`, `execution.py`, `contributors.py`, `exports.py`, `reports.py` |
| Canonical extraction | `services/delivery_reads.py`, `services/core.py`, `services/finance/` only where reusable read helpers need extraction; parity tests guard behavior |
| Shared tools | `tools/analytics.py`, `tools/application.py`: contextual analytics handlers and confirmed report changes |
| Adapters | `mcp/catalog.py`, `mcp/server.py`, `agent/mcp_chat.py`, `cli/app.py`, new `web/analytics_api.py`, route inclusion in `web/api.py` |
| Existing chat | `services/core.py` and `web/api.py` typed context and principal propagation; `storyline/recorder.py` respects owned read transaction and truthful trace metadata |
| Frontend | `apps/web/src/unified/AnalyticsPage.tsx` wrapper/export compatibility; `unified/analytics/{AnalyticsExplorer,ReportLibrary,AnalyticsTable,AnalyticsChart,AnalyticsPivot,useAnalyticsExecution}.tsx` (pure hook may use `.ts`); `api.ts`, `routing.ts`, `context.ts`, `ChatPage.tsx`, `Shell.tsx`, `UnifiedApp.tsx`, `localization.tsx` |
| Catalog/docs | Relevant command/resource/tenant-isolation catalogs, generated Tool Usage/MCP documentation, `docs/features/analytics.md`, `docs/WEB_SPEC.md`, `docs/DATA_MODEL.md` |
| Verification | New `tests/test_analytics_*.py`, `benchmarks/analytics/`, `apps/web/scripts/analytics-*.test.mjs`, `analytics-browser.mjs` |

Dependency direction remains domain → services → tools → adapters. UI/transport never owns a business measure.

## Design

### Definitions and grain

The [agent contract](contracts/agent-tools.md) is the exact implementation target for names, request grammar, limits and error semantics. Different perspectives provide line, header, customer-history, pair, commitment, inventory, invoice and payment grains. The compiler uses mapped SQLAlchemy expressions and bound values. It never accepts raw identifiers/joins/expressions from the agent.

Filter relationship predicates are fixed by catalog, with explicit inner period scope. Customer first/last history is calculated before filtering on the resulting date. Pair analysis first deduplicates product IDs within each order. Financial and operational measures use existing definitions; helper extraction must preserve their current consumers. Non-additive totals are calculated at their requested grain, never summed in the browser. Currencies/units partition applicable measures automatically and visibly.

Source eligibility must be proven per supported interpreter. Count retained interpreted documents, not payload versions. Pending later versions contribute coverage warnings rather than erasing valid retained orders. No generic latest-stream-head predicate is allowed. If a defaulted numeric field lacks evidence of source presence, return unknown coverage rather than an invented zero authority.

### Read execution

The execution service owns its connection/session factory and read-only repeatable-read transaction. It does not inherit an already-open adapter or trace transaction. Initial totals, comparisons, pivot totals, coverage and page share one observation. Subsequent reads are explicitly fresh observations; fingerprints bind definitions, not snapshots.

Admission bounds expression complexity, candidate pair expansion and canonical derived input populations. SQL runs with the remaining monotonic deadline; shared Python providers check cancellation/deadline between bounded batches. Adapter cancellation signals the owned execution context and cancels its DBAPI operation. No process-wide backend-ID cancel endpoint or queue is added. Inability to guarantee cooperative bounds is an implementation failure to resolve before completion, not permission to claim bounded execution from output pagination.

Storyline/auth/chat writes stay outside the analytical session and are identified as transport tracing in metadata. No projection refresh or business write occurs inside analytics execution.

### Identity and saved definitions

A trusted optional context is passed outside model arguments through generic read dispatch, MCP dispatch and both Web chat tool loops. Existing non-contextual tools retain their behavior. Web Principal is rechecked against membership; tenant-only MCP/CLI lacks personal report authority but retains all unsaved query capabilities. No new token auth is introduced.

Report services implement the single-table lifecycle in [data-model.md](data-model.md). Save/update/delete use expected revisions, retry identity/payload fingerprints and deletion tombstones. Agent proposals bind author and expected revision; approval checks them again and uses existing action receipts. Direct Web save is an explicit action through the same service. Broad company-owner permissions must not expose another user's reports.

### UI and agent handoff

Preserve `AnalyticsPreview` and Overview's existing route behavior. Explicit legacy days/metric/day links select Overview even if the previous route was Explore. Add local `analytics_view`, saved report ID and validated unsaved-definition handoff state; company changes clear it.

The execution hook separates draft/executed definition/result and generation. A failed rerun preserves the previous labelled observation; stale responses cannot override a newer company/run. Presentation switches use the executed result. Table, SVG chart and service-provided pivot remain decimal-safe in labels. No new grid library is required.

Typed analytics context extends commitment context in the existing chat. Discuss explicitly attaches visible context to the composer. Agent result rendering recognizes only supported same-company handoffs; untrusted definitions are validated again. Definitions can travel in bounded URL fragments, never result records in query strings. Opening does not save.

### Admission/protected-company policy

Classify new POST query/contributor/export routes explicitly as diagnostic reads under current company policies. Do not add a generic POST bypass. Saved-definition mutations retain current company admission restrictions and authenticated ownership. Existing retired Playground browser boundaries remain unchanged.

## Test Strategy and Traceability

Tests precede implementation where practical. Initial failures must demonstrate absent capabilities, not fixture/DB unavailability. Fixtures create business state through existing application services and use fixed dates.

| Requirement | Level / proposed path | Expected initial failure |
|---|---|---|
| FR-001–005,019; DR-001,004,005 | Unit/story: `tests/test_analytics_definitions.py`, `test_analytics_questions.py` | Catalog/grammar/compiler absent; 30 question cases not executable |
| FR-006–007,010,018; DR-002–004 | PostgreSQL: `test_analytics_execution.py`, `test_analytics_contributors.py` | No aggregate snapshot/bounds/contribution contract |
| FR-012–013; DR-003,006 | PostgreSQL/concurrency/migration: `test_analytics_reports.py` | No private definition lifecycle or Principal path |
| FR-014 | Service/adapter: `test_analytics_exports.py` | No complete bounded decimal-safe CSV export |
| FR-015,017–018 | Adapter: `test_analytics_adapters.py`, `test_analytics_chat.py` | No shared contextual tools or typed handoff |
| FR-008–011,015–016 | Node/browser: `apps/web/scripts/analytics-contracts.test.mjs`, `analytics-browser.mjs` | No explorer/library/draft lifecycle or new context navigation |
| SC-005 | `benchmarks/analytics/run.py`, `test_analytics_performance.py` | No representative evidence query benchmark |

Include tenant/author confusion, replay/new source versions, source-default versus stated zero, fiscal-neutral ISO weeks, DST, null dates, incompatible currencies/units, one-to-many fan-out, non-additive pivot totals, cancellation/returns/revisions/reversals, partial allocations, no writes, fresh observations, unknown-source coverage and query cancellation. Restricted question rows must assert a meaningful refusal/narrower answer, not fabricated data.

Benchmark workload: Q01 customer/product/week, Q04 customer period comparison, Q06 product ranking, Q07 weekly product quantities, Q08 product-pair counts within the admitted pair bound, Q09 customer agreed-price range, Q22 purchase-price history and Q23 supplier/product history. Seed 100,000 interpreted order lines with repeated products, several customers/suppliers, two currencies and fixed time windows. Run each query once cold and 20 times warm; report individual failures and warm p95, plus all cold timings. Setup uses normal application services; timing excludes fixture creation. Every timed result is checked against independently prepared expected values.

Required gates: `make spec-check`, `make lint`, full `make test` including migration tests, `make web-build`, `make site-build`, Web localization/contract/browser checks, `make docs-generate`, `make docs-catalog-check`, `make docs-build`, benchmark and manual desktop/mobile visual review. Record failures as failures; do not mark tasks complete while required checks are red.

## Rollout and Rollback

Add schema through the normal deployment migration path before exposing saved reports; no runtime auto-migration. Preserve existing Overview endpoints and URLs throughout. Deploy backend contract before frontend callers. Roll back frontend/backend together while retaining the additive configuration table. No source/reality backfill or result-cache cleanup is required. Do not purge saved definitions as an automatic downgrade.

## Review Risks

- Trusted personal identity does not currently cross every tool boundary; a JSON owner field would be a privacy defect.
- Canonical services may be full-tenant Python reads; their deadline/admission checks must be real rather than output-only limits.
- Mutable/defaulted source evidence requires per-intake eligibility and value-presence proof.
- Global tracing wrappers currently commit reads; analytics must own its isolated read transaction and describe tracing honestly.
- Chart/pivot totals, live-page drift and draft/result state are easy sources of plausible wrong numbers.
- New saved-definition schema and the tenant-only-token limitation require explicit technical review; scope approval already exists and is not being requested again.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Planning output

Research, model, agent contract, quickstart and tasks are provided under this feature directory. Extension hooks were skipped because no configuration exists. Architecture/schema review and reviewer checklist disposition are recorded. Implementation follows the analyzed dependency order; remaining verification stays open.

## Chart guidance defect correction (2026-09-13)

Scope accepted through the user's request to fix the diagnosed generic message.
Restore FR-010/FR-016 with presentation-only cause detection in AnalyticsChart and
localized actionable messages in en/de/nl/es. Preserve result partitioning, first
measure, chart bounds and all values; no API, model, service or schema changes.
Constitution check: PASS for all principles (read-only presentation, unchanged
shared semantics/tenant scope/provenance, regression proof before implementation).
Test the rendered component for currency-only, unit-only, combined, missing-group
and compatible results. Verify frontend contracts, localization audit, web build,
spec check and diff review. Backend/migration/catalog gates are unaffected because
no executable business catalog, API or persistence changes. Rollback is a code revert.

## Recognizable Explorer controls (2026-09-13)

User approved improving the discoverability of dataset/sort and related inputs.
Replace undefined `br-input` with existing `br-control`; use a local native-select
wrapper with a decorative Lucide chevron and a bordered Filters disclosure.
No new CSS system, dependencies, business behavior, API or persistence changes.
Constitution check: all PASS; shared services, values and explicit execution stay
unchanged. Verify with the existing fixture browser flow, computed control styles,
keyboard use, desktop/mobile screenshots and dark-mode inspection; run frontend
contracts, build, localization and spec gates. Rollback: revert presentation changes.

## Direct chart partition selection (2026-09-13)

User feedback authorizes fixing the remaining chart dead end. Use local React state
and native labeled buttons in AnalyticsChart to choose among the service-returned
currency/unit partitions. Default/fallback to first available; filter loaded rows
before the display bound. No derived totals, requests, API/schema/business changes.
Constitution gate: PASS throughout; this is bounded presentation of existing values.
Test rendered first-partition isolation and unit/combined/unknown cases, then browser
switching and unchanged query count. Run contracts, browser, build, i18n/spec checks,
review and update the already-authorized local web deployment on 8080.

## Dedicated analysis chat (2026-09-13)

Owner accepted a new conversation and explicit button label. Reuse ChatPage's
existing createCopilotSession API for manual and analytics-triggered conversation
creation; guard concurrent creation/sending and tenant unmount, bind attachment to
its new session, clear prior context after success, and block sends against retained
stale session data. Add en/de/nl/es labels. No API/schema/business-action changes.
Constitution check: PASS; explicit UI action creates chat metadata only, no business
mutation or automatic message. Browser fixtures cover old/new sessions, failed
creation, attachment payload and history isolation; run chat regression, frontend
contracts/build/i18n/spec checks, then update the authorized local web deployment.
