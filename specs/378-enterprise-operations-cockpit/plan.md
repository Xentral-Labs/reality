# Implementation Plan: Enterprise operations cockpit

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

New server capability `REALITY_OPERATIONS_COCKPIT_ENABLED`, default off, gates both nav and direct routes. A disabled URL returns to a permitted existing page. Capability changes presentation/read access only, not mandates or ownership.

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
