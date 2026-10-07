# Operations cockpit

## Upper business-case overview and shipping briefing (FR-079–080)

Two initially closed disclosures below the instrument legend provide a compact
whole-company case register and selected-day/site shipping briefing. Six process
families are visible, but only order fulfillment and announced returns have real
controllable-case counts. Unsupported families remain explicitly unavailable.
Registered cases, outstanding work and automation/human responsibility use the
canonical register aggregate; completed manual cases remain visible. Responsibility
does not certify a running Agent. Incomplete canonical rollout coverage remains
explicit next to the table. Numeric cells open an on-demand six-row read-only
preview with exact kind/ownership/outstanding filters and original object links.
The existing live register publishes its observation to the overview; no additional
periodic reader or business mutation is introduced.

The shipping briefing retains at most three original affected orders, a held cause,
responsibility and the first recorded case-linked action/status, or an explicit
missing-response statement. It does not attribute an actor, establish that the
action responds to that blocker, or claim an external outcome. Full evidence and
all affected-order inspection remain in the shared shipping analysis. Native
disclosures retain state through refresh and analysis changes; company changes
reset them. Badges, contained table/preview and theme-aware cards share the existing
instrument frame. German activity wording is “Zuletzt passiert”.

## Compact instrument inspection (FR-068–070)

Available primary counts and known risk groups open a compact read-only modal,
without selecting a chart, changing URL/history or scrolling the page. One local
group field selects All, In plan, At risk, Critical or Not assessed. Zero groups
have an explicit empty state; unknown counters remain unavailable. Escape/Close
restore trigger focus, and company changes close the modal. Finance retains its
existing unavailable explanation and workspace access.

The existing activity snapshot exposes up to eight exact members per category and
for the complete primary cohort, after full totals and worst-condition deduplication.
Rows name the original object, held condition and due/recorded date; stock shortfall
copies the canonical evaluator with the item's recorded unit. Source text stays
plain text. The preview explicitly states shown/total and links the exact Inspector
record plus the existing full specialist workspace. Two bounded, tenant-scoped
metadata reads label only retained document/item previews; no new endpoint, business
rule, schema, permission, persisted observation or browser reader is introduced.
Retained stale rows remain inspectable with an explicit warning.

This supersedes FR-057's non-interactive summary behavior for record inspection only;
analysis still has one independent selector.

## Shared analysis and compact operations workspace (FR-052–067)

FR-062–064 put shipping and all five flow areas in one contained analysis card below
the instruments. Shipping performance is the first/default option on a fresh page or
company change; existing area bookmarks are restored. FR-065–067 give the right
column one Operations workspace with a labelled selector: Responsibility
(default), Live events, or Registered Agents. Only the chosen view occupies space;
hidden components retain their manual review, paused log, Agent inspection and shared
reader state. Company change resets the workspace. Narrow layouts show analysis then
workspace. Main cards share padding/heading rhythm and natural height.

The analysis selector switches locally without scrolling, transferring focus or adding
history. Hidden views preserve their disclosures; shipping investigations stay in the
same left column and return with shipping. Opening a shipping investigation from the
deviations panel selects shipping. Shipping blockers are a counted, initially
collapsed disclosure within the
shipping view; all preview/action/source links remain available when opened, and the
disclosure survives chart switches. There is no detached full-width blocker card.
Its exact business day/site scope and source-backed plan/handovers/forecast remain distinct from the other areas' company-wide last-hour
scope. Both mail plots and the disclosed recording-rate plot remain available. The same
four readers, existing source/control state and confirmation semantics are reused.

Observation utilities use labelled keyboard-accessible icons; reviewed business
controls stay explicit text. Missing flow evidence does not hide shipping; missing
shipping input does not invent curves or disable selecting another flow area.

The shared flow reader partitions each displayed primary cohort before evidence limits.
Orders count once at their worst line finding; supplier work counts open lines. Existing
high/critical findings are red, other findings orange, assessed dated deliveries with
no evaluated finding green. Missing dates remain unclassified unless a stronger finding
is held. The canonical due-soon class is included because it supersedes unreserved work.
Stock covers only oversold items. Returns without a held finding remain unclassified,
as a missing learned threshold cannot establish timeliness. Message urgency counters
remain null without recorded response deadlines; the known unanswered count remains
visible. Finance stays unavailable. Nothing is persisted. The partition itself adds no query; compact inspection labels use the bounded metadata reads described above.

