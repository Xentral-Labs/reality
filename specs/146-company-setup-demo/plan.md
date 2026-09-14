# Implementation Plan: Company Setup and Continuous Demo Data

**Date**: 2026-09-09 | **Spec**: [spec.md](spec.md) | **Feature context**: 146-company-setup-demo. Existing working branch is retained.
**Status**: Concrete schema and authority approval received on 2026-09-09. Implementation and local acceptance are complete; see quickstart.md. Spec 147 remains the scheduler/worker foundation; no live deployment has been performed.

## Summary

Use one creation form and shared account-scoped services for first and later creation. Empty is default; one goal-based UI choice maps to distinct content/environment fields, and demo implies Sandbox. Reuse PlaygroundRun orchestration for new empty/canonical/execution presets and add only an ordinary-company receipt and a Demo Data connection. Seed a single international profile through transaction-bound application services. Register continuous synthetic source intake with the existing scheduler/worker and normal interpretation pipeline.

## Technical Context

Python 3.12+, SQLAlchemy 2, Alembic/PostgreSQL, Pydantic, FastAPI, existing React/TypeScript/localization. No new package, broker or deployment app. Decimal quantities/money, explicit UTC dates and opaque IDs. Tests: unit, PostgreSQL service/concurrency/migration/business-story, API security, frontend contracts and real browser acceptance. Initial bounds: 16 items, 4 customers, 3 suppliers, 2 locations; 84-day history; 10/60/300 orders per hour; one unfinished delivery per schedule, one active child per worker, 20 pending/failed generated imports per connection; existing setup quota and 64 KiB manifest cap.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Lossless demo_data source intake; shared interpreter creates evidence and commitments, seed uses normal services | PASS |
| Reality owns operational state | No document operational fields; source progress is distinct from fulfillment | PASS |
| Proven schema only | Two infrastructure tables and one supporting uniqueness have field-level proof in data-model.md; implementation waits for explicit review approval | PASS |
| Tenant + shared service boundaries | Existing immutable purpose and admission retained; narrowly bound initialization/intake authority, scoped composite links | PASS |
| Spec/test traceability | All 24 FR/DR and nine success criteria map to tests/tasks; tests first | PASS |
| Explainable web | Shared four-language form and integration controls; source/intake/order links and truthful empty/loading/error states | PASS |
| Received values not recomputed | Authored source amounts and business dates retained; no invented cost/net-profit authority | PASS |
| Smallest coherent design | Reuse PlaygroundRun, ScheduledJob/Run and source outcomes; no DemoRun/delivery table or new scheduler | PASS |

PASS assesses design conformity, not self-approval of schema expansion. The concrete approval gate in review.md remains mandatory. No constitutional exception is requested.

## Files and layers

- Domain/catalog: `src/reality/demo/international.py`, `src/reality/demo/profile_contract.py` (pure fixture/config validation and source-stated payloads).
- Persistence: `src/reality/db/company_setup.py`, `src/reality/db/demo_data.py`, core metadata registration and next available Alembic revision.
- Services: `src/reality/services/company_setup.py`, `demo_profile.py`, `demo_data.py`; narrowly adapt `core.py`, `playground.py`, `tenant_policy.py`, `scheduled_jobs.py`.
- Source interpretation: `src/reality/integrations/demo_data.py`, existing source interpreter registry and `config/connector_catalog.yaml`.
- Job definition: `src/reality/jobs/handlers/demo_data.py`, register in `jobs/registry.py` with exact Sandbox/source/actor policy.
- Adapters: `src/reality/web/company_setup_api.py`, `demo_data_api.py`, mount in `web/app.py`; existing `web/api.py`, `web/auth.py` forward shared operations. No generic Chat scheduling/source-control tools.
- Frontend: `apps/web/src/components/CompanySetupForm.tsx`, `CompanySetup.tsx`, `DemoDataIntegration.tsx`, `api.ts`, `Auth.tsx`, `App.tsx`, existing Playground presentation and localization sources. Preserve theme/shared form patterns.
- Durable documentation: `docs/features/company-setup-demo.md`, `docs/DEMO_SPEC.md`, `docs/WEB_SPEC.md`, architecture/data model/CLI/test strategy, source/scheduler contracts and coverage/isolation catalogs.

