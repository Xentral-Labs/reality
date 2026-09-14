# Implementation Plan: Background projections and responsive Inspector

**Branch**: `179-background-projections` | **Date**: 2026-09-12 | **Spec**: [spec.md](spec.md)

## Summary
Deliver in order: (1) catalog performance, (2) background materialization, (3) read-only consumption and freshness UX, (4) complete verification and review. Keep the business outbox as the durable trigger so queue capacity never blocks business writes. Scheduler detects dirty tenant projections and enqueues a coalesced internal run; worker calls shared projection services. No broker, API loop or browser scheduling is introduced.

## Technical Context
Python 3.12+, SQLAlchemy 2, PostgreSQL, Pydantic v2, existing FastAPI and scheduler/worker packages; React/TypeScript frontend. Test with pytest against isolated PostgreSQL, existing browser scripts and Node contract tests. Warm catalog target: >=80% less local CPU than 0.97–1.37s baseline. Healthy background target: 30s for events, 90s for time-only observations. Worker retains its 30s bound and ordinary retry/claim discipline; oversized derivations fail visibly rather than running indefinitely.

## Constitution Check

| Principle | Design evidence | Gate |
|---|---|---|
| Source → Evidence → Reality | Existing builders/services and shortest record links are retained | PASS |
| Reality authority | No document state, business action or source-value recomputation is introduced | PASS |
| Proven schema | One existing job actor becomes nullable only for cache-maintenance runs, enforced by a check; one tenant-first partial uniqueness index coalesces unfinished cache jobs. See data-model.md | PASS — owner explicitly approved 2026-09-12 |
| Tenant/service boundaries | Scoped outbox/checkpoints/queue; system authorization allowlisted to rebuilding caches, never owner fallback | PASS |
| Specification/test evidence | Product scope accepted in conversation; tasks include test-first and complete verification. Specific internal-job schema approved by the owner on 2026-09-12 | PASS |
| Explainable web | Per-response progress and stale notice; explicit live/pricing labels; no browser business rules | PASS |
| Simplicity/storage discipline | Reuse queue/registry/runtime; no new table, broker or dependency | PASS |
| Received values | Builders retain received values and derived observations remain disposable | PASS |

The independently deployable catalog phase has no schema impact. The owner explicitly approved the specific schema change and sequential implementation on 2026-09-12. No constitutional exception is requested.

## Project Structure
- `packages/reality-core/src/reality/catalogs.py`, `web/api.py`, `web/app.py`: separate immutable/defensively copied runtime catalog cache; uncached validator retained; startup warming.
- `apps/web/src/unified/InspectorCatalog.tsx`: lazy disclosure bodies, full metadata search retained.
- `packages/reality-core/src/reality/services/projections.py`: independent builders, invalidation selection, transaction-bound rebuild, stored reads and freshness.
- `packages/reality-core/src/reality/services/projection_jobs.py`: scheduler dirty discovery, bootstrap and minute eligibility; internal enqueue through shared scheduling service.
- `packages/reality-core/src/reality/jobs/handlers/projections.py`, `jobs/registry.py`: code-owned cache-only handler and authorization.
- `packages/reality-core/src/reality/services/scheduled_jobs.py`, `jobs/runtime.py`, `jobs/runner.py`: shared queue producer and consistent worker transaction.
- `packages/reality-core/src/reality/db/scheduled_jobs.py`, `migrations/versions/0057_projection_jobs.py`: minimal nullable-actor constraint and unfinished-run uniqueness.
- `packages/reality-core/src/reality/web/read_models.py`, `web/api.py`, `services/read_contracts.py`, `tools/application.py`: stored readers and explicit live contract compatibility.
- `apps/web/src/api.ts`, `unified/ProjectionDataDialog.tsx`, affected financial/workspace consumers: snapshot metadata and shared freshness notice.
- `packages/reality-core/config/business_event_catalog.yaml`, `projection_catalog.yaml`, data-model catalog: audited dependencies and calculation-mode descriptions.

## Design and execution order

### 1. Responsive catalog
Cache a successful validated global snapshot per application process; keep `load_application_catalog()` uncached for drift tests and generator. Do not store tenant/request data. Return a defensive copy or pre-serialized immutable body. Warm during lifespan, with explicit reset in tests. Lazy disclosure mounts body only when open; native summary remains present and keyboard-operable. Benchmark repeated runtime reads and browser expansion/search.

### 2. Dependency-correct builders
Split the monolithic builder into individually selectable derivations while reusing canonical services. Fulfillment queue/blockers/supply-demand may share intermediate reads only when selected together. Inventory, commitment register, documents, exceptions, finance, payments, journal, timeline and usage avoid unrelated work. Audit event invalidates against actual builder dependencies; unknown events fall back to all materialized projections. Tenant usage must query only its tenant (the current global usage summary call is unsuitable inside a tenant worker). Explicit live MCP derives selected builders without cache writes.

