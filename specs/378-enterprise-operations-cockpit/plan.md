# Implementation Plan: Enterprise operations cockpit

## Preview parity implementation (FR-052–056)

Owner-approved scope, 2026-10-07. Constitution Check PASS: all observations are derived
at read time, no schema, authority, permission, external effect or polling change.
Supersedes the earlier FR-042 placement and FR-047 uniform decorative strip.

Tests first: full-cohort dated/undated supplier partition, order worst-line deduplication,
canonical due-soon supersession, unavailable message risk and read-only scalar/snapshot
parity; browser geometry, exact counts/legend and named access/manual previews. Implement
service partition from already-loaded identities/findings, then additive DTO and thin UI.
Use continuous proportional widths rather than rounding eighteen squares: small positive
categories retain their true proportion. Unknown is hatched and never a green inference.

Reuse the existing four live reads. Default register scope becomes human-owned for its
compact preview; choosing an automatic case switches the existing read to outstanding.
Keep the event list mounted in a bounded scrolling region, move its recording-rate chart
behind a disclosure, and place the existing access panel under the log in the same column.
Use the shared surfaces and container-responsive two-row grid; stack message plots.

Verification: affected service/adapter tests, frontend contracts/build/i18n/format,
full cockpit browser matrix and controlled live lifecycle, spec/annotation/lint/catalog.
Activate API/web only and inspect the real 8080 company. Preserve all earlier pilot and
enterprise performance gates. Missing current-day shipping input is not fixed by UI.


## Instrument console follow-up (FR-047–051)

Owner scope approval: 2026-10-07, proceed autonomously and provide a local viewing URL.
Constitution Check: PASS for all eight principles before and after design. No schema,
new business authority, external effect, dependency, timer, identity or permission change.
The existing custom checklists remain reviewer-owned; the owner explicitly authorized
this bounded follow-up without closing their markers or the earlier rollout gates.

Extend the existing operating flow read with local incoming/first-reply interval counts
from the already tenant-scoped mail cohort. Reuse the exact same-run first reply matching
and the existing half-open physical-flow bucket intervals; include the final observation
instant only in the final mail bucket to reconcile the inclusive existing hour totals.
Uncovered company time stays unknown. No extra SQL, persisted field or catalog entry.
Add nullable counters to existing bucket DTOs; absent counters remain unknown in clients.
Do not derive supply/stock/order/return history from unmatched measurement units.

Present five canonical instruments and an explicitly unavailable Finance entry. Reuse
canonical signals without estimating risky proportions. Lift selected area state into
OperationsCockpitPage, derive initial bookmarked selection, listen for hash navigation,
reset at company change and keep details mounted with hidden inactive articles. An
accessible local area selector and the instrument anchors choose the same state. Retain
existing shipping, case register, agent/activity and deviation components in order.
Replace tiny detail sparklines with responsive labelled SVGs; messages use separate
intake/reply and backlog plots, including truthful missing/partial coverage.

Test first: canonical duplicate/run/company mail bucket proofs and existing product
browser navigation, refresh/disclosure, unavailable, theme/locale, responsiveness and
case-control regression. Then implement service → DTO → web presentation. Run affected
backend tests, frontend contracts, cockpit/shell/live-session browser checks, build,
formatting, i18n, spec, annotation and lint gates. Activate only API and web locally;
leave operator, simulator and workers running. An actual local legacy migration-chain
mismatch may be reconciled only after backup and exact existing-DDL parity, using
the already-reviewed frozen case migration; this adds no new feature schema design. Rollback: restore the bounded
frontend presentation and additive mail projection; no data migration is needed.

**Feature**: `378-enterprise-operations-cockpit` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)
**Checkout**: `feat/company-reference-simulator`; no branch switch during planning.
**Language**: English
**Status**: Owner approved product scope, concrete shipping-input/schema, completion-slot-v1 and live/Agent clarifications in chat on 2026-10-06. Implementation authorized; verification and rollout remain separate.

## Summary

Add optional `/app/cockpit` inside Reality, keeping Home as the default. Shared reads calculate timed shipping plan, confirmed handover and a conservative forecast. Existing operational-case controls connect affected orders to human takeover, the human-owned register, specialist workspaces and reviewed handback.

Existing records do not establish dispatch-deadline meaning, timed targets or confirmed shipping capacity. Use the three approved source-backed input tables, detailed in [data-model.md](data-model.md). No stored curve/forecast, document fulfillment status, new case family, provider transport or scheduling infrastructure is introduced.

The owner's all-day-live clarification is explicit in US5/FR-021–023: a five-second visible-tab read lifecycle, a rolling recorded-business-activity panel and stable investigation/control state. The [live contract](contracts/live-observation.md) specifies truthfulness, bounded operation, recovery and company-day rollover; deterministic eight-hour proof and a separate real-time soak precede pilot enablement.

FR-024 adds a compact named Agent/access overview using existing manual MCP credentials, authorized clients and attributable recorded actions. Preserve existing owner-only inventory/telemetry disclosure; usable credentials and last use are not evidence of a continuously connected or currently executing external Agent.

## Technical Context

**Language/Version**: Existing Python 3.12+ and TypeScript versions.
**Primary Dependencies**: Existing SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite and localization modules; no new dependencies.
**Storage**: PostgreSQL; original planning/confirmation payloads remain immutable Sources.
**Testing**: Pure-domain pytest; isolated PostgreSQL service/story/adapter/migration proof; existing fixture-backed browser harness; deterministic eight-hour lifecycle proof, measured live-refresh workload and separate real-time soak.
**Project Type**: Shared domain/services/tools, thin Web/CLI/MCP adapters and the existing frontend.
**Constraints**: Decimal quantities, UTC instants, explicit company/site zones, opaque identities and strict tenant scope.
**Scale/Scope**: Approved proposed workload: 10,000 active orders, 100,000 historical orders, 500,000 shipment observations, ten observers; p95 openings/site changes within three seconds. Measurement required; no inference from annual revenue.

## Constitution Check

Results below concern design conformance, not implementation permission or executed tests. No exception is proposed.

| Principle | Evidence in this plan | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Accepted typed planning evidence references existing commitments; physical contents/events remain authoritative; exact Sources are linked | PASS |
| Reality owns operational state | Plan/progress/risk/forecast observations are derived; no document or plan fulfillment-status fields | PASS |
| Proven schema only | Three tables have repeated site/day/time/quantity/capacity selection and calculation use cases in the reviewed proposal; owner schema approval remains an execution gate | PASS — proposed design proof |
| Tenant + shared service boundaries | Composite tenant FKs; shared services; separate active-member cockpit router without widening owner telemetry | PASS |
| Spec/test traceability | FR/DR scenarios in spec, proof paths below and complete task coverage | PASS |
| Explainable web behavior | Cohort/forecast basis, supporting orders, exact scope/control decisions and shortest Inspector/source paths | PASS |
| Received values not recomputed | Source-stated inputs retained exactly; observations computed only at read time | PASS |
| Smallest coherent design | Reuse source versioning, Location, company zone, canonical recorded-activity classification and controls; no site hierarchy, task engine, snapshot table or new business scheduling mechanism | PASS |

### Authorization gate

The owner explicitly approved the prepared concept and implementation proposal in chat on 2026-10-06, including the three-table [data model](data-model.md), [completion-slot-v1 policy](contracts/shipping.md) and live/Agent-overview clarifications. This later approval satisfies the previously separate schema/model gate; see [approval and analysis record](review.md). Checklist markers remain reviewer-owned and runtime verification remains pending. Production enablement, merge and default-route replacement are not implied.

## Repository Structure and Layer Changes

New domain/service paths:

- `packages/reality-core/src/reality/domain/shipping_performance.py`: input validation, effective quantity coverage and deterministic observation/model policy.
- `packages/reality-core/src/reality/services/shipping_plans.py`: reviewed source-backed statement acceptance/versioning.
- `packages/reality-core/src/reality/services/shipping_performance.py`: cohort-bounded batched read and domain evaluation.
- `packages/reality-core/src/reality/services/operations_cockpit.py`: business summary, supporting orders and evidenced reactions.
- `packages/reality-core/src/reality/tools/shipping_operations.py`: canonical read/propose vocabulary.
- `packages/reality-core/src/reality/web/operations_cockpit.py`: admitted active-member HTTP adapter.

Existing adapters/metadata to extend: `db/core.py`, `services/operational_cases.py`, `tools/operational_cases.py`, `web/operational_cases.py`, `web/app.py`, `web/api.py`, `mcp/server.py`, `cli/app.py`, command/resource/data-model/refusal catalogs and generated documentation. The migration task allocates the next free Alembic revision after inspecting the actual head; do not reserve a colliding numeric revision during planning.

Frontend additions: `apps/web/src/unified/OperationsCockpitPage.tsx`, `ShippingDayPanel.tsx`, `ShippingSupportingOrders.tsx`, `OperationalCaseRegister.tsx`, `useOperationalCaseControls.ts`, `useCockpitLiveRead.ts`, `OperationsActivityPanel.tsx` and `AgentAccessPanel.tsx`. Extend `api.ts`, `unified/routing.ts`, `UnifiedApp.tsx`, `Shell.tsx`, `pageIntroduction.ts`, `OperationalCaseDetail.tsx`, existing styling and localization.