All backend paths above are relative to `packages/reality-core/`.

## Design

### Creation and destinations

Options come from authenticated account eligibility; the browser never grants an environment. Active users may create ordinary or permitted Sandbox companies; pending users only the existing enabled practice entry. Demo always selects Sandbox. First-name prefill is editable and not reapplied after typing; existing membership/invitation wins over setup.

One confirmed request retains its UUID and exact choices across reload/lost response. Lock owner and detect request reuse across ordinary receipt and PlaygroundRun before creating anything. Ordinary Tenant+membership+receipt commit atomically. Sandbox uses existing initializing/failed/active orchestration and quotas, new profile-specific presets and atomic seed transaction. Status reads do not seed. Active ready users open the exact App company; pending users open the exact existing Playground cockpit, with account-scoped integration controls there. Never broaden pending bootstrap or business APIs. Preserve old saved lessons and compact demo helper/CLI fixtures. Legacy company creation delegates to the shared service, requires a request key and maps guided demo creation to Sandbox; its API contract and spec 027 are updated together.

### Canonical profile and separate execution

The precise source vocabulary/cases/windows are in contracts/demo-profile.md. Share catalog primitives between full baseline and minimal connection prerequisites. A ready manifest verifies actual counts and expected case relationships before marking the run ready; interrupted/mismatched setup stays unavailable. No historical source ingestion timestamp or proposal timestamp is backdated.

Provision execution profile in a fresh practice tenant only after explicit request; one-unit free-stock success and held refusal remain unexecuted. Repeats retain prior analysis/execution tenants and audit; same request reopens the existing result. Existing proposal → review → explicit confirmation → receipt/verifications remains unchanged.

### Continuous integration

Demo Data is a genuine synthetic connector, never a Shopify impersonation. Existing profile refs must match exactly; empty Sandbox connection preview explicitly authorizes only missing catalog/customer/location prerequisites, no history or opening stock. Populated incompatible company fails without mapping guesses. Execution tenants and ordinary companies are refused.

Each Start-after-Stop allocates a new ScheduledJob whose ID is the continuous run ID. Register `demo.generate_orders`; generate one deterministic order per logical scheduler occurrence through transaction-bound `enqueue_source`/interpretation. Use SourceRecord/ImportJob/outcomes for counts and links; no synthetic source success based only on a scheduler heartbeat. No reservation, shipment, payment, replenishment or proposal confirmation occurs on arrival.

Manual connection defaults to stopped; explicit live-company creation connects and starts automatically at 60 (FR-021). Supported controls use explicit rate 60; supported rates 10/60/300. Cancel only undispatched occurrences on pause/stop/rate change using the approved narrow spec 147 extension, preserving evidence and starting future timing on resume. Executing transactions may finish before acknowledgement. At 20 pending/failed imports, pause generation visibly; source-level retry retains identity, explicit resume follows recovery. Expose generated/pending/imported/failed counts, current rate, next due, last interpreted success and paginated intake/result links (default 25, maximum 100, tenant/source-bound cursor).

### Transactions and authorization

Extract bound intake/interpretation helpers without changing existing public commit contracts. Use nested transaction rollback for failed interpretation, retaining intake and safe failure outcome in the scheduler-owned transaction. Parent scheduler success means intake attempt handed off, not successful interpretation. Unexpected transaction failure retries the same logical scheduler identity. Existing API/CLI/import regressions must pass.

Profile initialization authority is bound to session, transaction, owner, initializing run and allowlisted profile version/operations. Continuous authority is bound to the current Sandbox connection, active source, scheduled run and current eligible owner, and allows only source intake plus outgoing order evidence/commitments. Neither grants arbitrary business mutation, network access or cross-tenant discovery. The authorization callback may accept verified pending private owners only through this explicit contract; no implicit use of the active-only cleanup policy.

