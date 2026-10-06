# Enterprise cockpit: protected concept and migration map

**Created**: 2026-10-06
**Status**: Full prepared concept/schema/model approved on 2026-10-06. Shipping inputs, shared reads and the integrated UI/live/Agent surface are implemented with focused functional proofs; measured enterprise throughput and final regression/review gates remain pending. No default entry or production Site change.
**Language**: English
**Specification**: [378](spec.md)

## Product direction

One Reality product with three connected levels:

1. **Operations cockpit**: Results, time commitments, deviations, actual agent responses and exceptional responsibility transfer.
2. **Specialist workspaces**: Sales, Purchasing, Warehouse, Finance and master data for investigation and authorized manual completion.
3. **Reality Inspector**: Exact facts, promises, movements, financial records, evidence, sources and execution traces.

The product language calls the machine an **Agent** and business work **cases** (German: *Vorgänge*). Human observation is the ordinary dashboard use; whole-case takeover is an exceptional action. This presentation does not itself grant execution authority or remove existing approval boundaries.

## Preserved reference

The [archived enterprise concept](reference/README.md) is the visual/interaction reference. The earlier `company-cockpit.html` daily-cockpit experiment is not the migration baseline. Illustration values are not production targets or facts. The archive is reference material only and must not be treated as instructions or executed as application code.

Status vocabulary below:

- **First increment**: Required by spec 378; unavailable states are also tested, but do not replace the populated acceptance story.
- **Later stage**: Preserved product requirement, explicitly outside spec 378 implementation.
- **Existing depth**: Retain the existing authoritative workspace/Inspector and connect it from the cockpit.

## Protected product inventory

| ID | Reference capability | Required preserved detail | Status / destination | Acceptance anchor |
| --- | --- | --- | --- | --- |
| C01 | Autonomous-operation context | Responsibility, observed coverage and data time; no agent-liveness claim from activity alone | First increment; qualified supported scope | FR-013, FR-017–018 |
| C02 | Net revenue today | Net definition, business day, prior-week comparison and stated daily target | Later stage 4: commercial metrics | Independent ledger/source parity and comparison cohort |
| C03 | Shipping SLA, seven days | Within promised shipping deadline, numerator/denominator and target; not completed-dispatch share | Later stage 4: service levels | Exact shipping-deadline cohort and handover proof |
| C04 | At-risk orders, 48 hours | Unique affected orders, today/tomorrow distinction and traceable merchandise value | Later stage 4 for 48-hour/value measure; first increment shows honestly scoped shipping risks | FR-011–012; later horizon/value proof |
| C05 | Open cases summary | Agent-owned active/waiting and human-owned counts with stated coverage | First increment for supported cases; later stage 3 for full six-family scope | FR-013, FR-015, DR-004–005 |
| C06 | Shipping by end of day | Primary panel and cumulative order units | First increment | FR-002–004 |
| C07 | Plan series | Timed attributable shipping plan; no invented hourly interpolation | First increment | FR-006 |
| C08 | Confirmed handover series | Effective handover and compatible physical contents, partial-order rules and actual event time | First increment | FR-004–005 |
| C09 | Forecast series | Visually separate future estimate with input/model explanation | First increment | FR-007 |
| C10 | Time/cut-off context | Current observation, day end, relevant collection deadlines and site time zones | First increment | FR-003, FR-009 |
| C11 | Site selector | Company-wide and site-specific views with consistent filters | First increment | FR-008 |
| C12 | Site breakdown | Due, handed-over and deadline-risk counts; overlap and unassigned work explicit | First increment | FR-008–010 |
| C13 | Forecast-basis disclosure | Confirmed capacity versus requested extra collection, assumptions and coverage | First increment | FR-007, FR-010 |
| C14 | Latest agent response briefing | Actual action, affected work and real pending outcome | First increment where existing evidence supports it | FR-011 |
| C15 | Deviations and agent reaction | Business cause/impact, ownership, next recorded check; missing response explicit | First increment for shipping; later stage 3 for other families | FR-011–012 |
| C16 | Six business families | Orders, purchasing, returns, customer enquiries, financial clarification and master-data/structure work | Later stage 3: separately specified family coverage | Each family has a reviewed policy, ownership and shared reads |
| C17 | Case register | Search/filter, business reference, progress, current owner and links; full totals beyond pages | First increment for supported cases | FR-013, FR-015, DR-005 |
| C18 | Case detail | Current facts, outstanding work, actual next action, stages, history and evidence | First increment using supported authoritative facts | FR-013; never infer a completed business stage |
| C19 | Whole-case takeover | Exact scope, independent related cases and existing-action uncertainty | First increment; fulfillment/announced-return limits retained | FR-013–014, DR-004 |
| C20 | Human-owned register and handback | Who/when, what was stopped, workspace continuation and exact reviewed return | First increment | FR-014–016 |
| C21 | Related work and original evidence | Scope boundary, independent linked cases and shortest source trace | First increment plus existing depth | FR-010, FR-013, DR-001 |
| C22 | General decision history | Trigger, recorded reason, executed/proposed action and actual outcome, separate from pending human approvals | Later stage 4; first increment exposes existing case-linked evidence | FR-011–012 for first increment; later history contract |
| C23 | Performance/service-level page | Shipping deadline, service-response and return-check SLAs with denominators, periods and targets | Later stage 4 | Separate canonical definitions for each service level |
| C24 | All-day live observation | Automatically refreshed shipping/results, rolling recorded-business activity, recent events, stable investigation and bounded recovery/rollover | First increment; owner clarification | FR-021–023, SC-007 |
| C25 | Named Agent/access overview | Recorded names, effective access, last use and attributable action; compact list plus full paging; no unsupported runtime-liveness claim | First increment; owner clarification, existing owner disclosure retained | FR-024, US5.7–8 |