Documentation: implemented behavior goes into `docs/WEB_SPEC.md`, new `docs/features/operations-cockpit.md` and the existing case contract. Do not edit the hosted reference/sandbox/CSP, archived visualization, live-demo profile, company setup or scheduling infrastructure.

## Design

### Reality flow

An authorized planning statement is proposed and reviewed through existing application decision conventions. Confirmed acceptance preserves its payload as an immutable Source version and typed planning evidence. It schedules existing accepted customer-delivery commitments, without creating promises or fulfilling them. Typed planning records are the evidence stage for these internal statements; no artificial business Document is created solely for dashboard presentation.

Effective Movements → ShipmentPackage → Shipment and attributed effective `handed_over` events establish physical contents and handover. The new pure observation uses their exact quantity/time/scope links, including corrections/supersession. Requirements point only to commitments and their parent planning evidence, not duplicate document/line/source FKs.

### Planning and forecast policy

Use direct explicit Location-as-dispatch-site assignments and the existing company business-day zone; site display zones are stated inputs. Propose `shipping_plan_statement`, `shipping_dispatch_requirement`, `shipping_capacity_window`; see [data model](data-model.md).

One current requirement schedules the full stated quantity of one commitment. A single commitment split across sites/days is not admitted in v1; an order with multiple commitments split across sites is supported. Quantity/revision conflicts mark coverage unresolved instead of reshaping the plan. Planned completion times per requirement produce the timed Soll; there is no curve-point table.

`completion-slot-v1` uses only explicitly stated, confirmed completion budgets for the accepted site-cohort work mix. It does not convert package counts, labor hours or piece rates into orders. Ready unfinished work is assigned deterministically within confirmed windows/cut-offs, under disclosed no-new-stock/readiness assumptions. Company forecasts complete an order only when all of its applicable site work can complete. The precise admission, consumption and time-interpolation rules are in [shipping.md](contracts/shipping.md).

### Service and adapter flow

Domain → shipping plan/performance services → shared tools → Web/CLI/MCP. HTTP and UI do not own cohort math or writes. New cockpit reads use normal admitted-company authentication plus active membership. Owner-only Engine Room endpoints remain unchanged. Existing member case controls and spec 377 default coordination remain unchanged. The register returns canonical coordination readiness, never gates existing cases on legacy CaseAdoption, and performs no rollout writes.

Add a new `operational_case_register` read: filters before pagination, complete matching totals and `after` paging. Preserve the old list response for existing callers. Case explanation derives current takeover actor/time/reason/decision from the matching control-revision BusinessEvent/ChangeProposal. Enrich actions through existing review/receipt reads; missing historical evidence remains unknown. `executed` never implies email delivery or carrier confirmation.

Return the register's own transient snapshot observation time and visibly retain
that time, as well as the Agent panel's independent observation time, on a failed
refresh. Missing metadata remains explicitly unknown; no browser receipt time is
presented as a server observation. This fulfills FR-018 through the existing
snapshot and UI lifecycle without changing schema, business rules or scheduling.

Extract shared current-revision/request-key/handback-digest behavior from existing Web case controls into the new hook. Preserve spec 377 default coordination and existing case policy/guards. No read enrolls history or transfers related billing/supplier/return work.

### UI availability and context

The initial server feature flag is removed by owner-approved FR-087. The permanent navigation and current-company capability endpoint remain; fresh existing company access authorizes operational reads without deployment configuration. Availability grants no mandates or ownership, and Home remains the landing page.

Namespaced URL state retains company business day, site, measure/filter, case and origin snapshot basis across Sales/Delivery/Inspector transitions. Company switching clears it. Contextual chat resolves an existing order/commitment; never pass a case ID into a commitment-ID prop. Cockpit starts with chat closed at desktop width; explicit opening works and other routes retain their existing behavior.

Use existing tokens/icons/shared formatters and all four supported languages/themes. The curve renderer consumes returned series and performs no operational derivation.

### All-day observation

Extend `services/activity_volume.py` with a bounded short-window canonical read and reuse its classification/first-recorded-entity deduplication, preserving current Home APIs. Expose it through the shared `operations_cockpit_activity` tool and thin adapters. Return 5/15/60-minute, 60-second bucket aggregates and the latest 50 inspectable event identities; company-wide recorded activity remains separate from shipping-site results and confirmed handovers. No additional persistence is needed for this clarification.

Implement the browser lifecycle with five-second foreground reads, an eight-second timeout, non-overlap, cancellation, hidden-tab suspension, immediate resume and capped failure backoff. Responses retain distinct observation times; don't claim an atomic snapshot across separate reads. Keep the day-based shipping curve primary, with the rolling graph and recent activity visible alongside it. Use stable IDs, bounded data and explicit following controls to preserve investigation. Refresh cannot change an exact control review or confirm a business action. Resolve Today on each server snapshot; retain pinned dates and open records across midnight. Follow the exact [live contract](contracts/live-observation.md).

Add an owner-guarded `operations_cockpit_agents` sanitized shared read in `services/operations_cockpit.py` and its thin tool/adapters. Reuse current MCP token and `services/mcp_authorization.py` effective-state rules and exact interaction attribution from `services/interactions.py`; introduce no registry/heartbeat schema. Distinct credential/grant identities and complete totals precede keyset paging; redact credential/personal material. Render a compact `AgentAccessPanel.tsx` with initial six rows, last-use/observed-action details and paged expansion. Restricted members retain other cockpit reads and receive an explicitly restricted panel. Current external execution remains unknown where Reality has no authoritative observation.

### Snapshot, totals and performance

Use one consistent read-only transaction for snapshot calculation. Return observation time, accepted plan/source versions, relevant-input fingerprint and tenant event watermark. The watermark is observation metadata, not identity or authority. Supporting orders re-evaluate current inputs; unchanged basis preserves consistency, changed basis returns an explicit re-evaluated notice. No historical snapshot authority is stored.

Aggregate the full cohort before pagination. Restrict input joins to selected day/site commitments and their relevant movements/events, with correction/supersession exclusion. Reuse canonical quantity/readiness rules in batch; avoid all-history `business_performance.overview`, per-order `shipment_explain` and counts from the first 200 rows. Prove bounded query count separately from measured wall time. No stale cache is introduced to pass performance. Exact opaque-ID cohorts use one typed PostgreSQL array bind instead of one parameter per ID, with caller tenant predicates unchanged. Canonical commitment terms may be passed between shipping, readiness and case assembly only within the same observation call; the register still loads every missing open case commitment. Fresh read-only REPEATABLE READ snapshots omit redundant post-read source/watermark comparisons because their visible versions cannot change, while caller-owned Connections retain both drift guards and initial source/intake validation remains mandatory. Case counts and keyset pages use SQL predicates built from canonical outstanding-order terms and return-state outcomes, preserving complete counts while avoiding historical case hydration. A full input fingerprint precedes a bounded 50-record basis preview; only selected supporting-order/deviation pages are converted for transport. Canonical readiness notices are omitted from fingerprint copies while original readiness fields and exact per-order evidence remain available. The protected Engine-bound gateway holds a caller authority connection and a separate snapshot connection. The reproducible ten-browser/four-read profile therefore uses existing `DatabasePoolSettings(pool_size=80, max_overflow=5)` and reports those limits explicitly; it does not change deployment defaults. Scalar and batch readiness share the canonical grouped physical-stock helper, including inverse movement corrections. Latest source metadata is joined to the exact original source cohort with explicit tenant scope, avoiding a large compound-key expression while preserving current-version/intake guards.

### Data and migration impact

Three new input tables with tenant composite FKs/checks/indexes. No historical backfill, current-case state fields, document statuses or persisted forecast. Source revisions and explicit accepted plan selection remain durable; replay cannot overwrite a later version. No process startup runs migrations.

Initially allocated after `0144_operational_cases`; integration onto current main places `packages/reality-core/migrations/versions/0146_shipping_plan_inputs.py` after `0145_default_operational_cases` as one linear head. Earlier verification described the initial chain; the PR integration reruns upgrade/downgrade against the actual combined chain. Upgrade, empty downgrade and a populated-evidence refusal have been verified in isolated disposable PostgreSQL. No live company was migrated. Presentation rollback disables the capability and preserves planning evidence/control decisions; dropping tables is not the normal rollback.

### Failure, security and tenant behavior

Preview binds exact input payload, current plan source and commitment meaning. Confirmed acceptance rechecks them under existing business locks, active actor membership and a replay-safe request key. Foreign/unknown IDs are non-disclosing refusals. Conflicting current plans or newer unresolved relevant planning/confirmation Sources produce unknown coverage; no convenient plan is chosen.

No read accepts Sources, executes providers, adopts cases or schedules work. Refresh failures retain the last snapshot marked stale, do not extend confirmed curves, and do not imply readiness or business success. Known zero and unavailable values remain distinct.

## Test Strategy and Traceability