The single case register initially reads human-owned work for a visible manual preview;
choosing an automatic case switches its existing filter. Ownership counts remain full
and takeover/handback still require the existing exact reviewed confirmation.

## Instrument console refinement (FR-047–051)

The owner-approved console presents the five canonical areas as compact instruments
with complete primary counts and labelled three-color conditions. The FR-052–056
preview parity refinement replaces decorative strips with exact complete-cohort
risk partitions and proportional meters, including explicit unclassified coverage. Finance is an explicitly
unavailable observation with a normal workspace link. FR-057–058 make the operational
instruments read-only and give detailed analysis one labelled local area selector.
Switching preserves viewport/focus and replaces the bookmarked area without growing
browser history. Live selection is retained, inactive evidence panels stay mounted,
and company changes reset context.

Local correspondence adds incoming/first-recorded-reply counters to the existing
five-minute operating buckets, derived from the already scoped full mail cohort with
no additional query. Intervals are half-open except the last includes the observation
instant, matching existing inclusive-hour totals. Unknown mailbox/company coverage is
nullable; providers do not acquire an inferred reply state. Separate intake/reply and
unanswered-backlog diagrams retain canonical units and evidence. Other plots retain
physical record semantics and stock stays current-only. No financial observation,
business status, timer, mandate or business mutation is introduced.

Verified locally on 2026-10-07: 53 affected PostgreSQL tests, 478 frontend contracts,
full cockpit and shell browser checks, four-language/theme responsive proofs and
controlled eight-hour observation passed. API/web were activated on port 8080 and
checked against actual changing company data; see [validation](../../specs/378-enterprise-operations-cockpit/quickstart.md).
The existing background rollout remains separate from instrument availability.

Authority: [spec 378](../../specs/378-enterprise-operations-cockpit/spec.md).
Design and protected reference: [migration map](../../specs/378-enterprise-operations-cockpit/migration-map.md).

## Implementation status

The Control Tower navigation destination is always visible in the authorized company shell; operational availability remains default-off and gated by the existing company capability. The Operations Cockpit integrates shipping by end of day, rolling business activity, a named Agent/access inventory, evidenced deviations and the supported operational case register. Home remains the default entry. The Inspector and specialist workspaces remain available through exact references and a validated return context. The hosted enterprise reference is unchanged.

Shared domain/service/tool/HTTP reads, reviewed planning inputs, takeover/handback receipts and read-only consistent snapshots have executable functional proofs. The canonical shipping/readiness/revision/policy/case-control regression passed 91 tests, two narrow-input representation proofs pass, and the final shipping/source-priority/adapter run passed 44 tests. The full frontend gate passes 478 tests and 2,964 used strings in four languages. These overlapping focused runs are not a full backend-suite count. Fixture-backed browser proofs cover populated/stale/missing observations, exact controls and a controlled eight-hour live session. These do not establish production throughput or a real-time pilot soak. The declared enterprise workload, final complete regression gates and final diff review remain pending; see the [quickstart](../../specs/378-enterprise-operations-cockpit/quickstart.md).

## Accepted planning evidence

`shipping_plan_propose`, `shipping_plan_revise_propose` and `shipping_plan_withdraw_propose` stage the canonical `shipping_plan_state` application proposal. The CLI `shipping-plan-propose` accepts an exact JSON argument file. Common proposal review/confirmation routes retain the original payload and require an observed active company owner. A manual MCP credential cannot approve its own statement; this feature grants no execution mandate.

Closed inputs declare the company business day/calendar, exact dispatch location/site zone, full canonical commitment quantities, shipping deadlines, optional planned handover times and confirmed/requested completion-slot capacity. A confirmation Source reference and its current original version are bound to the review. Accepted newer order-source intake is resolved while original evidence remains linked; exact plan/capacity confirmation versions must still be current. Newer unresolved sources, changed quantity statements/calendar/prior versions and competing current scope refuse acceptance. A commitment cannot belong to two current plan streams. Withdrawal appends an empty header and preserves history.