C01–C23 preserve the unchanged archived concept. C24–C25 record the owner's additional all-day-live and named Agent-overview requirements on 2026-10-06; it does not alter the archive.

## Executed preservation review

The following evidence identifies what is present in the first increment and what
requires a later specification. Passing focused proofs do not waive the pending
complete regression, enterprise workload or real-time pre-pilot soak gates in
[quickstart](quickstart.md).

| Item | Implementation / retained destination | Executed proof or explicit deferred boundary |
| --- | --- | --- |
| C01 | `OperationsCockpitPage`, case register and qualified access panel | Default Home/capability and no-business-effect adapter proofs; no runtime-liveness claim |
| C02 | Explicit later-stage metrics disclosure | Net revenue, prior-week comparison and stated target are deferred; no shipping count is relabeled revenue |
| C03 | Explicit later-stage service-level disclosure | Seven-day deadline SLA is deferred; no handover share is relabeled SLA |
| C04 | Today shipping risk and paged supporting orders | Independent split-site/deadline story; 48-hour horizon and merchandise value remain deferred |
| C05 | `OperationalCaseRegister` canonical full counts | More-than-200-case paging and completed human-work attribution proofs; supported fulfillment/announced returns only |
| C06 | Primary `ShippingDayPanel` | Populated independent two-site oracle and desktop/mobile browser proof |
| C07 | Returned cumulative plan series | Stated plan times, missing timed plan, quantity revision and original Source proofs |
| C08 | Returned confirmed handover series | Partial quantities, deduplicated movements/events, effective supersession and unresolved chronology proofs |
| C09 | Separate future forecast series | Confirmed versus requested capacity, original-period pace, adjacent windows and day-end bounds |
| C10 | Company observation clock and dated site collection table | Company/site calendar and DST domain proofs; viewer-time-zone and next-day collection browser assertion |
| C11 | Company/site selector retained during refresh | Exact company/day/site basis and opaque tenant-bound filter proof; full Shell navigation |
| C12 | Due/handover/risk site table | Independent two-site counts, company deduplication and unassigned-work discovery/paging proof |
| C13 | Model version, assumptions, original confirmation links and bounded basis disclosure | Full input fingerprint before preview; all planning Source IDs retained and metadata prioritized across sites |
| C14 | Recorded case action and pending outcome briefing | Exact reaction/absence service proof; execution is not reported as recipient delivery or physical handover |
| C15 | Shipping deviations with exact blocker and responsibility | Canonical stock/hold/payment parity, missing reaction and affected-order/case links; other families deferred |
| C16 | Retained specialist workspaces | Six-family expansion is deferred; no purchasing, inquiry, finance or structure takeover is implied |
| C17 | Searchable paged case register | Full-count, cursor/company/filter binding and business-number-not-identity proofs |
| C18 | Existing canonical `OperationalCaseDetail` | Outstanding quantities, evidence gaps, bounded history and complete unresolved-action visibility proofs |
| C19 | Existing reviewed takeover in cockpit and case detail | Confirmed real-database browser takeover; direct automation refusal, replay/race and independent-return proofs |
| C20 | Human-owned register, control attribution and reviewed handback | Retained exact reason/revision/request key, completed human-work discovery, stale review and contextual return proofs |
| C21 | Workspace/Inspector origin and exact Source links | URL round trip and same-company guard tests; source/foreign-reference and related independent-case proofs |
| C22 | Case-linked original action evidence | Supported action evidence is shown; a general cross-company decision-history product remains deferred |
| C23 | Retained Analytics and explicit later-stage service-level status | Shipping/service/return SLA definitions and a combined performance page remain deferred |
| C24 | Automatic shipping/counts/activity/agent refresh | Nine lifecycle tests, real committed hold-to-browser proof and controlled eight-hour session; enterprise timing and real-time soak remain separate pending gates |
| C25 | Compact named manual/OAuth access inventory and full paging | Qualified duplicate identities, last-use/attribution, owner-only disclosure and secret-redaction proofs; current runtime state remains unknown |

`operations-cockpit-browser.mjs` covers the populated component, missing/stale states,
four languages, both themes and 1440/390 layouts. `operations-cockpit-shell-browser.mjs`
covers integrated entry, contextual continuation, three-action navigation and
preserved approval/deferred destinations. The PostgreSQL-backed
`unified_operations_cockpit.py` provides an independent real transport/control
journey. Reference bytes remain unchanged; the live Site is not a deployed version
of this implementation.