The table records the original test-first plan. Executed outcomes, remaining gates and limitations are maintained in [quickstart.md](quickstart.md); a planned path alone is not passing evidence.

| Requirements | Level | Planned paths and initial failure |
| --- | --- | --- |
| FR-002–009, FR-012, DR-001–002 | Domain/service/story | `test_shipping_performance_domain.py`, `test_shipping_performance.py`, `test_shipping_performance_story.py`: absent evaluator; independent two-site quantity/time/capacity oracle |
| FR-003, FR-006–009, DR-001–003 | Input/migration | `test_shipping_plan_inputs.py`, `test_shipping_plan_migration.py`: absent typed inputs; source fidelity/current review/replay/constraints/tenant FKs |
| FR-010–011, FR-018, DR-005 | Service/adapter | `test_operations_cockpit.py`, `test_operations_cockpit_adapters.py`: absent shared reads; full totals/paging/basis/coverage/no writes |
| FR-013–015, FR-017, DR-004 | Case/browser | Existing case/control/retry tests plus cockpit tests: absent filtered register and derived attribution; preserve real control races |
| FR-001, FR-016, FR-019–020, SC-002/003/005 | Browser/routing | `apps/web/scripts/operations-cockpit-browser.mjs`, `operations-cockpit-routing.test.mjs`: absent optional route/context; reference comparison, languages/themes/keyboard/responsive layout |
| SC-004, DR-005 | PostgreSQL workload | `test_operations_cockpit_performance.py`: measured full declared profile, cold/warm runs, ten observers, complete-result/query-budget proof |
| FR-021–023, SC-007, DR-001/003/005 | Service/browser/lifecycle/workload | `test_operations_cockpit.py`, `test_operations_cockpit_adapters.py`, `operations-cockpit-live.test.mjs`, `operations-cockpit-browser.mjs` and workload tests: truthful recorded activity, ten-second healthy display, bounded eight-hour operation, stable review/inspection, recovery/isolation and day rollover |
| FR-024, DR-001/003/005 | Service/adapter/browser | Cockpit service/adapter/browser tests: manual and OAuth identities, duplicates/shared access, never-used/revoked/failed/unknown states, exact attribution, full paging, owner disclosure and no secret payloads |

Reuse shipment reads/story/domain/supersession, outbound-delivery, fulfillment-readiness, commitment-revision, CompanyTimeZone/DST and case-control regression suites. Add the new browser script to `apps/web/scripts/browser-suite.json`. Complete required backend/web/catalog gates after implementation; documentation-only planning does not require runtime tests.

## Rollout and Rollback

1. Record schema/input and forecast-policy approval; complete analysis with no CRITICAL findings.
2. Allocate and verify migration; ship dormant additive services with capability off.
3. Build an isolated acceptance company through approved shared services, not live-demo changes or direct ORM business-story writes.
4. Pass shipping/control/source/member/browser/reference/workload and deterministic live-session proof, record the separate eight-hour real-time soak, and complete required regression gates.
5. Enable a reviewed pilot through deployment capability configuration. Genuine approvals and existing entry remain accessible.
6. Disable capability for rollback, retaining records and responsibility. Default-route replacement remains a later specification.

## Review Risks

### Read transaction implementation decision (2026-10-06)

Production cockpit adapters will assemble each shipping read in a fresh, read-only PostgreSQL REPEATABLE READ transaction, using the existing SQLAlchemy/session patterns rather than persisting a snapshot. Authenticate current company membership before the read and recheck current access after releasing the snapshot; a data snapshot does not grant durable authority. Keep the snapshot's own observation time and watermark explicit. An unrelated stream of business writes must not invalidate every live read. Caller-owned transactions retain conservative source/version/watermark drift detection. Add committed concurrent-source/member parity proof before exposing data adapters; the initial caller-owned reader and deterministic tests alone do not establish production snapshot acceptance. No global isolation change, schema, scheduler or external effect is introduced.

Dispatch versus arrival meaning; capacity units/work mix; site-cohort versus whole-order completion; source/revision conflicts; split-site counts; event timing/corrections; responsibility versus already-started external effects; owner telemetry versus member business access; all-history reads and unmeasured scaling.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
| --- | --- | --- | --- |
| None | No exception proposed | Generic date reuse and untyped Fact/JSON forecasting are semantically inadequate | Concrete schema/model approved on 2026-10-06; no exception proposed |

### Identical in-flight observation decision (2026-10-06)

The unchanged ten-reader workload measured 29.385 s p95 despite a 3.522 s cold read after exact array bindings and call-local reuse. Identical concurrent Engine-bound reads now join one actively computing read-only repeatable-read observation, keyed by Engine, company, owner-only scope, operation and exact filters. Each caller independently checks current membership/role before joining and after obtaining its detached response. Remove the key before publishing a result or exception; a later call always opens a fresh snapshot. Caller-owned Connections never join. The process-local registry is bounded to 64 in-flight keys, with independent reads on overflow. This is request coalescing, not retained results, background scheduling or a new authority. Two new proofs first failed on the absent coalescer; exact concurrent joins, later freshness, independent response values, exceptions/context isolation and committed membership revocation then passed in a 30-test snapshot/adapter/delivery-policy regression. Full workload verification is still pending.

The ID transport binds one explicitly typed text parameter with PostgreSQL array element escaping and uses a tenant-scoped query predicate over `SELECT unnest(CAST(parameter AS varchar[]))`. The function scan evaluates the input once per query; an inline text-to-array cast in ANY was rejected after the large workload exposed per-candidate-row cast work. Empty/NULL/quoted/comma/braced/backslash/newline/string-NULL identities retain the same IN membership semantics, proven alongside a 70,000-ID cohort. Source metadata uses narrow tuple values and one source-ID/status ImportJob read, preserving exact original/current version and completed-intake checks. No SQL values are interpolated and no result is cached.

Registered public read responses are JSON DTOs. An in-flight leader encodes its completed DTO once, then each observer independently decodes that owned JSON value before its post-read membership/role check. Exceptions, including response encoding failures, retire the live key and propagate. No SQLAlchemy objects or source inputs are retained in a completed registry entry. The existing detached-response/context/revocation/adapters proof remains green (**25 tests in 8.59 s**). This avoids general Python deep-copy traversal per waiting observer without changing public response types.

Narrow read-only shipping rows retain only the selected original fields for requirements, quantities/revision links, handover observations and displayed order references. They do not hydrate unused ORM state or source payloads, mutate records, change cohort membership or sample any curve. The canonical readiness and commitment-term services remain the rule authority. Their narrow column inputs are used only inside the clean read-only cockpit snapshot; ordinary caller sessions retain ORM identity-map values and existing Decimal representation. Case explanation may reuse canonical terms from the same observation call, with scalar fallback for any missing commitment. The complete relevant regression passed 91 tests, with two additional standard/prepayment parity proofs. Enterprise timing is measured separately.

The sustained workload starts one canonical order writer concurrently with each forty-read ten-browser batch. A snapshot may include either the current cycle's committed order or exactly the prior committed count; every next-cycle read must include the prior commit. The last committed order is independently verified, with commit-to-observation time recorded. Cadence includes both the concurrent writer and all read responses; it never subtracts write time or relaxes the three-second p95/five-second cadence/ten-second visibility gates.

Daily-plan and collection-confirmation Source identities survive the bounded preview in `basis.planning_source_record_ids`; their metadata is prioritized across sites before the order-source sample. This preserves the most important forecast provenance without enlarging calculation cohorts or copying original payloads. Final shipping/source-priority/story/adapter proof passed 44 tests.

### Read-only planning metadata refinement

The isolated profiler identifies repeated cohort reads and unnecessary full ORM
records in the observation path. Restrict the existing current-statement selector
to original header columns, source identity/version and the original statement
action reference inside clean read-only cockpit snapshots. Read only the exact
reviewed proposal basis there; original Source payloads and proposal previews stay
lossless and accessible through existing Inspector links. Ordinary callers retain
the original ORM/pending-value behavior. The latest-version/withdrawal selector,
tenant joins, current-intake guards, complete quantities and full fingerprint
inputs remain canonical. No schema, retained cache or derived authority is added.
Stored-value observation parity and unchanged original payloads are required
before acceptance, followed by the unchanged enterprise workload.

The same clean snapshot may pass its original, tenant-scoped commitment/order
rows to canonical commitment terms, readiness and delivery-policy readers. These
private call-local inputs are filtered again by company and requested identities;
ordinary sessions ignore them and retain existing ORM behavior. No input survives
the read call. One-cohort-read/query-budget proof and complete stored-result parity
must pass, including stock corrections, holds, prepayment and delivery revisions.

### Final integration review: diagnostic reader boundary

The owner-only cockpit roster is an observation adapter, never a business calculation. Exact manual-access action attribution is assembled and redacted exclusively inside `services/interactions.py::latest_manual_actions`; `operations_cockpit.py` consumes detached dictionaries and never imports or queries the telemetry model. The architecture audit explicitly recognizes this single reader consumer and separately forbids direct telemetry access there. Shipping, responsibility and execution rules do not consume diagnostic observations. This implements the already approved FR-024 reader reuse without broadening owner disclosure or making telemetry business authority.