### 3. Durable background dispatch
The committed BusinessEvent outbox is already an atomic durable invalidation record; do not add work inside emit_business_event. On each shared scheduler sweep, discover eligible work per tenant using latest relevant event sequence, builder version and completed checkpoints. Missing caches initialize; overdue/risk and non-event activity projections have minute eligibility through this same scheduler. Archive prevents dispatch. Create at most one unfinished `projections.refresh` run per tenant, with frozen bounded projection names; a later sweep captures events committed while a run was active. Queue cap defers without acknowledging outbox progress. Eligible regular schedules and cache work alternate using retained run history, so neither frequent Demo Data jobs nor cache jobs starve the other.

The actor-null internal run is accepted only for `projections.refresh`, no schedule id, and a code-owned validated configuration. Existing user job paths reject that internal type. Authorization validates active tenant and internal run identity at each attempt; it does not choose an owner, create a synthetic user, or bypass a business service. Existing status endpoints may show these runs to admitted owners. No direct external effects.

### 4. Consistent publication and recovery
A projection handler owns no commits. Use a repeatable-read transaction for projection worker execution, selected before claim validation/builder queries. Capture the relevant event targets in the same snapshot as Reality reads. Serialize competing rebuilds with a tenant-scoped advisory transaction lock; PostgreSQL serialization failures follow existing transient retry. Publish rows, completed checkpoints and successful run state in one commit. Newer events remain ahead and cause later work; no mutable queued payload merging. Explicit maintenance rebuilds use an equivalent consistency boundary and remain separate from read APIs. Failed/unresolved runs remain visible and block blind redispatch until explicit recovery/reconciliation. A failed run remains a historical failure; an explicit successful maintenance rebuild whose completed checkpoints are later than that failure acknowledges the stale cache and permits later dispatch. Unresolved claims must first reconcile via the shared runner. A fresh opaque request key identifies each dispatched run; tenant locking plus the unfinished-run unique index coalesce dispatch. Failed-run/checkpoint timestamps block blind redispatch, while cache deletion can still bootstrap after a previously successful run.

### 5. Pure reads and honest freshness
Remove implicit refresh from stored readers, paginated readers and totals. Expose an additive snapshot envelope for Inspector and metadata on paginated consumers, retaining legacy list shape where required. Snapshot rows/totals/metadata must describe one completed generation. Compose filtered rows, page counts, currency totals, checkpoint and relevant event/run metadata in one SQL statement (CTEs/scalar subqueries); this avoids changing isolation after the shared request session has already performed admission queries. Legacy unadorned list reads remain one SELECT. Initial state is not business emptiness. Pending or failed results retain last completed rows and timestamp. A shared UI notice offers read-only refresh and updates after confirmed actions using existing refresh plumbing; optional polling is restricted to visible pending data and aborts on unmount.

Payments currently mixes live rows with cached totals. Keep its existing live rows and aggregate wholly live canonical payment_rows results using the same filters and settlement semantics; return live consistency metadata. The Inspector Payments projection remains a separately identified stored snapshot. Test currency separation and row/total filter parity. Explicit v2 MCP live reads retain `live_read`/`live_keyset` semantics. Legacy stored reads expose freshness through compatible metadata/header or documented companion snapshot read. Parameterized pricing calls `resolve_price` live and serializes its result without cache writes or unrelated refresh; Inspector labels it accordingly.

## Migration and rollback
Migration 0057 changes only `scheduled_job_run.actor_id` nullability and adds the internal-origin check plus unique unfinished cache-run index. Existing actor FKs and user/schedule authorization remain. No business payload/data is rewritten. Test upgrade and downgrade on isolated PostgreSQL; downgrade must explicitly refuse while internal runs remain rather than delete audit/history or invent actors. Operational rollback can revert frontend/read adapters and disable internal dispatch while leaving additive queue schema and retained jobs in place. Deployment/migrations are not executed on the user's live environment by this task.

## Verification and review
See tasks.md and quickstart.md. Test cache identity/failure/mutability; dependency selection; outbox rollback; tenant isolation; consistent concurrent publication; retries and stale claims; capacity; bootstrap/time; archived tenant; internal authorization; pure HTTP reads; stale UX and live pricing. Required gates: complete backend suite and Ruff, spec policy, frontend build/i18n/tests, docs generation/contracts/build; isolated migration up/down. Public site remains unchanged; run its required gate if shared/site files change. Review final diff and record actual evidence, without marking failed checks complete.

## Complexity Tracking
No exception. The only schema amendment prevents fake attribution of internal cache upkeep to a human and enforces queue coalescing in PostgreSQL. Reusing an owner's identity was rejected because the action is infrastructure upkeep, can be triggered by imports, and must not inherit business permissions or depend on a particular membership staying active.

## Public reference follow-up

Scope accepted by the owner on 2026-09-12. Add documentation-only read-mode metadata in the existing catalog reference generator, deriving stored projection membership/time triggers from the executable projection registry and MCP defaults from input schemas. Audit adapter-specific query variants against their handlers. Render the same data in English/German Markdown and the existing explorer. No runtime/schema change; Constitution Check remains PASS. Test generated coverage and decisive adapter distinctions first, then render/build and inspect responsive browser output. Existing FR-010/FR-011 own this clarification; no new business feature.