Migration `0146_shipping_plan_inputs` adds only `shipping_plan_statement`, `shipping_dispatch_requirement` and `shipping_capacity_window`, with composite company references and quantity/time/confirmation constraints. Sources remain immutable and versioned; the same approved proposal returns its existing receipt on replay. No Document operational status, stock movement, reservation, case adoption or provider effect is produced. Upgrade/downgrade proof uses temporary databases. Populated planning evidence prevents a destructive downgrade; no startup path runs migrations.

## Calculation contract

The pure [shipping domain](../../packages/reality-core/src/reality/domain/shipping_performance.py) distinguishes source-stated timed Soll, fully covered physical contents with attributed handover times, and deterministic estimated completion slots. Partial lines or split-site work count as a company order completion only after all required units complete. Repeated reports do not multiply contents; missing/conflicting/future handover times remain explicit gaps. A label alone is not a handover.

Only confirmed non-overlapping capacity contributes forecast slots. The original interval determines the pace; an earlier collection cutoff does not speed it up. Requested extra collection adds no baseline capacity. A boundary completion shared by adjacent intervals consumes the earlier interval once. Company counts deduplicate orders across sites. These are read-time observations, never stored forecasts or guarantees. The complete definitions and independent acceptance oracle are in the [shipping contract](../../specs/378-enterprise-operations-cockpit/contracts/shipping.md).

## Shared read and product contract

The shipping reader keeps independently valid Soll/cohort observations visible when physical handover timing is unresolved. It excludes post-day completion slots from end-of-day totals, shows no future confirmed point and does not reconstruct historical forecasts for a pinned past day. Supporting queries use cumulative instants or half-open intervals, retain individual risk deadlines and compute totals before bounded paging. Production reads use fresh read-only repeatable-read snapshots; caller-owned connections retain source/version drift guards. No read commits pending changes or creates business evidence.

The executable reads are `operations_cockpit`, `shipping_performance`, `shipping_supporting_orders`, `operations_cockpit_activity`, `operations_cockpit_agents` and `operational_case_register`. HTTP, CLI and MCP call shared services and enforce current company membership and the default-off capability. Agent/access inventory additionally requires current owner authority. Manual credentials and OAuth grants are separate qualified identities; exact observed use is disclosed only where attribution exists. Permission and last use do not establish current connection, execution or successful external outcomes. Missing runtime evidence stays unknown.

Shipping and case totals remain complete before display pagination. The complete basis retains all planning-source identities and prioritizes daily-plan/collection confirmation metadata across sites before the bounded order-source preview. Case search matches retained business references for display while opaque IDs remain identity. Supported fulfillment and announced-return cases under spec 377 default coordination support whole-case takeover. The register does not require legacy owner adoption. It exposes canonical platform rollout readiness separately, so incomplete reconciliation is visible without hiding existing cases or inventing complete coverage. The shared existing control service freezes the reviewed revision, exact reason and request key, preserves safe retry and requires a fresh handback review. A related case is independent and a started action is not cancelled by takeover. The human-owned register includes completed work and its exact recorded control attribution.

Visible-tab observation follows a five-second cadence with non-overlapping reads, bounded recent-event buffers, timeout/backoff, hidden-tab suspension and stale-state disclosure. Pausing the activity presentation is distinct from stopping a case. Inspection and confirmation state remain stable while sibling live reads arrive. Today follows the company's calendar; an opened supporting cohort retains its resolved day across midnight. A pinned day remains fixed. Company changes clear previous observations and exact reviews.

Open customer-delivery work outside the selected day's confirmed plan is discoverable through the company-wide unplanned view. It receives no inferred dispatch site or deadline. The protected reference inventory retains deferred commercial KPIs and process families explicitly in the [migration map](../../specs/378-enterprise-operations-cockpit/migration-map.md).

No real-company pilot, startup migration, history adoption, provider effect or default-route replacement is enabled. Final performance/regression evidence and a separate real-time soak remain prerequisites for pilot enablement. Interfaces are described in [contracts](../../specs/378-enterprise-operations-cockpit/contracts/interfaces.md).