### Bounded case explanation input refinement

The unchanged standard enterprise run measured 5.204537 s p95,
5.337442 s cold opening and 7.507750 s commit-to-observation after original
shipping cohort reuse. The three-second acceptance gate remains red.
Batch original inputs for the already bounded register page inside the clean
read-only snapshot only. The existing canonical explanation and domain state
functions remain the authority; preserve full DTO parity, exact control
attribution, related returns, source gaps, obsolete actions and complete
unsettled execution totals independently of display limits. Inputs are private
and call-local, tenant scoped and bound to that session; ordinary callers and
mutating reviews keep their existing reads. No schema, completed cache or new
authority is introduced. Add a failing stored-result parity/query-budget proof
before implementation, then rerun affected case/control/source/snapshot
regressions and the unchanged enterprise workload.

### Overview-only detail projection refinement

The standard case-batched run reaches 2.437429 s opening/site p95 with exact
complete totals, but the 480-request continuous workload remains red at
3.327774 s p95. All twelve five-second cycles and final committed-order
visibility pass. The main overview may request deviation details only inside a
clean snapshot: complete work, canonical readiness, physical/source basis,
fingerprint, totals, sites and all curves are still calculated first. Construct
order detail DTOs only for the exact already evaluated at-risk or coverage-gap
orders; keep all matching identities before the existing 50-row preview so the
complete deviation count remains true. Full supporting-order reads and ordinary
caller-owned sessions keep the existing full detail output. No rule/cohort,
public interface, schema or retained result changes. Stored full-observation,
terms and exact filtered detail parity must first fail and then pass for healthy,
held and source-gap inputs before repeating the unchanged workload.

The bounded case input reader also skips known-empty optional original cohorts
(returns, sources, control decisions/actors). If the complete bounded link query
returns no links, no execution can be linked to that case page; otherwise the
independent complete executing-count query remains mandatory, including actions
outside the preview. This removes empty SQL round trips only, with the existing
full DTO/control/source/51-execution parity proof required to stay green.

### Shared original source metadata cohort

The final detail-projected standard run keeps exact totals but measures
3.196917 s opening/site p95 (2.538228 s first read), so acceptance is still red.
Batch the original source metadata/current-version/intake-status reads across
accepted site statements only inside the clean snapshot. The canonical
`source_basis` validator still checks each statement's exact selected IDs and
current-required IDs independently; a missing or superseded exact confirmation
for one statement must never contaminate or excuse another. Bind private inputs
to the same session/company and explicit source cohort. Normal reviews/mutations
retain their existing reads, full originals remain untouched, and fingerprint
inputs remain identical. Require failing normal/batched result and scoped-error
parity, then the existing source/version/shipping/snapshot/case regressions and
the unchanged enterprise workload. No schema, cache or additional rule is added.

## Usability follow-up plan (FR-025–027)

Retain service reads and business rules. Bound presentation with native accessible disclosures for site times and deviation evidence; show complete server totals separately from preview counts. Place supporting orders immediately after shipping, focus its labelled region when opened and restore the originating control on close. Use compact case rows, explicit responsibility/status, business-facing search/filter labels and replacement-page navigation. Preserve whole-case confirmation and foreground reads. Update all four locales. Constitution Check: PASS for every principle; no schema, scheduling, mandate or business-service change. Add many-cutoff/action browser regression before implementation; run frontend contracts/build/i18n and desktop/mobile verification. Broader rollout/load/soak tasks remain open.

## Operating flows follow-up design

Owner-approved FR-028–033 adds a shared `services/operating_flows.py` reader assembled as `flows` by the existing `operations_cockpit` snapshot/tool/HTTP response. Reuse batched canonical `core.commitment_terms` for complete customer/supplier open work, canonical exception evaluators for urgency/stock risk, canonical announcement/disposition services for return semantics, and Source reply/ack lineage. Rolling SQL aggregates and first-reply timestamps provide a bounded message-backlog curve; first-recorded business identities deduplicate intake. Preview records remain capped after full totals. No stored observations, schema, additional polling loop, new scheduler or mandate. Frontend `OperatingFlowsPanel.tsx` renders five cards with labelled current queues and 60-minute curves, exact Inspector links, independent company-wide scope and disclosure for each definition. Existing shipping/deviation/case panels remain intact. All existing four locales and responsive shared styles apply.

Constitution Check: PASS for Source lineage, Reality operational authority, no schema expansion, tenant isolation/shared services, planned failing proofs, explainable UI and read-time derivations. Rollback removes the additive response/UI panel; no data migration. Tests precede implementation: PostgreSQL independent cohorts/lineage/corrections/unknown states; authorized snapshot/adapter regressions; fixture browser density/live/stale/mobile and full frontend quality gates. Run lint/spec/business-annotation/doc-generation gates and rebuild/restart existing API/MCP/web locally. Measure actual local expanded observation; the older enterprise benchmark does not certify this added workload.

## Visual consistency follow-up plan (FR-034–036)

Use the existing cockpit stylesheet and shared `br-*` primitives. Remove stacked section margins and apply shared heading rules to standalone section headings. Structure `OperatingFlowsPanel` into explicit header, metric, chart, notes, evidence and footer slots; CSS subgrid shares content-sized tracks across sibling cards, with a natural independent single-column fallback. No empty metric records, invented stock chart, fixed whole-card height or business computation. Wrap section headers at the panel's available width. Apply one grouped segmented style to the existing activity/case buttons, keeping `role=group`, accessible names and `aria-pressed`; share subtle footer layout across existing navigation without changing cursor/review behavior. Give the existing Agent access filter its shared field/control classes.

Constitution Check PASS: every Source/Reality/business count, tenant boundary, service/tool, action/confirmation and live lifecycle remains intact. No schema, backend, scheduler, credential, mandate or dependency. Tests first: source-independent fixture geometry for common row starts (2px tolerance), heading/section rhythm, keyboard selection, expanded evidence, compact selection and footer styles, responsive narrow-panel/four-locale/themes. Existing frontend contracts, formatting, i18n, build and complete cockpit browser regression then local web-only build/activation and real live UI proof. Rollback is presentation-only. Scope/design has direct owner authorization; UX review has no unresolved ambiguity or Constitution exception.


## Central status overview plan (FR-037–038)

Export a compact OperatingStatusPanel beside OperatingFlowsPanel in the existing component module so both reuse the same area definitions, primary metrics and signal labels. Insert it above ShippingDayPanel in OperationsCockpitPage. Render the existing service signal without reclassification, with prominent styled indicators/text and exact primary metrics. Use shared br-* card/link/focus primitives, scoped CSS grid responsive to available content and static anchor links to stable card IDs; no execution controls. Unknown/missing summary retains five named areas without fabricated values or dead navigable targets. Stale overrides all summary signals to unknown as in the flow cards. No backend/domain/schema/service/tool/polling/scheduling/dependency change. Constitution Check PASS for every principle. Rollback removes this presentation-only summary. Planned tests precede implementation and cover each signal, placement, metric parity, keyboard anchors, stale/missing and four-locale/theme/narrow layouts; complete frontend/browser gates, docs generation and local web-only activation follow.


## Permanent Control Tower navigation plan (FR-039–040)

Render the shell destination unconditionally for the existing authorized company shell. Retain the current abortable same-company capability read, add explicit resolved state and only mount operational children after an enabled response for this exact company. Pending state uses shared ReadState, unavailable/failed capability uses a shared explanatory section and ordinary Home navigation; existing company menu remains the switching mechanism. No capability bypass or business-purpose conversion. Keep operational access-loss redirects after an enabled read unchanged. Rename display keys/titles and translations consistently to Control Tower without changing route or service identifiers; register the selected workspace name in the existing explicit i18n invariant catalog, preserving rejection of unapproved untranslated copy. Tests precede implementation, extending the existing full-shell browser proof to first-root, disabled/transient and company isolation; update routing-label expectations and run full cockpit regression. Constitution Check PASS for each principle, no schema/domain/service/tool/scheduling/policy change. Rollback is frontend-only.


## Workspace surface consistency plan (FR-041)

Use `--surface` for the existing `.operations-cockpit` canvas, matching the company shell/workspace ground. Retain section cards and shared `--surface-sunken` selection/detail roles. No global tokens, preferences, rules, data, reads, timers, controls, schema or dependencies change. Constitution Check: PASS for every principle; this is an owner-authorized presentation-only correction with frontend-only rollback. First extend the existing computed-style browser proof across four locales, both themes and supported widths, then correct the canvas. Verify contracts/format/build, full cockpit browser regression, spec/lint and actual local web-only activation.


## Case takeover discoverability plan (FR-042–044)

Move the single OperationalCaseRegister directly after OperatingStatusPanel and before shipping. Refine its existing card into a bounded compact summary (maximum 1120px) with clear ownership/takeover copy and actionable existing counts. Keep the existing search/filter/list/inspection workspace mounted inside an accessible disclosure, hidden initially except for bookmarked case selection. No duplicate counts, services, read lifecycle or business semantics. Opening automatic count uses the existing outstanding view; human count uses the existing human view. Preserve in-flight control state when collapsing; busy controls cannot collapse. Shared surfaces and responsive grid/neutral buttons retain four-locale/theme support. Constitution Check: PASS for every principle; owner-approved frontend presentation change, no schema, mandate, backend, dependency, new timer or global appearance setting. Tests first in the existing cockpit browser proof; full frontend quality and web-only activation follow. Rollback is presentation-only.