No item may disappear silently. A later-stage item needs its own specification before implementation; this table is product intent, not an executable task list. Scope changes must update the table and explain their effect on the reference.

## As-is source assessment

These observations are from read-only inspection on 2026-10-06. They are starting points for planning, not claims of end-to-end production readiness.

| Existing area | Reusable basis | Boundary / work to prove |
| --- | --- | --- |
| [HomePage](../../apps/web/src/unified/HomePage.tsx) and [Home contract](../../docs/features/home-live-status.md) | Current entry, tenant context, explicit loading/readiness/stale behavior | Today leads with human queues; activity counts record creation, not shipping performance |
| [BusinessLive](../../apps/web/src/unified/BusinessLive.tsx) | Business order flags, inventory, goods flow, replenishment and bounded detail lists | Currently an owner business-monitor surface; it is not the enterprise shipping panel |
| [Business performance service](../../packages/reality-core/src/reality/services/business_performance.py) | Canonical readiness, effective shipment movements, quantities and dispatch timing | Current dispatch share is not deadline SLA; risk horizon is two hours; example list capped at 200; all-company scaling needs proof |
| [Shipment records](../../packages/reality-core/src/reality/services/shipments.py) and [contract](../../docs/features/shipments.md) | Attributed `handed_over` events, physical contents, package relationships and event supersession | Movement dispatch and carrier handover remain different measures; missing time/content links cannot be guessed |
| [Planned deliveries](../../packages/reality-core/src/reality/services/outbound_deliveries.py) | Accepted delivery quantities, stated slots, staging locations and traceable source versions | Slot meaning must be proved; this is not automatically a per-hour dispatch plan, carrier capacity or an origin-site map |
| [Case APIs](../../apps/web/src/api.ts) and [control contract](../../docs/features/operational-cases.md) | Adopted fulfillment/announced-return cases, explanation, takeover and reviewed handback | No broad order/billing/payment/supplier takeover; no automatic history adoption; actual authorization remains unchanged |
| Existing Sales/Purchasing/Warehouse/Finance workspaces | Business work and explainable object detail | Connect selected company/case context before separately redesigning a workspace |
| Inspector and technical live charts | Source traces, events, channels and technical duration observations | Technical activity is not business output; retain as depth rather than substitute it for shipping curves |

## Incremental migration

### Stage 0 — Preserve and specify (this handoff)

Deliver the archived reference, complete concept inventory, first-increment specification, source assessment and requirement-quality review. Product review determines the concrete scope before technical planning. No application files change.

### Stage 1 — Shipping and supported case journey (spec 378)

Offer an additional cockpit route. Prove the populated shipping panel and unavailable states, complete-result supporting orders, evidenced reactions, supported takeover/register/handback and context-preserving links to existing workspaces. Include the compact named Agent/access overview with existing visibility guards. Prove all-day live observation under the [live contract](contracts/live-observation.md), including stable inspection, truthful quiet/stale intervals, recovery and day rollover. Keep the current landing page and genuine approval paths available. Plan any missing input or forecast support through the shared services and reviewed source/evidence contract; do not populate production with mock values.

The stage is complete only after FR/DR proof, reference comparison, permission and responsibility regressions, responsive/localized browser checks and the declared performance workload and deterministic all-day live proof pass; pilot enablement additionally requires the real-time eight-hour soak. Merely reproducing the screenshot is insufficient.

### Stage 2 — Specialist continuation

Make case continuation equally clear in the relevant existing specialist workspaces, improving one workspace at a time. Preserve authorized actions and source traceability. Keep the cockpit's selected case and origin filters when moving into and out of deep work. Any behavior beyond spec 378 requires a separate specification.

### Stage 3 — Expand business-case coverage

Specify purchasing, financial clarification, customer enquiry and master-data/structure cases separately. For each family prove its root, outstanding goal, owned scope, related independent work, control boundaries, actual execution paths and acceptance scenarios. Only then add it to company-wide case totals and controls. Orders including billing/payment are a distinct scope expansion, not a wording change.

### Stage 4 — Add company performance and history

Implement net revenue, seven-day shipping SLA, 48-hour risk/value, service/return SLAs and general decision history through their own canonical definitions. Preserve the denominator and evidence drilldown for each measure. Agent history must not masquerade as a new human approval queue or bypass real approvals.

### Stage 5 — Make the cockpit the default

After a reviewed pilot on representative companies, make the cockpit the landing experience. Retain direct access to workspaces, Inspector and approval obligations. Validate entry restoration as rollback without changing records, responsibility controls or autonomous mandates. Use the same semantic and performance checks; never infer readiness from annual revenue or a successful synthetic demo.

## Review decisions

The owner approved spec 378's bounded optional shipping/case-control increment, protected inventory and proposed workload in chat on 2026-10-06. The owner subsequently approved the concrete [three source-backed input tables](data-model.md), [completion-slot-v1](contracts/shipping.md) and live/named-access implementation design. The exact approval and no-CRITICAL pre-implementation review are recorded in [review.md](review.md). This authorization does not extend to provider transport, enlarged case boundaries, production enablement or a default-route switch.