The independently refreshed responsibility register and owner access roster expose their own successful read times; a failed refresh preserves and labels the previous observation. Historical responsibility changes include full dates and business-zone offsets. Live/diagnostic observations preserve the user's display timezone and show its offset; shipping days and collection deadlines retain explicit business/site zones. The register timestamp is transient snapshot metadata, including an empty register or incomplete platform rollout. Exact manual access attribution is produced by the existing Engine Room reader as a redacted DTO; telemetry never determines shipping, responsibility or execution.


Clean snapshots project original planning header/source/action metadata and the
exact reviewed proposal basis without loading unused full payload/preview copies.
Original sources remain unchanged and inspectable. Original order/commitment rows
are read once per cohort and passed within this call to canonical terms, readiness
and delivery-policy readers, with company/identity guards and canonical fallback
for incomplete policy input. Ordinary sessions keep their ORM behavior. Complete
stored-result/fingerprint parity and the 147 affected regressions pass. Pinned-day
captions refer to the selected day; Today retains its current-day caption. These
read/presentation refinements do not certify enterprise throughput or a pilot soak.

A bounded register page in a clean read-only snapshot holds its original
company-scoped case/work/document/action/control inputs once for the canonical
explanation. Scalar and batched reads share the source-gap rule. Latest action
previews and complete executing totals remain independent; related returns and
completed human work retain their existing meaning. No input/result is retained
after assembly. Ordinary and caller-owned reads keep their original behavior.
Full DTO/scope/control/source parity and 53 affected regressions pass; the actual
browser still proves a committed change, reviewed takeover and its retained
reason. Enterprise throughput and the separate real-time soak are separate gates.

Overview detail allocation happens after the complete shipping calculation and
full fingerprint. Only exact already-evaluated risk/coverage-gap rows need detail
DTOs there; every matching deviation remains counted before the fifty-row preview.
Ordinary and supporting readers retain the full paged cohort. Stored parity and
a populated 63-order/61-deviation proof pass, alongside 183 affected regressions
and the final actual takeover/browser proof. Empty optional case-input cohorts
skip SQL only when absence is already established; any linked action keeps the
independent complete executing-count query. The 53 affected case/control proofs
remain green. Enterprise timing and pilot soak remain distinct acceptance gates.

Original source/current-version/intake metadata may be loaded for all accepted
site statement references together inside a clean snapshot. Per-statement exact
reference/current-confirmation checks remain in the canonical source validator;
missing or superseded evidence cannot cross-contaminate scopes. Inputs are
call-local and session/company/cohort bound. Normal mutation/review reads remain
fresh. Result/error/scope parity, all 184 affected regressions and the final
actual browser pass. The separate enterprise and pre-pilot gates remain explicit.

The declared isolated backend/JSON enterprise workload now passes with the full
10,000 active / 100,000 historical / 500,000-observation cohort and ten readers:
opening/site p95 2.793 s, 480-request continuous-read p95 2.823 s, all twelve
five-second cycles and committed-order visibility pass. Hardware/distribution
and all prior corrections/red runs are recorded in the validation report.
This is a service/JSON boundary measurement; large enterprise DOM timing and
the separate eight-hour real-time soak remain pre-pilot evidence gaps.

## Owner-requested compact observation refinement

Spec 378 FR-025–027 bounds default collection and deviation previews while retaining exact totals and expandable evidence. Shipping inspection opens immediately after its chart with focus/return-focus rather than below unrelated sections. Case controls use responsibility-oriented labels and replacement-page navigation; inline inspection remains adjacent to the originating case. Business rules, live reads, supported case families and reviewed takeover/handback are unchanged. Verification is recorded in the feature quickstart.

## Company-wide operating flows (FR-028–033)

The additive `flows` field in the existing authorized cockpit read supplies five compact cards: customer orders, local reply queues, expected supplier promise lines/receipt records, canonical oversold-item exceptions and physical returns/disposition. They are independent of shipping day/site filters, use the same read-only snapshot/live lifecycle and show complete totals before four-record previews. Existing CLI/MCP/HTTP adapters share the reader. Reply and acknowledgement are distinct; only exact same-company/source-system/message reply lineage reduces the local unanswered curve. Provider reply coverage remains unavailable. Open supplier/customer work uses canonical commitment terms; received records can be partial and quantities across items are not summed. Returns retain canonical announcement/disposition semantics, without implying refund or whole-case completion.