## Classic traffic-light presentation plan (FR-045)

Preserve the five canonical service signals and signalLabels. Group attention/progress/unknown CSS selectors under the same orange indicator/border color for both summary and detail cards, with critical red and clear green unchanged. Replace only the explanatory legend and its three translated entries. Tests first: extend the existing all-signals computed-style browser assertion and replay it in the locale/theme/responsive loop, including stale unknown coverage. No backend changes or separate palette abstraction. Constitution Check: PASS for all principles; owner-authorized presentation-only scope, no schema, authority, identity, service, scheduling or dependency change. Rollback is the scoped frontend palette/legend.


## PR enterprise action projection refinement (SC-004, T036)

The integrated full workload now contains canonical shared planning actions, and exposes excessive original action payload transfer on a bounded page. Refine only the existing snapshot-owned explanation-input holder: select bounded link identities first, deduplicate action/control identities, defer unused invocation input and load original proposed-review output once per action. Project exact recorded-result availability from the stored text for terminal action metadata. Preserve scalar explanation parity, per-case frozen business-review checks, source/control attribution, complete executing totals, limits and tenant scope; ordinary and mutating callers retain their original path. No input survives DTO assembly and no derived authority is stored. Spec impact: none; an equivalent read projection restores the existing SC-004 workload bound. Constitution Check PASS; no new schema, policy, case family, execution mandate, cache or scheduler. Tests first: shared large executed/proposed action regression plus existing scalar/batched parity, privacy/limit and 55-query budget; full unchanged enterprise/continuous-workload and CI gates follow. Review: no unresolved clarification or CRITICAL semantic finding.

The enterprise profile pins the canonical shipping reader's existing explicit
observation instant to fixture capture. Otherwise late-day setup can consume the
window's spare slots before measurement. Actual latency/cadence/change-visibility
use real monotonic time and real concurrent commits; business totals, query
budgets, distributions and limits are unchanged. This test-only clock correction
restores the declared scenario, not a forecast rule.

The measured profile attributes the remaining read cost to historical ORM
materialization in operating flows and exception inputs. Refine only clean
cockpit snapshots: use the canonical delivery SQL expressions for complete
open/supplier-received cohorts, and scope the commitment exception inputs to
the exact open promises that its derivator evaluates. Other exception classes
retain separate original scopes, and ordinary callers retain ORM semantics.
Test scalar/snapshot full DTO parity and absence of historical promise ORM
materialization first; then rerun unchanged enterprise and full CI gates.
Spec impact: none; equivalent read projections only. Constitution Check PASS.
No new rule, schema, retained cache, case family or mutation authority.

Measured shipping/site reads currently repeat independent company-wide flows.
Place those flows in the existing authorized activity snapshot instead, and lift
its existing UI lifecycle to the page to serve status, flow and activity panels.
Retain four read lifecycles, current timestamps, stale/access isolation, filter
separation and stable child investigation state. No timer/endpoint/schema/rule or
cache is added. FR-033/contracts now explicitly define the observation boundary.
Test activity flow authority/absence from shipping first, then fixture/all-day
UI and unchanged four-read enterprise cadence. Constitution PASS; no unresolved
clarification or critical review conflict.

The full forecast currently transports one point per completion slot (10,000 in
the declared profile). FR-023 now makes the bounded daily curve explicit: keep
small exact-event series; aggregate dense series into exact cumulative counts
at five-minute boundaries, including endpoints, and disclose resolution. Count
every source-backed order before projection; retain full fingerprint and exact
supporting-order/evidence readers. This is chart aggregation, not cohort sampling
or invented handover times. Test independent dense-series counts, duplicate
times/opening/end/out-of-window behavior before implementation. Constitution
PASS; no business rule/schema/authority/cache change or unresolved clarification.

Exact-head CI confirms every other gate, but SC-004 remains red at 3.235 s p95
(3.075 s cold; 3.087 s committed-change visibility). Preserve the unchanged
three-second limit. The source basis currently transfers original/current
metadata twice and joins the entire source table before selecting latest stream
versions. Replace these with one tenant-correlated LATERAL latest-version read
using the existing stream/version index. Preserve complete original/current
metadata, missing-reference and intake/current-required refusals. Existing
source/version/snapshot proofs precede the equivalent query refinement; inspect
its full-profile query plan and rerun complete CI. Spec impact: none, no new
rule/schema/cache/authority. Constitution Check PASS.


The final exact-head profile passes opening/site p95 (2.976 s) and committed
visibility (2.928 s), but its four-read live cadence fails at 9.847 s in cycle 2.
A newly accepted unreserved order activates commitment exception trace loading:
that snapshot still materializes every historical Document/Source/Line before
returning one current risk. Profiled activity rises from 1.960 to 7.211 s after
one real canonical order commit. Restrict only the existing open-commitment input
scope to its exact referenced documents, lines and original source metadata;
leave all other class scopes and ordinary readers unchanged. Add independent
scalar/snapshot risk/source-trace parity and historical payload/materialization
proof first, then rerun unchanged live cadence and complete CI. Spec impact:
none; equivalent read projection under DR-005/SC-004. Constitution Check PASS;
no rule, source mutation, retained cache, schema or authority change.


The actual UI never reads the shipping snapshot's duplicate `supported_cases`:
its always-mounted responsibility panel already owns the independently authorized
case-register lifecycle. Remove that redundant shipping calculation/field, retain
the exact full register and case-linked deviation explanations, and explicitly
define the independent authority in FR-033/contracts. Complete case counts remain
asserted in every register request of the unchanged ten-observer four-read live
profile; add the same full-count proof outside the shipping-only opening samples.
No request, reader, live cycle, volume, limit, business claim or UI state is removed.
Test that shipping does not invoke the register, and that the independent register
retains complete evidence/counts, before implementation. Constitution Check PASS;
no new authority, schema, timer or retained cache.


Refine the reviewed trace cohort further to exactly the current finding IDs,
collected before the existing three shared evidence reads. Ordinary derivation
retains immediate traces; clean snapshot derivation fills the same immutable
finding DTOs after its complete calculation. This avoids loading all 9,000 open
orders to explain one unreserved arrival while retaining bounded queries when
all promises are risky. Use existing full scalar/snapshot trace equality and a
many-current-risk bounded-query regression; no findings or source links change.
Case-linked shipping deviations also reuse the existing bounded original-action
projection for their at-most-50 exact cases, and then preserve their existing
six-action presentation limit. Constitution PASS; equivalent reads only.

SC-004 requires reported hardware and cold/warm measurements. Retain the
existing exact printed JSON measurements as JUnit properties for successful and
failing CI runs, including every live epoch and final visibility; normal pytest
capture otherwise omits passing measurements. This changes only verification
artifact reporting, not product behavior, scenario data, time or acceptance.
Spec impact: none; no additional business authority or Constitution exception.

## Complete canonical readiness fingerprint

Review before implementation: replace duplicated readable readiness dictionaries in the full hash input with every canonical frozen-readiness dataclass field, under fingerprint format `shipping-inputs-v2`. Preserve exact Decimal strings, tuple ordering, all IDs and every future declared field. Generate unchanged readable dictionaries only for the first-fifty disclosed preview and selected full/deviation order details, reusing each within the call. No cache survives the call, no rule/schema/source changes. Tests first: a 63-ready-order complete cohort must materialize only fifty readable previews in the narrow overview; full/scalar/supporting parity and canonical-field fingerprint sensitivity remain mandatory. Constitution Check PASS; FR-046/SC-004.

## Four-reader allocation review

The 32ddbe91 full profile passes cold/opening p95 (2.365/2.240 s), all twelve five-second cycles and committed visibility, but fails live-read p95 at 4.047 s. Concurrent diagnostics isolate shipping and full open-commitment ORM allocation. Before implementation, extend exact current-risk trace tests to prohibit open Commitment ORM retention, add real linked/unlinked physical handover scalar/snapshot parity with zero Movement/Package/Shipment ORM allocation, and run all stock-overcommitment scenarios through fresh narrow reads. Project only consumed promise/physical metadata in clean snapshots. For stock-overcommitment, use the existing canonical net-movement SQL builder restricted before aggregation to the same open promise/type cohort; ordinary readers and unit/kit/revision/correction rules remain unchanged. Constitution Check PASS; equivalent reads under DR-005/SC-004, no rule/schema/cache/authority change.

Fresh-authority review: every one of forty concurrent callers performs independent before/after access checks. The current canonical `_member` reads company, user and membership separately, then `_viewer` repeats company/member reads. Add an optional fresh joined read to the same canonical `_member`: exact company ID/business-purpose/unarchived, active user and active same-company membership, with populate-existing on the membership. Existing callers retain their original path. `_viewer` delegates to this canonical fresh path and keeps both per-caller checks and owner-role refusal. Tests first: exactly one access query per check, stale cached user/company/member and committed revocations (including owner role) cannot escape; existing coalesced waiter revocation and foreign/feature-off/dirty-session proofs remain mandatory. Constitution Check PASS; no shared authorization, retained access cache or permission change.