### Schema / migration

See data-model.md for exactly two tables and supporting same-tenant source uniqueness. No backfill, business-status column, general JSON extension or automatic schedule activation. Allocate migration number at implementation time after approval. Preserve purpose immutability and existing permanent-delete behavior. Do not migrate existing companies into the canonical profile.

## Test Strategy

| Requirements | Planned executable proof |
|---|---|
| FR-001/002/003/004/005/006/007, DR-001/004 | `tests/test_company_setup.py`, `test_company_setup_api.py`: matrix, editable prefill, exact destination, admission, duplicate/reload/concurrent requests, zero-record empty result, old-company preservation |
| FR-008/009/011, DR-001/002/003 | `tests/scenarios/test_international_demo.py`: counts, all ten cases, stock-location/unit/procurement distinctions, source links and manifest validation |
| FR-010/011, DR-003 | Same story + `tests/test_demo_profile_history.py`: 84-day/two-window cohorts, received values, currency separation, unavailable-cost declarations |
| FR-012, DR-004 | `tests/test_demo_execution_profile.py`: separate fresh tenant, unexecuted stock, success/refusal and replay via existing confirmed tools |
| FR-014/015/016/017/019/020 | `tests/test_demo_data.py`, `test_demo_data_api.py`: eligibility, explicit prerequisite preview, lifecycle/revisions, cursor/counts, backpressure and isolation |
| FR-018, DR-001/002/003/004 | `tests/test_demo_data_intake.py`: bound commit/rollback, lossless replay, ten timed imports, no operational actions, unchanged baseline/execution fixture |
| FR-006/014/017, DR-001 | `tests/test_company_setup_migration.py`: two-table migration, uniqueness and composite-FK refusal, owner-level cross-kind concurrency |
| FR-013 and UI portions of all stories | `apps/web/scripts/company-setup-contract.test.mjs`, `demo-data-contract.test.mjs`, existing localization tests and live browser journeys in four languages/themes/mobile/desktop/keyboard |
| Scheduler compatibility | Extend `tests/test_scheduled_job_recovery.py`: authorized queued-only cancellation, running/stale/unresolved refusal, preserved history; all existing spec 147 tests |

Observe meaningful failing tests before domain/services/adapters. Final gates: `make lint`, complete `make test`, `make spec-check`, `make site-build`, `make web-build`, `make docs-build`, migration roundtrip, final browser evidence and scheduler/worker container acceptance with the registered demo handler. Exact initial failure is absent new service/route/profile or current non-idempotent/committing behavior, not a mocked implementation mirror.

## Rollout / Rollback

Migrate once via release task; deploy matching API/scheduler/worker core and frontend only after local verification and separate deployment authorization. Manual connections stop by default; explicitly requested live-company setup connects and starts atomically. On rollback stop/cancel pending demo intake, disable new setup entry if needed, keep metadata, baseline, imports and audit. No destructive reset. Existing compact lessons and invitation worker are unchanged.

## Review Risks

Owner-level cross-kind idempotency; pending access accidentally reaching ordinary APIs; seed/import helper commits escaping transaction; cancellation versus active claim; new source counts hiding failed interpretation; unsupported finance/cost semantics; profile IDs exceeding manifest bound. Each has explicit tests above and in tasks.md.

## Complexity Tracking

No constitutional exception. New persistence and narrow authority/cancellation need concrete review approval, not another approval of the already accepted product intent.

## Approved live-creation refinement

Add optional strict `live_simulation=false` to the shared creation contract. Include true in the durable creation fingerprint and PlaygroundRun intent (preserve old false fingerprints). After canonical seed succeeds, lock the owner and atomically connect/start the shared Demo Data services plus a completion marker in existing initialization JSON. Allow caller-owned commits in the existing control wrapper; do not bypass services. GET only derives incomplete setup status. Explicit retries finish incomplete setup; a completed marker prevents restarting later user controls. No table, column, permission expansion or new timer. UI offers the option beside canonical demo data and persists it with the same creation request. Tests cover active/pending owners, rejected combinations, failure rollback/recovery and replay after pause; browser confirms the checkbox reaches the creation request. Constitution: all eight checks PASS.