Five-minute movement buckets cover exactly the rolling hour and use effective occurrence time; first-recorded orders use recording time; local backlog uses immutable first-reply/arrival times. Pre-company periods are unknown. Stock risk is current canonical exception evidence, with no invented historical curve. Traffic lights disclose evaluated exceptions; pending work does not claim active execution and unknown/stale observations cannot be green. Original shipping and deviation evidence remains intact. New local timing and functional evidence are recorded in spec 378 quickstart; the previous enterprise workload does not certify this expanded query.

## Presentation consistency (FR-034–036)

One page gap owns section separation; standalone and card section headings share typography. Operating flow cards use content-sized shared tracks for titles/status, metric rows, chart slots, contextual notes, evidence and footer links. Fewer metrics reserve comparison space only while cards share a row; they do not add empty business values. Stock keeps its current-only evidence disclosure rather than a simulated chart. Expanded evidence grows naturally. Content-container breakpoints support docked side areas independently of the window width, releasing cross-card spacing for a single column. Existing activity/case choices share accessible grouped selection styles; navigation footers share subdued spacing, while actual inspection and confirmed business-control actions retain their distinct semantics. No data, timer, source, action or authorization change.


## Central recorded-condition overview

FR-037–038 introduced the five-area overview before shipping, using the identical
canonical signals and primary metrics as the operating cards. FR-045 groups visual
conditions into red/orange/green, while FR-053–054 show exact disjoint risk counts,
proportional segments and explicit unknown coverage. FR-057–058 supersede the former
same-page instrument links: monitoring is read-only and analysis has one local selector.
Scope stays company-wide, independently of shipping day/site. No aggregate health
score, agent-quality judgement, threshold, new read/timer, mutation or schema is added.


## Permanent Control Tower discovery

Spec 378 FR-039–040 distinguish discovery from authorized availability. Root/Home/specialist/company-change navigation always includes Control Tower, while operational content mounts only after an enabled capability response for the current company. Pending availability uses a loading state; disabled, failed or unsuitable-company availability explains the current context and points to the existing company menu and Inbox return. Existing membership, business-company and default-off backend guards remain authoritative. Product titles/return links share the Control Tower name across languages; `/app/cockpit`, tools and structured origins retain their existing identities. Home/default-company and user preferences are unchanged.


## Shared workspace surface (FR-041)

The Control Tower canvas uses the same `--surface` ground as company workspaces and the shell header in both themes. Card grouping and shared neutral selection/explanation surfaces are preserved. No global palette, stored preference, observation, data, polling or business-control semantics change.


## Compact upper case takeover entry (FR-042–044)

The single case register appears after company status and before shipping as a compact, bounded ownership entry. Its automatic/human counts retain their existing complete-register meanings; selecting the automatic count opens the existing outstanding-work view, while the human count opens the complete human-owned view, including completed work. Search, case filters, pagination and reviewed inspection are revealed adjacent to this entry on demand; bookmarked case context also opens them. Clear copy explains automatic supported work, confirmed whole-case takeover, stopped new automatic starts and the distinction from work completion. The existing detailed review still discloses already-started actions and independent related cases. The disclosure retains mounted controls/review/reason/request state and existing live reads, and never performs a mutation itself. No additional request, poller, service, case policy or mandate.


Company-status tiles and operating-flow status dots use a classic three-color palette. Critical evidence is red; a clear evaluated scope is green; recorded attention, ordinary pending work and incomplete/stale/missing evidence are orange. The canonical five service signals retain their separate textual conditions and evidence links. Orange does not introduce an exception, service-level target or agent-quality score, and missing evidence never becomes green. The localized legend explains the shared orange category. This presentation-only refinement adds no reads, controls or business rules (spec 378 FR-045).

### Stable area selection (spec 378 FR-057–058)

Instruments are monitoring summaries. Detailed analysis owns the single labelled area
selector, which switches charts in place without a scroll/focus transfer or new history
entry. Bookmarked area, live/disclosure state and company reset are retained. Shipping,
Agent observations and whole-case responsibility keep their existing read/control scope.

### Missing daily shipping plan