Forecast allocation review: preserve completion-slot-v1 exactly while avoiding generator/min/max allocation for singleton order/site groups and replacing Fraction ceiling with the identical integer ceiling of positive period × slot / slots. No policy/version/precision/rounding/cohort changes. Add an independent seven-microsecond/three-slot expected-time proof before implementation and retain all split-site/partial/gap/capacity/quantity domain oracles. Spec impact: none; equivalent computation under FR-004/007/SC-004, Constitution PASS.

### Final live allocation refinement

Spec impact: none. Preserve DR-005/SC-004 and canonical revision/correction rules while projecting private scalar rows to call-scoped immutable tuples and reusing tenant-scoped latest explicit revision relations in the full fulfillment cohort. No completed observation or authority is retained. Validate immutable typed metadata, original scalar parity (including equal-time identity ordering and null-only revision fallback), then the unchanged full enterprise workload and all required gates.

### Final shipping-only allocation refinement

Preserve complete DR-005/FR-046 inputs and exact standard v2 fingerprint bytes. A same-company source is necessarily at least its own stream version: retrieve only strictly newer metadata, otherwise retain every original field as the latest metadata. Keep all intake/current-required refusals. Avoid circular-container tracking only for the constructed acyclic typed basis; independently compare the full bytes with the standard encoder. Select exact deviation IDs and bounded preview keys after full calculations; never prune the calculation/hash/supporting cohort. Run full source, allocation, shipping and control regressions, then unchanged enterprise acceptance.

The final shipping-only refinement may project owner-reviewed Action headers to all original source identities and all original quantity-revision bindings for clean observations only. Preserve missing/empty legacy review and binding semantics. All original Action payloads and ordinary/mutating validation remain unchanged, and every current source/readiness input stays in the full v2 fingerprint. Independent retained-input equality and complete scalar/snapshot proofs precede this allocation change.


The cc4d599d exact-head run passes every functional/browser/installer gate,
opening/site p95 1.852 s, all twelve live cycles (maximum 3.168 s), and final
visibility 5.051 s. Aggregate live p95 alone remains red at 3.062 s; overview
p95 is 3.120 s. Preserve the original three-second limit and complete workload.
Profiled complete shipping inputs still allocate unused cohort filters for
preloaded canonical promises/documents, and repeat ORM row-processing for fresh
scalar-only metadata. Review equivalent allocation only: build unused statements
only in their actual read branch, and execute selected scalar metadata through
the same Session-owned transaction Connection only in a clean consistent
snapshot. Ordinary/dirty readers retain Session execution/autoflush; no ORM
entity query changes. Independent exact typed-value/transaction/dirty-state
and preloaded canonical parity regressions precede implementation. Spec impact:
none under DR-005/FR-046/SC-004. Constitution Check PASS; no authority, source,
schema, field, cached observation, query workload, cadence or threshold change.

The private scalar Connection result is fully buffered once within its current read call, preserving every row, label and value while avoiding one driver fetch call per row. The result is consumed only by its original caller; no shared/completed result is retained. Existing typed metadata, same-transaction and ordinary/dirty Session proofs cover this allocation boundary.

## Stable analysis interaction (FR-057–058)

Render the five operational instruments as non-interactive summaries; remove selected
props, navigation text, links and selected border styling from OperatingStatusPanel.
Keep the explicit Finance workspace link. Replace the repeated area button group
with one shared native br-control select labelled Analysis area. Keep all existing
area articles mounted/hidden so evidence disclosure state survives switching. Change
selectArea to update state and replace the current hash through history.replaceState
with history.state preserved, without focus transfer or requestAnimationFrame/scroll.
Retain hashchange/bookmarked initialization and company reset. No new routing field,
service, dependency, read, schema, scheduling or mutation. Constitution Check: PASS
for every principle; presentation-only scope explicitly authorized by the owner.
Tests first: exact one selector/no summary navigation, keyboard focus and stationary
analysis heading, bookmark/reload/company reset, existing state/curves and layout.
Run frontend contracts, four-language audit, formatting/build, cockpit browser matrix
and controlled session; activate only web and inspect actual company. Rollback is
the scoped frontend change.

## Hierarchy and observation utilities (FR-059–061)

Move the one existing OperationalCaseRegister to the first row beside shipping and
move the existing activity/Agent column beside analysis in the second row. Retain
keys, all readers, supporting shipping investigation, selected/disclosure/control
state and lower deviations. Use align-items:start and remove register height:100%;
apply the compact register layout in its new parent. Frame OperatingFlowsPanel itself
as the card and strip only inner article padding/border class. Put the single area
field in its header; move long scope/observation copy into a compact footer. Keep all
area articles mounted and both message plots unchanged. Unify scoped card padding and
heading rhythm using shared surface tokens; preserve phone container breakpoints.
Reuse shell-icon-button and existing Lucide Info/Pause/Play/List/Minimize2/X icons,
localized aria-label/title and aria-expanded/pressed controls. Observation closes stay
read-only and all business/control/review text remains. No component library, schema,
service, poller, dependency or routing change. Constitution Check PASS for every
principle; owner-authorized frontend hierarchy refinement. Tests first: priorities
and stack order, no nested analysis card, natural case height, consistent styles,
labelled icon keyboard toggles and unchanged evidence/control/live state. Run frontend
contracts, formatting/build/languages, full cockpit matrix and controlled lifecycle;
activate frontend only and inspect the real company. Rollback is presentation-only.


## Shared shipping/flow analysis refinement (FR-062–064)

Owner scope review: explicit request for the same location and shipping as first option;
no clarification outstanding. Presentation only; Constitution Check PASS for shared
services, tenant scope, lossless evidence, no schema/writer/poller or business-rule change.
Extend selection with shipping while retaining the existing flow keys. The common
OperatingFlowsPanel frame renders the existing ShippingDayPanel in embedded mode and
keeps all views mounted/hidden; it owns one selector. Put the supporting-order component
below that frame in the same left column, hidden with shipping but still mounted. The
right column contains the sole register, then log/Agents. Preserve component keys,
source/control state and all reader lifecycles. A global shipping investigation selects
shipping before revealing its existing focusable supporting panel. Missing flow evidence must not remove
the shipping option. Business-day/site filters still affect shipping only.

Tests first: default/first option, single frame, stable switch/bookmark/reset, basis and
supporting-investigation restoration; revised desktop/narrow hierarchy; retain the full
locale/theme/viewport matrix, source/basis/shipping/missing/stale/manual-control tests
and controlled lifecycle. Run contracts, language audit, formatting/build/spec checks,
then update only local web, inspect actual company and update the existing PR. Rollback
is the preceding web revision; no data or migration changes.


## Compact Operations workspace (FR-065–067)

Explicit owner scope covers hiding secondary right panels behind a switch and
contextual shipping blockers. Requirements review has no unresolved clarification.
Constitution Check PASS: presentation only, shared services/readers, tenant isolation,
evidence and reviewed controls unchanged; no domain/schema/tool/polling changes.
Add a small OperationsWorkspacePanel using local state, one native select and mounted
hidden wrappers for the existing three components. Use shared card styles and scope
embedded child framing/padding to this workspace only. Key workspace by company.
Add a ShippingDayPanel child slot for the existing deviations component, embedded
in a native counted details disclosure; keep its state mounted across analysis swaps.
Keep supporting investigations in the same left column. No new dependency or reader.

Tests first: two frames/default/options/keyboard/focus/viewport/history, hidden panels
excluded from traversal, manual draft and pause/Agent inspection retained; counted
shipping disclosure closed/default, locality and state restoration. Adapt previous
geometry assertions to the explicitly superseded stack without deleting prior
control/source coverage. Run contracts, full viewport/theme/language matrix, eight
controlled hours, audit/format/build/spec/diff. Activate web only, inspect the real
company and update PR 383. Rollback is frontend revision only.

## Compact instrument inspection (FR-068–070)

Owner scope accepted by explicit request; no open clarification. Constitution Check:
all PASS. Extend the existing read-time partition helper to retain per-unit group
membership internally; expose only bounded previews (eight per group and eight for
all) in operating_flows.observe. Batch labels for preview document/item IDs only,
using tenant scope and the same snapshot. Existing count DTO stays unchanged.
Local-mail previews reuse the original oldest unanswered cohort. Stock shortfall
copies existing causal_values; no quantity recomputation. No new endpoint/tool,
schema, dependency, poller or permission. Shared snapshot and ordinary paths remain
identical. Existing Inspector paths provide evidence beneath each row.