Unified-domain compatibility: cancellation now calls shared `release_commitment_hold(_commit=False)`. The version-bound initialization authority includes that operation solely for authored cancelled seed cases; continuous intake does not receive it. Preserve newer action IDs, preview validation and lot expiry in merged core services.

FR-022 plan: batch-read tenant/profile/connection metadata through the setup service, restricted to requested authorized tenant IDs; expose optional company_kind/demo_data_state in existing bootstrap summary. Render each unified CompanySettings item as a bordered card with its management footer inside the card and labelled company type/source state. Test visible state, foreign membership refusal and actual mobile/desktop card layout. Constitution PASS; no schema or permission expansion.

FR-023: replace independent form state with a single business/sandbox/demo choice, mapped to the unchanged API at submission. Use a single native radio group with descriptions and an optional demo-only checkbox; retain eligibility and busy guards. Update four-language copy and existing browser acceptance before implementation. Constitution PASS: presentation-only, no schema, service or permission changes.

FR-024: shared form owns accessible name validation with a field ref, inline alert and required/help labels. Preserve API, field length and busy/eligibility checks. Browser proof covers empty/whitespace submission, no writes, focus, correction and retained choices across languages/themes/viewports. Constitution PASS; presentation-only.

FR-025: automatically attempt opening once per ready tenant in the shared setup component; preserve the existing open callback and receipt removal after successful opening. Replace the ready menu with opening feedback and error-only retry. Add scoped dismissible destination confirmation in UnifiedApp. Browser proof: automatic new/recovered entry, failed-open retry with no extra setup mutation. Constitution PASS; no service/schema changes.

## Sandbox clarity and live activity refinement

Add recent=true bounded snapshot to imports read with has_more and held created/completed times/document number; default cursor unchanged. Analytics replaces business-only guard with tenant existence only in two reads; HTTP membership/admission and mutation guards retained. UI groups controls and polls existing reads; no schema or new subsystem. Constitution PASS. UX reviewer identified opaque-ID ordering as unsuitable and recommended chronological feed and stale state.

FR-029: add demo-data destination to shared routing and shell navigation, reuse DemoDataIntegration on a dedicated page with RegisterHeader. Conditional navigation uses existing company_kind/demo_data_state; no new backend read or persistence. Remove inline widget from DataSourcesPage. Update browser route/navigation proof and localized layout checks. Constitution PASS.

FR-030 correction: replace only the two ordinary-workspace admission checks in
`services/attention_reads.py` with scoped tenant existence reads. The API keeps its
existing tenant access dependency; canonical exception and mutation services do not
change. No schema/UI changes. Test seeded demo findings and details plus authorized
Sandbox HTTP reads before implementation. Existing foreign-record and mutation
boundary tests remain required. Constitution PASS; no unresolved clarification or
critical finding. Verify focused regressions, full backend, lint/spec and actual
read-only deployed demo investigation. Rollback restores the prior API/core images.

## FR-031 implementation
Update CompanySetup presentation with scoped Tailwind styles and localized status titles. Preserve exact saved request and automatic ready navigation. Constitution check PASS: no service or schema changes. Verify delayed recovery and creation, errors and retry identity using HTTP browser fixtures, then web contracts, localization, build, formatting and mobile/light/dark visual review.

## FR-032 implementation plan

Reuse the Demo Data route from owner Sandbox cards; do not infer service eligibility from the card. The existing denied-status presentation offers normal CompanySetup for a separate demo, with an optional initial demo/live selection constrained by setup options. Preserve pending saved requests, explicit confirmation and all service scope checks. No schema, queue, business calculation or service changes. Constitution: PASS. Verify owner/member/ordinary cards, target tenant, read-only navigation, supported controls, unsupported recovery and cancel, default choices, saved-request recovery, localized/mobile layout.