Spec 378 FR-071–072 separates observed physical shipping from daily planning. Orders with actual shipment bookings and source-backed confirmed package handovers remain visible for the selected company day/site even without a plan. These counts retain their distinct units; a package or partial booking never implies a completed plan order. Plan comparison/forecast and affected-order coverage remain unknown without the required accepted inputs. The scenario-only trusted local daily fixture is documented in Company Simulator LIVE.md; it does not grant agent, worker or production planning approval.

The two primary console cards use one selected-topic heading (spec 378 FR-073):
Flow analysis and Operations workspace are category eyebrows; the current shipping/
flow or responsibility/log/Agent topic is the sole primary h2. Embedded views retain
context, accessible region names, icon actions and state without repeated headings.

Available instrument tiles open their same compact all-work inspection from the
whole primary hit area (spec 378 FR-074). The native primary trigger supports
Enter/Space and full-tile focus feedback; sibling risk controls retain their exact
filtered group. Unavailable counts do not acquire an inspection action, and Finance
retains its workspace link. No extra request, navigation or business action.

Console content grouping (spec 378 FR-075) separates current snapshot metrics from
explicit last-hour activity metrics without changing their units or meaning. Each
plot contains its own title, series/range legend and relevant scope/change notes.
Shipping comparison, physical actual activity, responsibility actions, stopped
cases and observed Agent/event lists follow the shared theme-aware section rhythm.
The selected topic, read lifecycle, exact record inspection and authority remain
unchanged; no extra business reader or navigation is added.

Viewer observation timestamps (spec 378 FR-019) use personal timezone/locale and
show their actual date/UTC offset in the global status, case read/control history
and supporting-order read. Shipping reference clocks, business-day evaluation
and stated site deadlines retain their own explicit zones. This is display only;
stored UTC instants and shipment calculations remain unchanged.

Shared analysis presentation (spec 378 FR-076) uses the same labelled metric-group
and titled bounded figure wrappers for shipping and company flows. Plan comparison
precedes the separate recorded physical-activity group; package handovers retain
their own unit and do not become completed plan orders. Legends/assumptions live
below their own curves. Site tables start collapsed; their exact dated cutoffs and
all existing inspection/live controls remain available.

The instrument overview is one themed section with aligned title/value/description,
compact proportional meter, labelled right-aligned risk-count rows and condition
slots. Its four-key legend, scope and classification caveat share a separated
centered footer. Known zero work has an empty neutral meter; unavailable or stale
evidence remains hatched. Tile/category inspection and Finance navigation retain
their existing exact record scope and keyboard behavior (spec 378 FR-078).


### Compact shipping deviation rows (FR-081)

Both the upper briefing and detailed shipping disclosure use one compact semantic
table: order, recorded cause, responsibility and first recorded case action/status.
Their original three/four-order preview limits, complete affected total, unknown/
empty messages, original links and causal/outcome caveats remain unchanged. In the
detailed table, all held causes and case-linked actions expand beneath their exact
order across the table width; additional previews and full supporting-order
inspection retain their existing scope. Tables scroll horizontally within their
own labelled keyboard-focusable region on narrow screens. No business read, rule,
DTO, timer, control or confirmation changes.


### Stacked monitoring and upper case controls (FR-082)

The right column now displays Recorded business activity and Registered Agents simultaneously as separate cards (German: Zuletzt passiert / Angemeldete Agenten), with no right-view selector or duplicate responsibility panel. Whole-case control lives in the upper Business cases in operation disclosure, under Cases & takeover. The same single mounted OperationalCaseRegister reader supplies upper totals; the embedded control entry omits duplicate ownership counts. Supported kinds, exact takeover/handback reviews, evidence links, stale/denied states and owner restrictions are unchanged. Bookmarked case IDs open both containing disclosures; closing them or switching analysis retains a prepared review. Company changes reset local context. Access authorization/last use remains distinct from Agent runtime state.

Verified by the full operations-cockpit-browser.mjs locale/theme/viewport matrix, 478 frontend contracts, four 3056-key audits, production build/image, format/spec checks and actual local company proof on port 8080. Source, service, API, scheduler and execution authority are unchanged. See spec 378 review/quickstart for evidence; earlier release gates remain open.