Use one native compact modal, state local to OperatingStatusPanel, per-count
buttons and one group selector inside the modal. Render current snapshot previews;
stale retained rows carry a warning. Unknown counts stay unavailable and absent
flows disable triggers. Eight-row shown/total caption plus workspace access is the
explicit preview contract; no pretending the preview is the complete register.
Tests first: service complete membership/deduplication/parity and source/stock
labels, browser activation/empty/group/Escape/focus/no-scroll/URL/no extra reads,
phone/theme/language coverage. Verify relevant backend suites, frontend contracts,
audit/build/format/spec policy and full cockpit browser matrix; review and activate
API + web only, preserving simulator/MCP workers. Rollback is prior API/web image;
no data migration. Existing enterprise and real-soak release gates remain open.

## Daily plan absence recovery

FR-071–072: Add a read-only physical activity projection in shipping_performance.py using effective Movement and ShipmentEvent/Package relationships, scoped to tenant, dispatch location and company-day interval. Return distinct booked orders and effective first-handed-over packages, cumulative points and a bounded original-record/source preview within the existing fingerprint/snapshot. Keep canonical cohort totals unchanged. Render a compact actual-activity strip/plot independently of missing-plan feedback; unknown deviation total remains unknown. No schema, endpoint, tool, timer or business authority changes. Tests cover deduplication, correction/supersession, boundaries and isolation before implementation, then frontend contracts, browser fixture proof, formatting/localization/build and actual local inspection. Constitution Check: PASS on all eight principles; observations are read-time only, recorded timestamps are preserved. Existing enterprise release gates remain open. Rollback: remove additive DTO/UI projection without changing stored business data.


## Single selected-topic heading

FR-073: Let OperatingFlowsPanel and OperationsWorkspacePanel own the selected-topic
h2 and stable category eyebrow. Remove the repeated flow article heading; use
explicit embedded presentation props on shipping/case/log/Agent children, preserving
standalone defaults and stable accessible region labels. Retain descriptions and
existing icon controls in compact context rows. No business/service/schema/polling
change. Test the existing product browser matrix first for one main heading in
each card, selected-topic changes, matched typography and retained state. Run
frontend contracts, localization/format/build/spec checks and actual local browser
inspection. Constitution Check: PASS, presentation only with no authority changes.
Rollback: restore prior component headers; no stored data changes.


## Full instrument tile activation

FR-074: Extend the existing native primary-count button's hit area to its containing
tile using a positioned CSS pseudo-element. Risk buttons remain siblings above that
hit layer; disabled primary buttons create no hit layer. Keep the same handlers,
dialog and exact shared snapshots. Retain full-tile hover/focus and update the short
four-language instruction. Browser tests first click title/meter/status/padding,
check all-work selection and keyboard/focus, and retain the existing risk/filter/
modal/full-matrix proofs. Verify frontend contracts, audit/format/build/spec policy,
then activate only the web locally and update existing PR. Constitution PASS; no
service/schema/business/authority/polling change. Rollback removes the additive hit
area styling and restores the existing count instruction.


## Readable content grouping

FR-075: Extend explicit Metric presentation metadata with interval membership,
render current/recent definition-list groups in OperatingFlowsPanel, and keep
message coverage/change notes with its backlog Curve through an optional footer.
Use semantic section/figure boundaries, shared border/surface tokens and aligned
label/value rows. Bound shipping plan plots in ShippingDayPanel and use the same
CSS rhythm for shipping counts, workspace introduction/actions, manual preview,
event/Agent lists and panel headers. No new domain/service/tool/schema/polling
changes or copied business rules. Product browser proof first validates group
counts, boundaries/containment and scope-note ownership; retain complete matrix
for locale/theme/responsive/selection/action evidence. Frontend contracts, build,
localization, format and spec policy follow; activate only web and inspect actual
company. Constitution PASS for all eight principles, explicit owner presentation
request has no unresolved clarification. Rollback restores the prior grouping
markup/styles without affecting data. Existing performance/CI/release gates remain.


## Viewer observation timezone regression

FR-019 repair: use existing formatZonedDateTime for general observation metadata
in OperationsCockpitPage, OperationalCaseRegister and ShippingSupportingOrders.
Use formatCalendarDate to retain the business calendar date in ShippingDayPanel context.
Remove the case register's company-zone override; retain shipping's explicit
business/site clock formatting and UTC dateTime attributes. Existing product
regression first fails on the UTC header, then verifies UTC/Tokyo observation
metadata alongside unchanged business clocks/cutoffs and stale-time retention.
Run full cockpit browser, frontend contracts/audit/build/format/spec checks,
activate only web and inspect the actual Berlin preference. Constitution PASS;
no unresolved clarification, schema, preference mutation, service or authority
change. Rollback restores the prior formatter call. Earlier release gates remain.


## Unified analysis and object-case presentation

FR-076/077 use two small presentation-only wrappers in AnalysisSections.tsx for metric groups and figure titles, shared by ShippingDayPanel and OperatingFlowsPanel. Keep each existing SVG renderer, counts, formatter, reader and inspect handler. Align shipping's clickable metric cells to the shared metric grid; place plan plot before actual activity and disclose site tables. Shared OperationalCaseDetail receives explicit named groups and dedicated operationalCases.css; OperationalCaseControls imports that CSS so standalone object pages and cockpit reviews share control geometry. No generic br-card rule is introduced. Existing translations are reused.
Constitution Check: all eight principles PASS; browser-only presentation retains services, tenant scope, UTC values and original evidence. Owner explicitly authorized the proposed layout and preceding case CSS repair. No unresolved clarification, new schema, service, dependency or authority. Test first: browser assertions fail on old shipping wrappers and unstyled case cards. Verify existing takeover retry/handback and cockpit locale/theme/viewport matrix, frontend contracts/audits, production image/build, format/spec policy; activate only web and inspect actual shipping/messages/object panel. Rollback restores prior presentation files. Existing CI/enterprise/soak gates remain open.


## Cohesive instrument overview

FR-078 changes only OperatingFlowsPanel.tsx and operationsCockpit.css: use one bounded overview, a CSS row subgrid for existing tile slots, label/count risk rows and a shared centered legend footer. Preserve native primary/risk buttons and Finance link; no extra reader, calculation, source, translation, service, schema or dependency. Empty known-zero meters render no segment, while unknown/stale meters retain their existing hatch. Test-first geometry/zero/legend assertions extend operations-cockpit-browser.mjs, followed by the retained interaction/locale/theme/viewport matrix, frontend contracts/audit/format/build and spec policy. Constitution Check I–VIII PASS; scope explicitly authorized, no clarification or critical issue. Rollback restores the previous presentation. Activate only local web and update the existing PR; earlier CI/enterprise/soak gates remain open.


## Business case overview and evidence briefing

FR-079 adds kind_counts to the existing operational_cases.register_cases aggregate: group the same canonical outstanding/completed/abandoned clauses by kind, retain legacy global counts by summing grouped observations, and return zero rows for supported empty kinds. No schema, new case family or execution-state inference. API type is additive. OperationalCaseRegister publishes its current page/status to OperationsCockpitPage; BusinessCaseOverview uses that same live observation and opens an exact-filter register preview only on demand, with cancellation and original object links. OperatingStatusPanel accepts supporting content after the shared legend. FR-080 uses the existing observation in a separate compact OperationsDeviationsPanel presentation; all causal caveats and full evidence remain. Native disclosures default closed, retain mounted state, and reset by company key. Reuse translated vocabulary and add four-language copy for new labels.
Constitution I–VIII PASS; owner explicitly authorized restoring the useful reference concepts. No unresolved scope or critical finding. Supported goals remain exactly the two canonical kinds. Test first: grouped register service/tenant/completed-manual proof and browser missing upper table/briefing. Verify affected PostgreSQL case/cockpit/adapter/snapshot tests, frontend contracts/audit/build/format, full cockpit browser matrix, scoped lint/business annotations/spec/catalog, API/web activation and actual company inspection. No migration or runtime/Agent restart. Existing release/enterprise/CI/soak gates remain open. Rollback reverts additive observation and presentation.


## Compact shipping deviation tables (FR-081)

Replace both list/card modes in OperationsDeviationsPanel.tsx with a single local DeviationTable renderer over the same CockpitObservation rows. Four columns retain order reference, first held cause/risk, exact responsibility and first recorded proposal/status. Each detailed row group adds a native full-width evidence disclosure; reuse the existing held blockers/actions and shortest original links. Retain upper three-row/detail four-row bounds, Show more, inspection, totals/unknown states and caveats. Replace unused card-grid CSS with contained table/header/cell/disclosure styling in operationsCockpit.css; add only the cause column translation. No domain/service/API/schema changes. Rollback reverts presentation only.

Constitution I–VIII PASS: same service DTO/evidence, tenant scope/opaque paths and confirmed controls; no derived authority or new infrastructure. Owner approved the compact-table scope. Tests first: missing semantic table/column/aligned summary-row proofs in operations-cockpit-browser.mjs; retain all evidence and inspection assertions. Verify full cockpit locale/theme/viewport/live/control browser matrix, 478 frontend contracts, localization audit, production build/image, formatting, spec policy and diff. Activate only web, inspect actual company and update existing PR. Backend/catalog tests need no rerun: business services/tools/output are unchanged.


## Stacked monitoring and one responsibility entry (FR-082)

Make OperationsWorkspacePanel a stateless stack of existing standalone activity/Agent cards; remove the right selector and embedded frames. Registered Agents is the Agent card heading, localized as Angemeldete Agenten in German. Move the single OperationalCaseRegister into BusinessCaseOverview through a child slot and mounted native Cases & takeover disclosure; suppress duplicate ownership totals through an explicit presentation prop. Automatically open both disclosures for a case bookmark, retaining original controls, reader and observation callback. Closed disclosures retain state and company-key remount resets it. Preserve all exact authority checks and evidence; no changes to services, timers, schema or API.

Constitution I–VIII PASS. Explicit owner request settles placement and copy; no unresolved clarification. Test first: simultaneous right-card order/frame/heading and upper-only bookmarked controls with no repeated counts. Adapt obsolete selector assertions while retaining all takeover, handback, review, stale, denial, Agent ownership, event pause, focus and full responsive/locale/theme proofs. Verify browser matrix, frontend contracts, audit, build/image, format/spec and semantic diff; activate only web and inspect actual company. Rollback reverts presentation. Existing CI/enterprise/soak release gates remain open.


## Compact risk legend (FR-083)

Keep four original labels/swatches and move only the two explanatory paragraphs into a native details element with a labelled existing Info icon. Use scoped compact footer/legend spacing and a bounded theme-token explanation panel anchored to the whole footer. Escape closes native disclosure and returns focus without scrolling. No translation/schema/service/reader changes. Constitution I–VIII PASS, owner explicitly requests less legend space, no unresolved clarification. Test first: closed desktop height, retained labels/copy, keyboard reveal/Escape/focus/history and narrow containment; retain full cockpit matrix/contracts/audit/build/format/spec checks. Activate only web and inspect actual company; update existing PR. Rollback reverts presentation. Earlier release gates remain open.


## Observed live feedback (FR-084)

Use two small pure presentation comparisons in cockpitLiveSignals.ts: finite numeric differences within one current context, and newer unseen event IDs within the same displayed context/sequence boundary. ObservedMetric.tsx keeps a local observation baseline and one finite CSS highlight; OperationsActivityPanel keeps a displayed-event baseline, preserving pause/inspection. Both invalidate stale/context baselines before reusing current data. Promote the existing per-minute chart into a compact always-visible scope-labelled band; keep period controls and detailed measurement caveat in the native disclosure. CSS animation completion clears highlights; no additional timers/readers, authority, success inference, mutation, schema or dependencies. A small useCockpitMotion.ts preference subscription suppresses and clears pending feedback while preserving a current baseline, so re-enabling motion cannot replay old changes. CSS also disables bar transitions. Zero-activity buckets have zero height.

Constitution I–VIII PASS. Owner explicitly requests watchable real activity, no unresolved clarification. Tests first: pure comparisons for initial/equal/change/replay/context/reset and browser visible band/new-row/metric change, pause, finite completion and reduced motion. Retain full cockpit browser matrix, contracts/audit/build/format/spec checks; inspect actual local web and update existing PR. No backend/catalog changes. Rollback reverts presentation. Existing CI/enterprise/soak release gates remain open.


## Instrument mini trends (FR-085)

Add InstrumentTrend.tsx and instrumentMiniTrend.ts as presentation adapters over the existing OperatingFlows DTO. The small pure helper selects named bucket fields or mail backlog points, converts invalid/uncovered values to gaps, and maps exact timestamps/values into a bounded SVG path with no interpolation across gaps. Current stock risks are not historized: its mini plot labels the existing dispatch/receipt record counts. Finance has a truthful no-history footer; keep its current native whole-tile link and remove only the repeated workspace label/arrow. Shared CSS subgrid row seven aligns the six 32px plots/short captions; no scrolling or new selection controls. Original previews, risk partitions, finite live cues, full plots, shared readers and domain services remain unchanged. No additional data, schema, dependency, timers or retained history; no catalog regeneration. Rollback reverts presentation.

Constitution I–VIII PASS. Explicit owner authorization includes choosing a feasible period; held rolling-60-minute data provides the smallest truthful implementation. No unresolved clarification. Test first: mini-trend selector/time/gap/zero comparisons, followed by six-footers/source/title/Finance-link/alignment browser proofs. Retain full cockpit four-language/two-theme/viewport/control matrix, frontend contracts/audit/build/image/format/spec policy and actual local visual review; update existing PR. Earlier release/enterprise/soak gates remain open.


## Shared page header (FR-086)

OperationsCockpitPage already renders inside Shell, which supplies the canonical page title/Info/live-monitor/chat controls. Remove only its second body hero and nested padding. Reuse filterChips from FilterChip.tsx around the exact existing native day/site selects; keep pinned-date input and unchanged live status in a compact local scope toolbar. Scope only local layout CSS and remove obsolete cockpit-header/filter overrides; Shell and global header/filter styles stay unchanged. No new component architecture, data, services, reader, scheduling or authority. Rollback reverts this presentation increment.

Constitution I–VIII PASS; owner explicitly requests autonomous consistency with other pages and existing shared surfaces settle scope. No unresolved clarification. Tests first: operations-cockpit-shell-browser.mjs single H1/header-control/standard-inset regression and operations-cockpit-browser.mjs shared-filter/compact/contained toolbar proof in the existing locale/theme/viewport matrix. Verify both browser suites, frontend contracts/audit/build/image/scoped format/spec/diff and actual local web; activate only web and update existing ready PR. Existing CI/enterprise/soak gates remain open.


## Recent-activity visual alignment (FR-084 refinement)

Owner requests removal of the nested chart frame. Scope is only operationsCockpit.css: remove signal border, radius, background and horizontal padding; preserve chart height, baseline, bar geometry, counts, scope, pause and reader behavior. Constitution I–VIII PASS; no ambiguity or domain/service/schema change. Verify with the existing full cockpit browser matrix, production build, formatting, spec policy and actual local screenshot. No new tests for this reversible styling change; existing live/control/responsive proofs cover retained behavior. Rollback restores the prior scoped CSS.


## Mini-trend observation time (FR-085 refinement)

Use existing value.observed_at in InstrumentTrend.tsx beside the period; formatTime uses the user timezone, a semantic time datetime and localized full-date title/label expose exact meaning. Preserve stale wording and absent observation. Add matrix assertions before implementation for six exact timestamps and Berlin presentation, retain contained responsive footers. Constitution I–VIII PASS; owner explicitly requests this narrow presentation. No new clock, polling, data/schema or authority. Existing full cockpit/contracts/i18n/build and actual visual proof apply.


## FR-087 implementation plan: universal company observation

The owner requested a separate green PR on 2026-10-07, removed the deployment switch, and clarified that all companies including Playground are included: anyone already allowed to access the company may open Control Tower. No unresolved scope clarification. Existing sensitive owner-only inventory and all mutation authority remain protected.

Constitution Check: PASS for all eight principles. Shared read services remain tenant-scoped, evidence-backed and read-only. Reuse the canonical Playground run/owner/account readiness check; do not weaken business-only operational-case controls or egress. No schema, derived authority, infrastructure or external effect. Explicit user scope approval is recorded; merge/deployment is separate.

1. Tests first: absent/obsolete switch values; owner/member/admin business reads; ready practice/temporary Playground, verified pending owners and readable archived runs; private/unready/revoked/inactive/unverified refusal before/after observations. Preserve owner-only inventory, readonly/no-BusinessEvent proofs and generic Playground mutation denial. The real browser journey must use no feature flag.
2. Remove the unused `os` import, `enabled()` helpers, snapshot flag refusal and its now-unraised `operations_cockpit_unavailable` entry from config/service_refusals.json; preserve the strict refusal-catalog parity gate. Replace the cockpit-only business-case `_member` coupling with a fresh tenant/user/member read, including existing persisted platform-admin business observation. Resolve Playground through `require_playground_run`, active/archived readiness and canonical account eligibility. Keep before/after authorization and owner-only inventory, without changing operational-case mutation guards. Business snapshots retain one authorization query per boundary.
3. Add only exact existing GET cockpit and case-inspection/status routes to the temporary Playground read allowlist in web/api.py. Keep ready-run/cookie/ownership checks ahead of the allowlist and leave POST/egress denied. No new endpoint, grant or browser poller. Direct cockpit URLs pass the selected tenant to the existing bootstrap reader, which validates shared cockpit access before adding only that owned quick/archived Playground company. Home keeps its practice-only list and pending-account admission is unchanged. Preserve the capability DTO/shell mount guard; update obsolete activation wording in four locales.
4. Clean obsolete flag setup in tests; update durable cockpit/Web/Playground contracts and coverage. Compose/installer/deployment templates contain no switch and require no configuration. Inherited old false values are inert in the new image. Run affected PostgreSQL regression, actual browser journey, lint/spec/docs gates, final access-boundary review and all final-head PR CI checks.

Rollback: revert this PR to restore the previous gate. No persisted setting or migration exists. Risks: broadened read availability must exactly preserve existing company privacy and Playground ownership; denied generic controls must stay denied. Missing data and incomplete rollout remain honest. Availability cannot start Agents or approve mutations.
