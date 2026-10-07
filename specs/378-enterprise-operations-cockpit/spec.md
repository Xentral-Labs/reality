# Feature Specification: Enterprise operations cockpit — shipping and case control

## Owner-requested compact instrument inspection (2026-10-07)

This explicitly supersedes FR-057's non-interactive summaries only for read-only
record inspection. Instruments still never select charts, change hashes or scroll.

- **FR-068**: Each available primary instrument count and each known risk count,
  including zero and unclassified, MUST open one compact accessible inspection
  dialog in place. It shows the selected area/group, exact full-cohort total,
  observation timestamp and up to eight actual member rows with record label,
  recorded condition and relevant date. Empty, unavailable and stale observations
  remain explicit. Unknown risk counts never imply zero. Finance retains its
  unavailable explanation and existing workspace link.
- **FR-069**: Rows MUST come from the same shared observation and worst-condition
  identity partition as the displayed count, before preview limits. Orders count
  once across lines; supply counts promise lines; stock covers uncovered items;
  returns cover pending physical positions; local unanswered messages stay
  unclassified. Include shortest true Inspector links, item shortfall only from
  the existing evaluator, an explicit shown/total limit and workspace access.
  No new business rule, schema, authority, polling loop or inferred urgency.
- **FR-070**: Opening/closing or changing the dialog group MUST preserve analysis,
  URL/history, viewport, manual drafts and live readers. Escape and Close restore
  trigger focus. Dialog is bounded and scrolls internally on phones, supports
  keyboard and four languages/light and dark themes; company changes close it.

Acceptance: inspect both uncovered items; inspect a preview of 504 critical orders
without navigating; switch to an empty in-plan group; inspect unclassified mail;
Escape restores the selected trigger and analysis stays unchanged. Backend proofs
cover complete totals beyond eight, deduplication, actual pending membership,
worst severity, tenant scope and optimized/ordinary observation parity.

## Owner-requested compact operations workspace (2026-10-07)

The owner requests a coherent, quieter arrangement instead of three permanently
expanded right-column boxes and detached shipping blockers. This supersedes the
continuously visible right-column stack in FR-064, preserving its control priority.

- **FR-065**: One adjacent Operations workspace card MUST present exactly one of
  Responsibility (default), Live events, or Registered Agents, using one labelled
  native selector. Switching is local with stable header/focus/history, all existing
  content and reviewed business controls accessible. Company changes reset to
  Responsibility. Hidden panels stay mounted and keep their exact manual draft,
  inspection, paused log, selected Agent and live-reader lifecycle.
- **FR-066**: Shipping blockers MUST be a collapsed, counted disclosure inside the
  shipping analysis, available only with shipping. Opening it retains every original
  source/action link, bounded preview, expansion and full supporting investigation.
  Switching away/back retains its open state. No detached full-width blocker card.
- **FR-067**: Analysis and Operations workspace MUST use consistent outer frames,
  header/select spacing and responsive reading order (analysis then workspace).
  Only the selected right panel occupies layout or keyboard/accessibility traversal;
  no nested card frames, arbitrary empty fixed heights, business-rule changes, new
  readers or timers. All diagrams, actual dates/scopes and unknown indicators remain.

Acceptance: fresh view has Shipping/Responsibility, exactly two primary card frames;
keyboard area switches do not reset a prepared takeover or paused log; hidden Agent
access continues its original reader without extra requests. Shipping blockers start
closed, expand in-place and restore across area switches. Both themes, all four
languages and narrow/docked widths remain readable without overflow.

## Owner-requested shared analysis including shipping (2026-10-07)

The owner explicitly requests shipping performance in the same switchable analysis
location as the operational diagrams, as its first option. This supersedes separate
shipping/analysis placement in FR-059; Responsibility remains prioritized before logs.

- **FR-062**: One shared analysis card MUST offer Shipping performance first, followed
  by the existing five flow areas. Fresh/invalid area selection and company change
  default to shipping; existing bookmarked flow areas remain supported. Switching
  stays local, keeps selector focus/viewport/history and exposes one selected view.
- **FR-063**: Shipping MUST retain its exact day/site scope, plan/confirmed/forecast
  curves, all metrics, basis and supporting-order investigation within the common
  analysis location. Live flow views retain their independent company-wide 60-minute
  scope, every diagram and disclosures. Hidden view state/paused inspection survives
  switching; do not duplicate frames, readers, business rules or calculations.
- **FR-064**: After the instruments, analysis occupies the main left column and
  Responsibility leads the right column, followed by the log and Agents. Narrow order
  is analysis, Responsibility, log, Agents. There MUST be no second standalone shipping
  or flow-analysis block. Scoped shipping investigations stay beside the selected
  shipping view; opening a shipping investigation from the deviations panel selects
  shipping in the shared card. No action or confirmation permissions change.

Acceptance: a fresh page shows shipping inside the sole analysis card with six options;
shipping → messages → shipping preserves both mail plots and the opened shipping basis
and supporting investigation. Existing flow bookmarks work; company change resets to
shipping. Both themes, four languages and narrow/docked layouts pass without overflow.

## Owner-requested hierarchy and quiet observation controls (2026-10-07)

The owner explicitly requests a coherent box hierarchy, Responsibility ahead of Agent
inventory, a contained analysis panel and compact icons for observation-only actions.
This supersedes FR-052's row placement; FR-053–058 data/selection/control meaning stays.

- **FR-059**: After the instrument overview, the first desktop row MUST contain shipping
  on the left and whole-case Responsibility on the right. The second row MUST contain
  selected analysis on the left and the event log with registered Agents beneath it on
  the right. Responsibility MUST precede event/access monitoring on narrow screens and
  in document order. Shipping remains adjacent to its supporting investigation. Keep
  every risk/evidence/Agent/control view, the same four readers and tenant boundaries.
- **FR-060**: Detailed analysis MUST be one complete card, containing its heading,
  single labelled area selector, metrics, plots and evidence. Do not frame an extra card
  inside it or leave a freestanding large header between regions. Main cards MUST use
  consistent padding, heading size and section rhythm. Compact cards keep natural
  height rather than stretching across a long diagram. Retain both mail plots, original
  measurement units, wrapped-metric alignment and stable selection/viewport behavior.
- **FR-061**: Read-only observation utilities (shipping basis, pause/resume event
  following, expand/compact Agent list, close observation detail) MUST use quiet small
  icon buttons in the related card header/detail, with localized accessible names,
  explanatory hover titles, visible keyboard focus and applicable expanded/pressed
  state. Supporting-work navigation remains descriptive quiet text. Business takeover,
  handback, reasons, confirmation and lifecycle limits MUST remain explicit text controls;
  iconization MUST NOT change a permission, review or mutation semantic.

Acceptance: shipping/Responsibility share the first desktop row; analysis/log share
second, Agents follow log; narrow order is shipping, Responsibility, analysis, log,
Agents. Analysis has one border and one selector; matching main-card heading/padding;
short case card is not stretched. Icon utilities retain keyboard activation, state,
source explanation, paused list/inspection and exact reviewed control persistence.
Both themes, four languages and narrow/docked layouts are required.

## Owner-requested stable analysis interaction (2026-10-07)

The owner requests systematic removal of surprising viewport jumps and duplicated
area selection. The smallest coherent interaction separates monitoring from analysis.
This explicitly supersedes instrument navigation in FR-048; FR-052–056 remain intact.

- **FR-057**: The top operational instruments MUST be read-only monitoring summaries,
  retaining complete risk counts, proportional meters and legend. They MUST NOT show
  selection styling, detail-navigation affordances or perform area selection. Finance
  retains its explicit specialist-workspace link. Detailed analysis has exactly one
  labelled, keyboard-accessible area selector beside its charts, using the existing
  five areas. No repeated area button strip or second selection source is shown.
- **FR-058**: Changing the analysis area MUST update only the selected diagrams and
  evidence in place, preserve the viewport and focus on the selector, and never force
  anchor scrolling. Retain bookmarked area support without adding a history entry for
  each area change. Live refresh retains the chosen area/disclosures; changing company
  resets area to Orders. Shipping/log/Agent/responsibility geometry and reviewed case
  state are unaffected. No new reads, business rules or mutations are introduced.

Acceptance: summary is non-interactive except explicit Finance navigation; one selector
changes Messages to Supply and back without moving the analysis header or focus; both
mail diagrams remain; a bookmarked area survives reload and refresh; another company
resets selection. Both themes, four languages and narrow/docked layouts are required.

## Approved preview parity refinement (2026-10-07)

The owner explicitly approved matching the supplied instrument-console preview,
including mixed risk meters and its two-row layout. No unresolved clarification.

- **FR-052** (row placement superseded by FR-059): After the instruments and legend, place shipping on the left and the
  recent business-event log with the single registered Agent/access inventory on the
  right. Below, place selected detailed analysis on the left and the existing whole-case
  responsibility register on the right. Stack these regions in the same reading order
  in narrow content. Preserve every diagram, evidence path, inspection and reviewed action.
- **FR-053**: Each instrument MUST show exact primary-cohort counts labelled In plan,
  At risk and Critical, plus an explicit unclassified count when needed. Derive disjoint
  counts in the shared operating-flows service from the complete scoped cohort before
  preview limits, using opaque identities and existing exception severities: high/critical
  is Critical, other findings At risk, no finding in a dated assessed delivery cohort
  In plan. Orders collapse all open lines to one order with worst finding winning;
  missing dates stay unclassified unless an actual finding is stronger. Include the
  canonical due-soon class that supersedes unreserved findings. Supply counts open lines;
  stock counts only the displayed oversold-item subset, never all inventory. Pending
  return positions without a held exception stay unclassified because absence of a
  learned resolution threshold is not evidence of timeliness. Message urgency has no
  held SLA/deadline assessment; its three risk counters MUST remain null and the known
  unanswered cohort unclassified. Finance and unavailable observations stay unknown.
  No new threshold, stored classification, business status or SQL query is introduced.
- **FR-054**: Render the meter as proportional colored widths with exact counts in text,
  and show a swatch legend directly below: In plan / At risk / Critical / Unclassified;
  explain that segments refer to the displayed open cohort. Green means no finding in
  the evaluated scope, not completed work or certified service quality. Empty cohorts
  and stale/missing assessment MUST NOT become a filled green meter or a false zero.
- **FR-055**: The recent-event log MUST be compact by default, with recorded timestamps,
  business labels and exact evidence links. Preserve its full bounded event list,
  pause/inspection state and recording-rate diagram via an explicit disclosure. Show
  the existing named Agent inventory immediately beneath it; keep permission/runtime
  limitations and all-access filtering without adding a second poller.
- **FR-056**: Responsibility MUST explain that supported cases run automatically and
  confirmed manual takeover stops new automated actions for that whole case. Show
  complete ownership counts and a compact initial human-owned case preview from the
  same register read; selection opens the existing filters/review controls. Preserve
  pending review/reason/revision state, company isolation and all lifecycle warnings.

Acceptance: desktop two-row alignment; narrow reading order; selecting Messages changes
only the lower detail panel and preserves both diagrams; mixed risk widths reconcile
with exact counts; unknown SLA is visible; named Agents and manually owned cases are
visible without expanding unrelated tables. Four languages and both themes are required.


## Owner-requested case takeover discoverability (2026-10-06)

- **FR-042**: A compact case ownership/whole-case takeover entry MUST appear alongside the selected detail analysis in the second console row (FR-052 supersedes the original position). Show complete automatic/human counts from the existing case register read. Case search, filters, inspection and pagination are initially collapsed so routine observation remains compact. Explicit selection and a bookmarked case open the adjacent workspace. Do not add a second register, read, poller, global overlay or mutation.
- **FR-043**: Explain in business language that the system automatically handles supported order-fulfillment/announced-return cases under default coordination; the operator selects one and confirms manual takeover, blocking new automated starts for that entire supported case. Identify where manually taken-over cases appear and that takeover alone does not complete the work. Preserve already-started-action and related-case scope disclosures in the reviewed confirmation.
- **FR-044**: Labelled automatic/human count buttons and a selection disclosure MUST provide keyboard-accessible entry to the existing register. Human entry shows the existing human-owned filter (including completed work); automatic entry shows supported open work without changing the meaning of the automatic total. Opening/closing is presentation-only, preserving selected inspection, review/reason/request state and live reads; it MUST NOT itself stop, complete or hand back work. The bounded entry/workspace wraps in all four languages, both themes and mobile/narrow content without overflow; shipping curves and all existing observations remain intact.

Acceptance: test compact initial state and upper placement, keyboard disclosure, count entry/filter behavior, existing reviewed takeover/handback, bookmarked case access and state preservation. Run four-locale/theme/responsive browser regression, frontend contracts/format/i18n/build and spec/lint; activate web only and inspect the real company without performing a takeover. Earlier rollout gates remain open.

## Owner-requested workspace surface consistency (2026-10-06)

- **FR-041**: The Control Tower page canvas MUST use the same semantic workspace surface as the existing company workspaces in light and dark mode, without an additional grey page-wide inset. Preserve the existing shipping/status/flow card grouping, neutral selection/detail surfaces, spacing, readable status colors, and all live, evidence and case-control behavior. Do not change global theme tokens or stored appearance preferences.

Acceptance: add a failing computed-style assertion to the existing four-language/light-dark/responsive cockpit browser proof, comparing the page canvas with the shared workspace surface and checking card, detail and selection surfaces. Verify frontend contracts/format/build, the full cockpit browser proof, and web-only local activation with actual UI screenshots. Existing enterprise/soak/rollout gates remain open.

## Owner-requested central status overview (2026-10-06)

- **FR-037**: A company-wide status overview MUST appear immediately below the cockpit live observation and above shipping, with all five operating areas visible as compact labelled tiles. Each tile shows a prominent signal, its textual condition and the existing primary metric with its unit/definition. The signal uses the existing shared service's critical/attention/progress/clear/unknown value without new thresholds or overall company/agent-quality scoring. Red means critical recorded condition; orange covers recorded attention, ordinary pending work and incomplete/stale/unavailable evidence; green means no finding in the evaluated scope. The underlying five service signals and their distinct textual conditions remain unchanged. Color MUST NOT be the sole meaning.
- **FR-038**: Each available tile MUST offer keyboard-accessible same-page navigation to its exact operating card and its existing definition/evidence. The summary MUST share the existing read and live lifecycle, retain company-wide scope regardless of shipping filters, show unknown for all stale/missing areas, never invent a zero, and introduce no timer, request, mutation, schema or mandate. All five tiles wrap without clipping at narrow content/mobile widths and retain four-locale/light/dark support. Shipping and existing aligned flow cards remain intact.

Acceptance: browser proof fails before implementation on absent overview; assert placement, all five distinct canonical states, exact metric parity, keyboard jump, stale/missing neutrality, no extra mutations, four-locale/theme responsive reachability and preserved existing cockpit functional regression. Verify frontend formatting/contracts/i18n/build, spec/lint/docs freshness and web-only local activation with an actual live screenshot. Earlier enterprise/soak/rollout gates remain open. Scope is directly authorized by the owner's request for a more visible central traffic-light system; existing recorded-condition semantics remain authoritative.


## Owner-requested visual consistency revision (2026-10-06)

The owner requested a Head-of-UX review and implementation of consistent spacing, aligned metric/chart starts and clear view selectors across the whole existing cockpit. The read-only UX review confirmed stacked flow-section margins, an unstyled standalone heading, variable metric-area heights and unrelated general-action styling on view filters. This authorizes presentation only.

- **FR-034**: Adjacent cockpit sections MUST share one outer vertical rhythm, explicit section-heading typography and a distinct heading-to-content gap. The flow heading MUST match the surrounding main-section headings; header metadata and action groups wrap within the available panel width. Do not compound section margin with parent gap, clip long names, or force page overflow in any supported locale/theme.
- **FR-035**: Flow cards sharing a desktop grid row MUST align their primary metric, corresponding metric-row and chart-slot starts within two CSS pixels, including all five cards on wide screens. Use shared content-sized layout tracks rather than fabricated metrics, fixed whole-card heights or clipped disclosures. The stock card retains its truthful current-only explanation in the chart slot. Notes, evidence disclosures and workspace footers have consistent slots. A single-column layout releases cross-card reservation; expanded evidence grows naturally. Counts, definitions, sources and live lifecycle remain unchanged.
- **FR-036**: Activity time choices and case-register filters MUST use the same accessible segmented-selection presentation, preserving labels, selected state, keyboard focus and existing callbacks. Keep inspection/business-control actions visually distinct and preserve every confirmation guard. Case, agent, deviation-preview and shipping-inspection navigation MUST share wrapping, subdued footer spacing with summaries separated from navigation actions. Shared `br-*` form/button states remain in use; no new control, query, business rule or backend change.

Acceptance: add a failing geometry/selection browser proof before implementation; verify 1440/1920 desktop rows, 390 mobile, a narrow side panel, all four locales, light/dark themes, keyboard selection, expanded evidence, ordinary action and paging behavior. Existing cockpit functional proofs and all frontend checks remain green. Rebuild only the local web image, verify real live page geometry/update preservation and leave simulator/Claude/API/MCP unchanged. Earlier enterprise-load/soak/rollout gates remain open.

## Owner-requested operating flow revision (2026-10-06)

The owner explicitly authorized implementing a compact, continuously updating overview of order intake/dispatch, messages awaiting a response, expected/received supplier goods, stock risks and arrived/processed returns. Existing shipping curves and deviations remain protected. This is observation, not a new human approval queue or execution mandate.

- **FR-028**: The main cockpit MUST include five compact company-wide operating flow cards alongside the protected shipping panel: customer orders, correspondence, supplier receipts, stock risks and customer returns. Counts use complete tenant-scoped cohorts before bounded evidence previews. Each card states its unit, rolling 60-minute scope, current backlog and applicable recorded exceptions. Shipping day/site filters do not narrow these company-wide live cards, including on a pinned day.
- **FR-029**: Correspondence MUST distinguish recorded inbound/outbound messages, simulator-local unread messages, and simulator-local messages without a linked recorded reply. Acknowledgement MUST NOT count as a response. Reply matching retains exact tenant/source-system/message lineage and counts each incoming message once despite multiple replies. A bounded historical unanswered curve and arrivals/first-response counts MUST reflect actual immutable recording times, not sampled pages or browser counters. Explicit existing customer party references identify customer requests; orders and supplier messages remain separate. Provider inbox/reply completeness and delivery remain unknown where no canonical provider response link exists.
- **FR-030**: Order counts MUST distinguish first recorded customer-order intake, open customer obligations and physical dispatch movement records; confirmed carrier handover remains exclusively the shipping definition. Supplier work MUST use shared effective open supplier quantities, excluding cancellation and corrections, count open promise lines and unknown dates, and distinguish actual receipt movement records from purchase documents. Quantities of different items/units MUST NOT be summed into a claimed goods total.
- **FR-031**: Returns MUST distinguish announcements still expected, effective physical return movement records, fully disposed return positions and outstanding physical disposition. Reuse canonical outstanding-announcement and return-disposition reads; a physical disposition MUST NOT assert refund or entire return-case completion. Corrected movements do not count. Unsupported disposition evidence is explicitly unknown. Stock risks MUST reuse canonical oversold-item exceptions and their evidence, without inventing replenishment thresholds, historical stock snapshots or risk horizons.
- **FR-032**: Traffic lights MUST summarize only the named recorded condition: canonical urgent exceptions are critical, other recorded exceptions require attention, known pending work is shown as non-critical open work without claiming active execution, and no finding means only no finding within the disclosed evaluated classes. Unknown/partial/stale coverage MUST NOT appear green. Message backlog direction and first-response rate are observations, not a service-level target or evidence that an agent performed well. Every card offers exact source/Reality preview links and its existing complete specialist workspace; there are no new business mutations.
- **FR-033**: New flow observations MUST use the existing authorized read-only company activity snapshot and live lifecycle, independently of shipping day/site observations, preserving access loss, stale time, filters, open records and control reviews. Curves are bounded to 13 five-minute buckets plus a current unanswered value, with gaps before company creation; default evidence previews show at most four records per card. No additional browser timer, persisted derived authority, schema or scheduler is introduced. Responsibility counts and items come exclusively from the existing independent case-register observation; the shipping snapshot must not repeat an unused register calculation. Exact case-linked shipping-deviation evidence remains within its shipping snapshot.

Acceptance: independent PostgreSQL fixtures prove complete totals beyond four/200 preview rows, acknowledgement versus reply, duplicate and foreign-run replies, order retry deduplication, corrected receipts/returns, partial supplier/return work, unknown dates/disposition, explicit exception severity and read-only tenant scope. Frontend/browser proof preserves shipping/risks and shows every card, units, curve labels, unknown/stale cases, exact evidence links, four locales and mobile reachability. Verify the actual retained local company and restart the existing stack to expose the result on port 8080. Existing enterprise workload and real-time pilot gates remain separately open until rerun for the expanded read.

## Owner-requested usability revision (2026-10-06)

The owner explicitly requested a working live local trial and a Head-of-UX review of the oversized lower-page tables and unclear case controls. This authorizes the following presentation refinements without changing business measures, supported case families, execution mandates or rollout scope.

- **FR-025**: The default cockpit MUST bound repeated evidence: show at most two collection-time entries per site and four deviation previews, with accessible disclosures preserving every returned entry, exact complete-result totals and the full-result inspection path. Recorded case actions MUST NOT be described as resolving a blocker without causal evidence.
- **FR-026**: Case navigation and activity rows MUST use business-facing responsibility/event labels from the existing presentation vocabulary, visibly distinguish open work from manual ownership, and state that automation normally works independently. Paging MUST describe replacement-page navigation; reset navigation is hidden on the initial page. Supported fulfillment/announced-return scope and takeover confirmation/handback guards remain explicit.
- **FR-027**: Selecting a shipping measure MUST immediately reveal and focus its supporting-order details adjacent to the shipping panel, preserving exact basis, explicit refresh, paging, close and return focus. Inspection MUST NOT be appended unseen below unrelated sections. No automatic refresh may execute an action or disturb an open review.

Acceptance: a fixture with hundreds of collection times and many actions remains compact by default, all exact entries remain reachable, shipping curves/live activity remain intact, a KPI click visibly opens its matching orders, keyboard close returns focus, and first/later case pages and manual responsibility remain understandable at desktop and mobile widths.

**Feature**: `378-enterprise-operations-cockpit`
**Created**: 2026-10-06
**Status**: Product scope approved by the owner in chat on 2026-10-06 ("ja geb ich"). The owner subsequently approved the concrete proposed shipping schema/model and live/Agent clarifications on 2026-10-06; implementation is authorized. New execution mandates, production rollout, merge and default-route replacement remain separately governed.
**Language**: English
**Input**: Incrementally bring the enterprise Control Tower concept into Reality as the primary observation surface for an autonomously operated ecommerce company. Preserve important details, especially shipping by end of day, and connect exceptional whole-case human takeover to existing workspaces.

## Context and Intent

### Problem

A Head of Operations needs to understand whether the business will meet its commitments, what is blocked, and what the autonomous agent is doing about it. The current entry page leads with human-facing queues and recorded activity volume. Neither recorded activity nor a completed-dispatch share establishes that today's shipping promises will be met.

The approved direction is one product with an operational surface, specialist workspaces and deeper Reality inspection. The enterprise concept supplies the visual and interaction reference. Replacing it with generic KPI cards would lose the time, capacity, location and responsibility information that makes it valuable.

### Scope

- An additional enterprise cockpit entry within the existing product, initially optional rather than replacing the current landing page.
- A first complete journey: shipping by end of day → affected orders → supported operational case → human takeover → existing specialist workspace → reviewed handback.
- A protected shipping panel with plan, confirmed handover, forecast, time/cut-off context, site selection, site breakdown and explanation paths.
- Scoped order risks, evidenced agent responses, a supported case overview and a human-owned case register.
- Explicit unavailable, incomplete and stale states where a company lacks the required business evidence.
- All-day live observation: automatically refreshed shipping/results, a rolling recorded-business-activity graph and an inspectable recent-activity stream, preserving the operator's current work.
- A compact named Agent/access overview in the primary cockpit, showing authorized connection records, last observed use and attributable actions without claiming an unverified external runtime state.
- A preserved concept inventory and an ordered migration map for later enterprise functions; deferred features remain individually identified.

### Non-Goals

- Redesigning every specialist workspace, replacing the Inspector, or changing the default landing page in this increment.
- Granting the agent new execution mandates, removing existing approval requirements, adding provider transports, or claiming fully autonomous execution merely because the dashboard exists.
- Expanding fulfillment takeover to billing, payments, independent returns or supplier work. New purchasing, Finance, service and master-data case policies require separate specifications.
- Implementing net-revenue reporting, company-wide six-family counts, service/return SLA reporting or a general decision-history product in this increment.
- Inventing hourly shipping targets, warehouse capacity, carrier confirmations, shipment locations or shipping deadlines from unrelated data.
- New background scheduling, a parallel workflow engine, or stored operational status on business documents.

### Existing Contracts

- [Web product](../../docs/WEB_SPEC.md): cockpit and Inspector in one product, shared operational logic and localization.
- [Operational cases](../../docs/features/operational-cases.md) and [spec 371](../371-operational-cases/spec.md): supported ownership scope, takeover and handback; [spec 377](../377-default-operational-cases/spec.md) supersedes legacy adoption with default coordination.
- [Shipments](../../docs/features/shipments.md): movements establish physical stock/fulfillment; attributed shipment events establish external observations.
- [Home activity and readiness](../../docs/features/home-live-status.md): recording activity and runtime availability have distinct meanings.
- [Spec-driven workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md) and [Constitution](../../.specify/memory/constitution.md).
- [Protected concept and migration map](migration-map.md) and [archived reference](reference/README.md).

## User Scenarios & Testing

### User Story 1 — Understand today's shipping outcome (Priority: P1)

An operations leader opens the cockpit and sees how confirmed handovers compare with the stated shipping plan, whether the remaining plan can be reached, and which site/cut-off matters.

**Why this priority**: This is the central business-performance detail the owner explicitly requires us to preserve.

**Independent Test**: Use a two-site company with accepted shipping work, timed plan inputs, attributed handovers and capacity inputs; verify all three series, totals, cut-offs and explanations at a fixed observation time.

**Acceptance Scenarios**:

1. **Given** complete evidence for today's shipping cohort at two sites, **When** the cockpit opens, **Then** it shows cumulative plan and confirmed handover, a separately styled future forecast, the observation time, relevant cut-offs, site selection and a site table with due, handed-over and risk counts.
2. **Given** an announced shipment, printed label or stock movement without applicable handover evidence, **When** the panel is read, **Then** it does not count that work as confirmed carrier handover and explains the evidence gap.
3. **Given** partial shipments, repeated carrier events or superseded evidence, **When** the series is evaluated, **Then** orders are counted once per defined cohort only after its required quantities satisfy the physical and handover conditions; invalidated evidence is excluded.
4. **Given** a missing dispatch deadline, timed plan, site mapping, handover timestamp or capacity input, **When** the panel opens, **Then** the affected measure or series is explicitly unavailable/incomplete; available evidence remains visible and unknown values are not zero-filled.
5. **Given** an unconfirmed extra collection request, **When** the forecast is shown, **Then** it is excluded from confirmed baseline capacity; its actual pending state and affected orders remain visible. A scenario that includes it must be explicitly conditional.
6. **Given** a selected site or chart interval, **When** the operator opens its supporting orders, **Then** the list uses the same company, day, site, cohort definition and observation basis as the measure, with differences after later changes made explicit.

### User Story 2 — Understand a deviation and the agent's response (Priority: P1)

An operations leader follows a shipping risk to its actual cause and sees what the agent has already proposed, started, completed or is waiting for.

**Independent Test**: Compare one blocked shipping cohort with no response and one with an evidenced response awaiting an external result.

**Acceptance Scenarios**:

1. **Given** a blocked due order, **When** its deviation opens, **Then** the screen states the causal records, affected order/case links, responsibility and any recorded next check; it does not turn every exception into a human task.
2. **Given** an actual case-linked response, **When** the operator inspects it, **Then** trigger, recorded decision basis, action and observed execution result are distinguishable. Without response evidence the screen states that none is recorded.
3. **Given** no approved 48-hour risk or on-time-shipping measure, **When** the summary is read, **Then** existing two-hour risk flags or all-history completed-dispatch shares are not relabeled to imitate those concept metrics.

### User Story 3 — Take over a supported case and finish it (Priority: P1)

An authorized member selects a fulfillment case, reviews its exact responsibility boundary and takes it over. The case is discoverable under human-owned work and opens the relevant existing workspace.

**Independent Test**: Exercise takeover, a concurrent change, an already claimed action and a current handback through the existing responsibility contract.

**Acceptance Scenarios**:

1. **Given** a supported fulfillment case under default coordination, **When** the member confirms its current takeover review, **Then** new automated starts are blocked under the shared control contract and the human-owned register shows the member, takeover time and exact scope returned by the authoritative control history.
2. **Given** an action already claimed or sent, **When** takeover commits, **Then** that action retains its actual execution state; the UI does not claim provider cancellation or start a replacement action.
3. **Given** a related return, supplier order or invoice, **When** fulfillment is taken over, **Then** those relationships remain discoverable and are not included in the ownership claim.
4. **Given** human-owned work, **When** the member opens its specialist workspace and returns, **Then** company, case and list filters are preserved. Handback uses the existing exact current review and refuses changed meaning or unresolved execution uncertainty.
5. **Given** a record without a registered supported case, **When** the operator opens it, **Then** existing business detail remains accessible; reads do not create or adopt a case and unsupported takeover is explicitly unavailable.

### User Story 4 — Use the new entry without losing the existing product (Priority: P2)

An operator can enter the new cockpit while retaining access to existing workspaces, inspection and genuine approval obligations.

**Independent Test**: Navigate the optional cockpit, an order, the Sales workspace, Inspector and contextual chat, then disable cockpit availability.

**Acceptance Scenarios**:

1. **Given** the cockpit is available, **When** the user navigates it, **Then** the performance view has full working space and chat opens on demand with the selected business context; existing queues and specialist pages remain accessible.
2. **Given** existing approval requirements or insufficient agent authority, **When** the cockpit displays case responsibility, **Then** those requirements remain enforced and discoverable. Assignment to an agent is not described as proof that the entire company is autonomously running.
3. **Given** an unavailable cockpit or revoked membership, **When** navigation is retried, **Then** existing permitted routes remain usable and no cross-company data is shown.
4. **Given** a refresh failure, **When** the cockpit already has results, **Then** it retains and marks them stale, does not extend the confirmed curve into unknown time and does not preserve an unsupported positive readiness claim.
5. **Given** the accepted concept inventory, **When** an increment is reviewed, **Then** every concept feature is accounted for as included, explicitly unavailable for missing evidence, or deferred to a named stage; disappearance is not a valid migration status.

### User Story 5 — Observe the company working throughout the day (Priority: P1)

An operations leader leaves the cockpit open throughout a working day and sees real changes in shipping performance, recorded business activity, evidenced agent responses and case responsibility without manually reloading.

**Why this priority**: The owner explicitly confirmed that continuous visible activity is part of the primary product experience, alongside the shipping outcome, rather than an optional technical-monitor page.

**Independent Test**: Keep the cockpit open with controlled time and actual fixture updates; prove automatic updates, an advancing rolling window, quiet periods, recovery and stable investigation/control state over a sustained session.

**Acceptance Scenarios**:

1. **Given** a visible cockpit and healthy reads, **When** a new recorded order, effective handover or supported case-control change becomes available, **Then** the relevant graph, values and recent activity update without navigation, with new committed changes visible within ten seconds under the declared acceptance workload.
2. **Given** an observed quiet period, **When** time advances, **Then** the short-term activity window advances with known-zero buckets; after a failed read, new unobserved time is unknown. The daily shipping chart retains its business-day meaning and its confirmed series ends at the actual observation time.
3. **Given** an open order, scrolled activity history, contextual chat or takeover/handback review, **When** new data arrives, **Then** selections, filters, scroll and unsent input remain stable; new items are indicated without moving inspected history. Changed control meaning still requires the existing fresh review, and no refresh confirms an action.
4. **Given** a hidden tab, connection failure, company switch or revoked membership, **When** the tab resumes or context changes, **Then** it refreshes the permitted current context, cancels obsolete reads and never restores another company's data or an unsupported positive live state.
5. **Given** the default Today view crosses company midnight, **When** the next successful observation arrives, **Then** it follows the new company business day with explicit plan coverage. A deliberately selected historical day remains pinned; rolling current activity is clearly labeled separately.
6. **Given** an eight-hour session with new events, quiet intervals, a failed read and recovery, **When** sustained observation is verified, **Then** requests, chart buckets and recent-event buffers stay bounded, and the current view remains responsive. Pausing activity-following changes presentation only and never stops the Agent or a business case.
7. **Given** permitted company access to named manual MCP credentials and authorized clients, **When** the cockpit opens, **Then** a compact Agent/access overview shows their recorded names, access state, last observed use and any exactly attributable recent action; all matching access records are discoverable through pagination. Repeated display names remain distinct records and access counts are not labeled as unique Agent counts.
8. **Given** a never-used, revoked, stale or unsupported external connection, **When** the overview refreshes, **Then** it shows the actual known state and observation age without inventing an online, working, disconnected or stopped state. Existing owner-only connection visibility remains enforced independently of normal member cockpit access.

### Edge Cases

- Empty companies; no shipping due; zero-denominator rates; orders with no accepted delivery commitments.
- Partial deliveries, split sites, different line deadlines, cancelled commitments and no-backorder/ship-complete rules.
- A shipment-wide event versus a package-specific event; supersession; duplicate reports; one package carrying several commitments.
- Physical dispatch without carrier handover, carrier handover without compatible physical contents, missing event time and late historical import.
- Booked customer-arrival slots that are not dispatch slots; delivery deadlines that are not shipping deadlines; unassigned sites.
- Same order due at multiple sites: company totals deduplicate orders and need not equal the sum of site order counts.
- Plan revisions and historical corrections after a snapshot; business-day boundaries and daylight-saving changes; different site time zones.
- Changed ownership during review, uncertain external execution, delayed case reconciliation, historical work awaiting bounded platform reconciliation and revoked membership.
- Refresh failure, incomplete source coverage, pagination, fast company switching and large-company workloads.
- Eight-hour observation, quiet rolling windows, hidden-tab recovery, company midnight while an order/review is open and new activity arriving while history is inspected.

## Requirements

### Functional Requirements

- **FR-001**: The cockpit MUST be an optional entry in the existing product, preserve access to current workspaces/Inspector and leave the current landing page unchanged in this increment.
- **FR-002**: The shipping panel MUST preserve the reference's three-series hierarchy, day-end context, cut-off markers, site selector, due/handed-over/risk breakdown and forecast-basis disclosure.
- **FR-003**: Each shipping measure MUST disclose the selected business day/time zone, observation time, unit, cohort membership rules and coverage. Dates must express their actual dispatch meaning; customer-arrival promises or generic delivery slots MUST NOT silently become shipping deadlines.
- **FR-004**: Cumulative confirmed handover MUST count a distinct order only after all non-cancelled quantities required by the selected day/site cohort have compatible effective physical shipment contents and applicable effective handover evidence. The explanation MUST distinguish cohort completion from completion of the entire order.
- **FR-005**: Confirmed handover timing MUST use stated applicable event time, not ingestion time; missing or conflicting timing MUST remain explicit. Announcements, labels, picking and unaccompanied stock movements MUST NOT count as carrier handover.
- **FR-006**: Timed plan values MUST come from an attributable dispatch plan or an explicitly identified, approved planning model. A daily total alone MUST NOT be drawn as an invented hourly plan.
- **FR-007**: Forecast MUST be a separately identified estimate from the observation time onward, with input coverage, assumptions and calculation-version explanation. Baseline capacity MUST exclude unconfirmed extra collections; unavailable prerequisite inputs MUST make forecast unavailable rather than fabricate a trajectory.
- **FR-008**: Site filtering, table values and supporting-order navigation MUST use the same measure definitions. Company order totals MUST deduplicate split-site orders; site counts MUST explain possible overlap. Unassigned sites MUST remain visible without guessed assignment.
- **FR-009**: Shipping cut-offs MUST have recorded business meaning and relevant site/time-zone context. A company's aggregate view MUST preserve differing site cut-offs rather than imply one global collection time.
- **FR-010**: Plan, handover and risk explanations MUST expose supporting orders, underlying evidence and any coverage gap. Supporting lists MUST paginate without changing complete-result totals, and preserve the snapshot basis or visibly re-evaluate after changes.
- **FR-011**: Deviations MUST distinguish business impact, current responsibility, actual recorded agent reaction, pending external outcomes and recorded next check. No response evidence MUST remain an explicit absence, not generated progress text.
- **FR-012**: Unsupported reference measures MUST remain explicitly unavailable or deferred. Existing risk horizons, movement-based dispatch counts and completed-dispatch shares MUST retain their actual meanings and MUST NOT be relabeled as 48-hour risk, confirmed handover or seven-day on-time SLA.
- **FR-013**: Supported case detail MUST show outstanding work, exact owned scope, related independent work, evidence gaps and claimed/sent/uncertain actions before takeover or handback.
- **FR-014**: Takeover and handback MUST use the existing authorized, confirmed, replay-safe responsibility controls and current reviews; concurrent changes, revoked authority and unresolved uncertainty MUST retain their existing refusal behavior.
- **FR-015**: The human-owned register MUST include every matching supported case through pagination, exact responsibility and authoritative control attribution; opening a case MUST preserve company and origin filters. Requested optional reasons MUST NOT be presented as retained unless the control contract actually records them.
- **FR-016**: Navigation MUST connect the case to the existing relevant specialist workspace and Inspector, with contextual chat on demand instead of a permanently reserved large chat column.
- **FR-017**: No cockpit read, filter or navigation MUST adopt historical work, change a case boundary, execute a business action or grant agent authority. Existing genuine approval obligations MUST remain accessible and enforced without making every deviation a human approval queue.
- **FR-018**: Loading, empty, unavailable, partial, stale and failed states MUST be distinct. Last successful values MUST retain their observation time, and unknown elapsed time MUST NOT become zero or confirmed progress. Technical readiness MUST remain distinguishable from business success and agent mandate/coverage.
- **FR-019**: The cockpit MUST retain the product's existing supported languages, number/date formatting, themes and accessible keyboard navigation. Business-day evaluation MUST remain explicit when it differs from the viewer's display time zone.
- **FR-020**: Every protected concept item in the migration map MUST retain an accountable included/unavailable/deferred status and acceptance evidence before rollout. The preserved reference MUST remain available for visual and interaction comparison.
- **FR-021**: The visible cockpit MUST automatically refresh shipping, relevant counts, supported case responsibility and evidenced responses, and show a rolling recorded-business-activity graph and recent-event stream. Healthy reads MUST expose committed changes within ten seconds under SC-004; the rolling time axis MUST advance during quiet periods without inventing activity. Recorded time, business occurrence time, confirmed progress and forecast MUST retain their distinct meanings.
- **FR-022**: Live updates MUST preserve filters, selected/open records, scroll, contextual chat input and current control review. Inspected activity history MUST offer a new-items indicator and explicit resume-following behavior; pausing following MUST NOT stop the Agent. Current control guards MUST invalidate changed reviews without auto-confirmation. The Today view MUST follow company-day rollover while explicitly selected dates stay pinned.
- **FR-023**: All-day observation MUST use bounded chart/event data, non-overlapping cancellable reads and explicit last-success/connection states. Hidden-tab resume, failure recovery, company switching and access loss MUST preserve tenant isolation and unknown-time semantics. Business activity MUST trace to recorded events; activity alone MUST NOT imply agent execution, case completion, availability or external success. Dense daily shipping curves MUST use exact full-cohort cumulative counts at disclosed five-minute boundaries (including opening/terminal counts), with at most 302 points per series on a 25-hour company day. Smaller series retain exact event points; full fingerprints and supporting-order/evidence reads remain complete.
- **FR-024**: The main cockpit MUST include a compact named Agent/access overview for authorized viewers, covering manual MCP access records and authorized client grants with exact recorded names, access state, last observed use and attributable latest actions where supported. Full matching access totals MUST precede pagination; identities MUST remain opaque and credential-kind-qualified, never deduplicated by name or asserted to identify a unique runtime Agent. Existing connection-disclosure/owner boundaries MUST remain enforced. Registration, usable access or recent use MUST NOT imply a persistent connection, mission, current execution, business completion or external runtime health; unsupported current states MUST remain explicit.

### Domain and Traceability Requirements

- **DR-001**: Important observations and control actions MUST preserve the shortest Source → Evidence → Reality explanation path using opaque business identities. The cockpit MUST NOT introduce alternative business rules.
- **DR-002**: Shipment, fulfillment, stock, risk and financial observations MUST remain derived from authoritative Reality and applicable stated inputs; operational status MUST NOT be added to Documents or persisted as a new authority to populate this dashboard.
- **DR-003**: All reads, aggregates, explanation paths and controls MUST enforce current company membership and tenant boundaries and use shared application semantics across Web, Chat, CLI and MCP.
- **DR-004**: Fulfillment/announced-return ownership MUST retain spec 371 control/policy limits and spec 377 default coordination. The cockpit register MUST NOT require legacy owner adoption; it MUST expose canonical rollout readiness separately from responsibility counts. Relations to billing, supplier or unsupported work MUST NOT enlarge control scope; human ownership MUST NOT claim external cancellation.
- **DR-005**: Complete-company totals MUST NOT be calculated from a capped example list or a page of cases. Read activity MUST NOT create business records or implement a second scheduling mechanism.

### Key Entities

- **Shipping cohort**: Accepted shipping obligations in an explicitly defined dispatch day/site scope, related to their orders; not a new authority for promises.
- **Shipping plan**: Attributable timed dispatch targets with their business meaning and current version; distinct from physical progress.
- **Confirmed handover evidence**: Effective attributed handover observations linked to the physical consignment/contents and stated event time.
- **Forecast observation**: Explained estimate using known progress and supported remaining capacity; never evidence of actual shipment.
- **Operational case**: Existing bounded responsibility for supported work; related business objects do not automatically belong to it.
- **Cockpit snapshot**: Read-time observation basis and coverage for consistent summaries and drilldowns, not a stored business truth.

## Success Criteria

- **SC-001**: On the two-site acceptance company, plan, confirmed handover, forecast, site counts and supporting orders exactly match independently calculated expected results, including partial shipments, split sites, duplicates and supersession.
- **SC-002**: At 1440-pixel desktop width, shipping by end of day, its site selector, legend, cut-offs and site breakdown are present in the primary operational area without a persistent chat column. At 390-pixel width all controls remain reachable without page-level horizontal overflow; tables may scroll within their own region.
- **SC-003**: An operator can navigate shipping risk → matching order/case → takeover review in at most three navigational actions, excluding confirmation. After confirmed takeover, the case appears in the human-owned register on the next successful refresh and automated starts remain blocked independently of that refresh.
- **SC-004**: A proposed acceptance workload of 10,000 active orders, 100,000 historical orders and 500,000 shipment observations supports ten simultaneous observers: 95% of cockpit openings and site-filter changes show results within three seconds. Hardware, cold/warm measurements and input distribution MUST be reported; this benchmark does not infer capacity from annual revenue.
- **SC-005**: All 25 protected product items (23 archived concept capabilities plus the owner's live-observation and Agent-overview clarifications) have explicit migration status and evidence; all first-increment items retain their required details. A screenshot with unavailable placeholders alone does not satisfy the fully populated shipping acceptance case.
- **SC-006**: Every FR and DR maps to a scenario and planned executable proof; existing authorization, shipment and responsibility regression checks remain green. Missing-data, stale-data and cross-company cases show no fabricated values or leaked controls.
- **SC-007**: A deterministic eight-hour browser session verifies bounded buffers/requests, company-day rollover, quiet intervals, hidden-tab recovery, one connection failure and stable inspection/control state. Under the SC-004 ten-observer workload, healthy live updates display committed fixture changes within ten seconds; measured sustained refresh latency and request/query budgets are reported. A separate eight-hour real-time soak is required before pilot enablement.

## Assumptions and Dependencies

- The owner approved this concrete optional shipping/case-control scope and technical planning in chat on 2026-10-06 ("ja geb ich"). That approval does not approve new schema, new case policies or changed execution mandates.
- The enterprise reference is an intentional German business example. Its numbers, sites, names and agent actions are illustrative, not production evidence.
- EUR 100 million annual revenue describes the intended audience, not a query-performance measurement. The stated workload is a proposed, reproducible acceptance profile for product review.
- Current shared business reads supply useful movement-based dispatch/readiness metrics. They require a separate confirmed-handover interpretation and full-cohort aggregation for this panel.
- Existing shipment events and planned outbound deliveries offer relevant records, but a booked slot alone does not prove dispatch meaning, hourly targets, carrier capacity or collection cut-offs. Planning must prove exact input coverage before adopting them.
- A company with incomplete planning/capacity inputs remains usable through explicit unavailable states. Completion of this feature requires both that behavior and the fully populated acceptance company, with attributable planning inputs and an explained forecast method.
- Product scope review is complete. Any necessary repeated-use schema or forecast-policy design remains subject to the existing Constitution and architecture review gates.
- On 2026-10-06 the owner explicitly added all-day live observation to the cockpit requirement. Its presentation/read contract is recorded in [live observation](contracts/live-observation.md); this clarification does not approve the pending shipping schema/model.
- The owner additionally requested a named overview of the Agents/accesses contributing to the company. Existing named credentials, authorized clients and observed calls provide the initial read basis; no external runtime registration or heartbeat protocol is introduced or inferred.
- Spec 377 default coordination is authoritative: accepted supported work is automatically covered and bounded platform rollout handles open history. The cockpit must not recreate owner activation, backfill work on a read or infer full coverage before canonical rollout readiness. Existing roles, permissions and responsibility controls remain unchanged.

## Requirement Traceability

### Instrument console refinement approved on 2026-10-07

The owner approved the Instrument console concept and explicitly retained detailed
incoming/processed diagrams. This refinement supersedes the simultaneous default
five-card layout in FR-035 while retaining every metric, definition and evidence link.

- **FR-047**: The top company-wide overview MUST use compact instruments with a large
  primary count, a labelled classic traffic-light condition and a proportionate risk
  meter (FR-053 supersedes the original decorative strip). It MUST retain the five canonical areas. Finance MUST be explicitly unavailable
  in this observation, with a link to its existing workspace and no invented count.
  The meter uses only the complete, explicitly defined primary cohort and the canonical classifications described in FR-053.
- **FR-048**: Detailed analysis MUST support bookmarked areas and keyboard navigation.
  FR-057–058 supersede the original instrument click/anchor behavior: one local area
  selector changes analysis in place without scrolling or duplicate selection. All existing evidence,
  specialist links and supported case controls MUST remain accessible. Selection and
  evidence disclosures MUST survive live refresh, and company changes MUST reset selection.
- **FR-049**: Message analysis MUST show two distinct diagrams: local incoming versus
  first recorded replies in five-minute buckets, and unanswered backlog over the last
  hour. Duplicate replies, reading/acknowledgements, foreign company/run replies and
  unassociated provider messages MUST NOT inflate answered work. Missing/partial
  coverage MUST stay explicit. Missing bucket counters MUST never render as zero.
- **FR-050**: Other detailed diagrams MUST retain canonical units: orders recorded
  versus physical dispatch records, goods receipt records, and return arrivals versus
  disposition movement records. Stock MUST stay current-only. The browser MUST NOT
  infer queue history from incompatible counts, agent quality, completed cases or
  successful external delivery. Shipping plan/handover/forecast, cutoffs, supporting
  orders, deviations, access inventory and reviewed case controls MUST remain intact.
- **FR-051**: Instruments, analysis metrics and curves MUST fit 320px, 390px, docked
  720px and desktop widths in both themes and four languages. Diagrams MUST provide
  readable count/time axes, series labels and missing observations. No new poller,
  business write, stored status, dependency or default-route/capability change is allowed.

Acceptance scenarios: (1) keyboard-select Messages and compare the two explicitly
labelled diagrams and complete totals; (2) switch to Returns and inspect actual
movement units/evidence; (3) refresh while a disclosure is open and retain selection;
(4) navigate a bookmarked area and reset on company change; (5) stale/unknown coverage
cannot become green or zero; (6) all display sizes retain shipping and manual controls.
Success: each evidenced area is reachable in one instrument selection, message
incoming/first-reply bucket sums match canonical totals for a fully covered hour,
and the supported widths have no page-level horizontal overflow.

| Requirement | Proof tasks |
| --- | --- |
| FR-047–048 | T082, T084, T086 |
| FR-049 | T083, T085, T086 |
| FR-050–051 | T082, T084, T086 |

The owner authorized autonomous implementation and local viewing on 2026-10-07.
Existing reviewer-owned checklists and outstanding enterprise/soak gates remain open.

| Requirement | Scenario(s) | Planned test/evidence |
| --- | --- | --- |
| FR-001 | US4.1, US4.3 | Optional-entry navigation and rollback/access regression |
| FR-002 | US1.1, US4.5 | Two-site shipping story and reference-based browser inspection |
| FR-003 | US1.4, US1.6 | Cohort/day/time-zone and dispatch-versus-arrival semantics |
| FR-004 | US1.2, US1.3 | Independent order/quantity oracle with partial and split shipments |
| FR-005 | US1.2–4 | Handover attribution, missing-time and late-import checks |
| FR-006 | US1.1, US1.4 | Attributable timed-plan and daily-total-only checks |
| FR-007 | US1.1, US1.4–5 | Forecast input, confirmed-capacity and version explanation checks |
| FR-008 | US1.3, US1.6 | Multi-site deduplication, unassigned-site and filter parity |
| FR-009 | US1.1, US1.4 | Different cut-offs, site zones and daylight-saving checks |
| FR-010 | US1.6, US2.1 | Paginated full-cohort totals and changed-snapshot drilldown |
| FR-011 | US2.1–2 | Evidenced versus absent agent response business stories |
| FR-012 | US2.3, US4.5 | Metric identity and deferred/unavailable reference audit |
| FR-013 | US3.1–3 | Supported case scope, action uncertainty and evidence inspection |
| FR-014 | US3.1–4 | Existing responsibility races/replay/review tests plus browser journey |
| FR-015 | US3.1, US3.4 | More-than-one-page human-owned register and control attribution |
| FR-016 | US3.4, US4.1 | Context-preserving workspace, Inspector and chat navigation |
| FR-017 | US3.5, US4.2–3 | Read-only/adoption/mandate/permission regressions |
| FR-018 | US1.4, US4.4 | Refresh failures, unknown coverage and readiness separation |
| FR-019 | US1.1, US4.1 | Four-language/theme, keyboard and responsive browser checks |
| FR-020 | US4.5 | Migration inventory audit and reference fidelity review |
| FR-021 | US5.1–2 | Timed real-event refresh and rolling-window/quiet-period checks |
| FR-022 | US5.3, US5.5–6 | Stable inspection/review, presentation-only following and company-day rollover |
| FR-023 | US5.2, US5.4, US5.6 | Eight-hour lifecycle, bounded buffers/requests, recovery and tenant isolation |
| FR-024 | US5.7–8 | Named access/grant roster, attribution, complete pagination, owner disclosure and unknown runtime-state proof |
| DR-001 | US1.6, US2.1–2, US3.1 | Measure/action trace to exact Reality/evidence/source records |
| DR-002 | US1.2–3, US2.3 | Canonical result parity and no dashboard business-state writes |
| DR-003 | US3.1, US4.3 | Cross-tenant/member access and shared-service equivalence |
| DR-004 | US3.2–5 | Existing ownership policy and external-uncertainty regressions |
| DR-005 | US1.6, US3.5, US4.4 | Full-result totals beyond example/page limits and read-only checks |

These are planned proofs, not executed tests or completed acceptance criteria. Exact test paths and tasks follow product review in the technical plan.

## Implementation Authorization

The owner approved the prepared concept and implementation proposal on 2026-10-06 ("I like all of it, approval"). This includes the separately presented three-table shipping-input design, completion-slot-v1, all-day-live observation and named Agent/access overview. See [review record](review.md). Earlier pending-approval statements above describe the proposal history; this later explicit approval satisfies that implementation gate. It does not grant new external mandates, enable a production pilot, authorize merge or replace the default route.


## Permanent Control Tower navigation revision (2026-10-06)

- **FR-039**: The authorized company shell MUST always show the Control Tower navigation destination on first entry, Home, specialist pages and company changes, without requiring prior direct cockpit entry or inferring permission from route history. This supersedes hiding the navigation entry for an unavailable capability; the backend default-off feature and membership/business-company guards remain unchanged. Home stays the default landing page. The shell waits for same-company capability resolution before mounting operational reads, and unavailable/failed capability shows a clear current-company explanation and a permitted Home return rather than a disappearing link or redirect loop. A revoked read in an already enabled cockpit retains existing access-loss handling. No unknown/disabled company can receive operational data or controls.
- **FR-040**: The product destination, shell/page titles and return link MUST use the name Control Tower consistently in all four supported languages. Preserve `/app/cockpit`, query/bookmark/origin semantics and internal/API/tool identifiers. The unavailable explanation MUST guide the user to the existing company menu; choosing another company uses its fresh capability and never retains a prior company's positive availability. No company default, membership, purpose, execution mandate or stored browser preference is changed.

Acceptance: first-root/default-playground discovery and unavailable state, enabled-company navigation with unchanged Home, disabled and failed capability, company switch and in-flight isolation, fresh direct URL, consistent four-locale labels, responsive shell/chat and existing cockpit regression. Tests first, full frontend/format/i18n/build, spec/lint/docs freshness and web-only local activation with actual root-entry and company-switch screenshots. Owner explicitly requested a permanent navigation point and reconsidered the former label; Control Tower follows the existing enterprise concept. No unresolved clarification or backend/schema change. Existing enterprise/soak/rollout gates remain open.


## Classic traffic-light palette (owner authorization, 2026-10-06)

- **FR-045**: The central company-status indicators/borders and operating-flow status dots MUST use only red, orange and green. Canonical critical stays red and clear stays green; attention, progress and unknown all render orange while retaining their existing distinct textual labels, evidence definitions and stale/missing semantics. The localized legend explains orange as pending work, attention or incomplete evidence and contains no blue/grey status category. This is presentation only: no new severity, threshold, service result, action mandate, read, timer or schema. Missing/stale evidence never renders green. Both themes, four locales, keyboard detail navigation and responsive layout remain supported.
- **FR-046**: Shipping fingerprints use a versioned canonical representation of every fulfillment-readiness field for every cohort requirement. Only the disclosed first-fifty readiness preview and selected order details materialize the existing readable evidence shape; neither complete calculations nor supporting-order evidence may be sampled.

Acceptance: extend the existing populated/all-signals/stale browser proof before styling; verify exact visible palettes for all five canonical signals in the summary and details, both themes and every supported locale. Retain the full cockpit regression and run frontend contracts, localization, formatting and build. Activate only the local web image and inspect the actual port-8080 company without altering the running operator or simulator.

## Missing daily plan recovery (owner request, 2026-10-07)

- **FR-071**: A missing selected-day shipping plan MUST NOT hide observed physical shipping activity. Expose independently labelled effective shipment-booking order counts and confirmed handed-over package counts, with cumulative selected-company-day series, exact location/time scope and source trace. Package counts MUST NOT masquerade as completed plan orders. Deduplicate effective package/shipment observations, exclude future, corrected and superseded evidence, and never use ingestion time as handover. Existing plan totals, completion and forecast remain unchanged and unknown without accepted evidence.
- **FR-072**: Without a usable daily cohort, affected shipping orders MUST remain unknown rather than zero and the UI MUST explain that only plan comparison/forecast are unavailable. Existing actual activity remains live through the existing snapshot lifecycle; no additional polling or business mutations.

Acceptance: yesterday-only planning plus today's physical booking/handover remains visible; partial/duplicate/future/superseded events, company-day boundary, site and tenant isolation preserve exact units and counts; no-plan blocker total is unknown; existing plan calculations and supporting orders retain parity. Tests precede implementation. Local simulator planning recovery is specified in spec 376 and does not authorize production plan acceptance.


### Unified console heading hierarchy

- **FR-073**: The shared analysis and Operations workspace cards MUST each expose one consistent primary heading for the currently selected content. Use the stable card category (Flow analysis / Operations workspace) as a small eyebrow and the selected topic as the sole h2. Switching the six analysis areas or three workspace views updates this heading without duplicate inner topic headings, new navigation or resetting retained review/live state. Embedded child views retain contextual descriptions, status, evidence and controls, including shipping basis and owner-only Agent feedback; standalone child use retains its own heading.

Acceptance: shipping defaults to Flow analysis / Shipping by end of day; returns
uses Flow analysis / Returns & disposition; the right default uses Operations
workspace / Cases & takeover. Log and Agent views follow the same hierarchy.
Both titles use the same shared typography and remain readable at phone/docked/
desktop widths in all product languages and themes. There is one visible h2 per
primary card, with no dangling accessible section labels.


### Full instrument tile activation

- **FR-074**: Clicking any non-secondary-control part of an available instrument tile MUST open its existing compact all-work inspection dialog, including title, primary count, meter, status and padding. A single native primary button provides the full hit area and keyboard Enter/Space behavior without nesting risk buttons. Known risk counts retain their specific group activation, unknown/unavailable data stays disabled, and Finance retains its existing workspace link. Closing/Escape restores the primary trigger focus, with visible full-tile hover/focus feedback; no chart/URL/history/reader/business mutation changes.

Acceptance: padding/title/meter/status clicks open the matching all-work preview
for all five supported areas, including an empty known cohort. Enter/Space do the
same; a risk click opens only its own group. Escape preserves scroll and focus.
Phone/docked/desktop geometry and both themes/four languages remain supported.


### Readable content grouping

- **FR-075**: The console MUST distinguish its primary panels, present-state metrics, recent activity metrics and individual plots through a consistent visible hierarchy. Keep one selected-topic h2 per panel. In each flow analysis, explicitly group current metrics under Current status and interval metrics under Last 60 minutes, without changing returned values, definitions or units. Each plot MUST contain its own title, series, range, legend and related coverage/change notes inside a visibly bounded plot surface. Current stock observations remain distinct from unavailable history. Shipping metrics, actual activity and plan/forecast plot remain separate and labelled. Use shared theme surfaces/borders, consistent section spacing and responsive label/value alignment; do not add navigation, duplicate selection or business readers.

Acceptance: messages show three present-state metrics and two recent activity
metrics with their existing values; the two message plots have distinct boundaries
and reply coverage/backlog change belongs to the backlog plot. Orders, supply,
stock and returns use the same grouping with explicit interval membership. Shipping
keeps its counts, interactive series, evidence and unknown-plan actual activity.
Responsibility instructions, counts/actions and manually stopped cases remain
visually separated; log and Agent rows use the same bounded-list treatment.
All four languages and both themes retain readable boundaries, aligned values and
no horizontal page overflow at 320/390/1440/1920 pixels. Full-tile and risk inspection,
manual review, retained selectors, live state and record links remain unchanged.


### Viewer observation timezone regression (FR-019)

Restore the existing independent display-timezone requirement: general observation
metadata in the top status, case register/control history and supporting-order
read timestamp uses the viewer's chosen timezone/locale with its date and UTC
offset. Company business-day selection, shipping curve axes/reference clock, due/
handover/forecast instants and site collection deadlines retain their explicit
business/site zones. Never pair a viewer observation clock with a company-day date
as though they describe one instant. Disclose the unchanged business calendar date next to the shipping context (FR-003).
No change to stored UTC values or calculations.
Acceptance: a UTC viewer of Berlin shipping sees 12:30 GMT rather than 14:30;
a Tokyo viewer sees 21:30 GMT+9 in observation metadata while Berlin shipping
remains 14:30 and site cutoffs retain their date/offset. The actual Berlin user
sees the same UTC observation two hours later in October. Stale retained metadata
keeps its original instant. Existing user formatting, keyboard/live/action proof
and business-day/date boundaries remain intact.


### Unified analysis and object-case presentation

- **FR-076**: Shipping and all flow analyses MUST use the same labelled metric-group and bounded figure presentation, including typography, spacing and responsive grids. Shipping has a Shipping plan group (due, handed over, forecast, risk), followed by its titled cumulative comparison figure with legend/context below. Observed shipping activity remains a separate group with booked orders and package handovers in their original units; its plan-independent figure remains available when the plan is absent. Company calendar/zone, plan gaps, forecast assumptions, cutoffs, exact supporting-order clicks and live reads remain unchanged. Site details are initially collapsed, explicitly named, keyboard accessible and retained across refresh/analysis switches. No duplicate analysis heading or selector is added.
- **FR-077**: The shared object Operational cases panel in Orders and document Inspector MUST have a styled disclosure, a bounded readiness/refresh area, separated case cards with kind/ownership/work state, a distinct control action row, and initially collapsed technical IDs/work/source links. The company-wide case list retains a visible stable case identity so multiple cards remain distinguishable before control. Shared takeover/handback confirmation groups MUST have their own styles loaded directly by the shared control component, independently of the Control Tower stylesheet. Existing exact confirmation, stable retry identity, membership, unresolved-action warnings and source links remain unchanged. No read or disclosure triggers a mutation.

Acceptance: shipping and message metric groups/figures share computed padding, border and value size in both themes and narrow/wide viewports; both message diagrams survive. A missing plan retains actual values/curve; all site cutoffs remain inspectable through disclosures. Object cases render bounded cards and spaced actions in the independently loaded case harness; ID/source links remain accessible on disclosure, takeover is still a separate confirmed action, and both object embedding paths reuse that component. No page overflow at 320/390/1440/1920px in all four UI languages.


### Cohesive instrument overview

- **FR-078**: The instrument overview MUST present the six existing areas inside one themed bounded section, with aligned title, primary value, metric description, compact proportional meter, labelled risk-count rows and condition slots within each responsive row. Risk labels precede right-aligned counts; the optional unclassified row reserves the same space across tiles. The shared legend is a separated centered footer with category keys, proportional-scope explanation and classification caveat kept together. Known zero work has an empty neutral meter rather than an unclassified segment; unknown/stale evidence remains hatched and never implies green. Counts, exact proportions, whole-tile and category inspection, Finance navigation, keyboard/focus, live reads and business authority remain unchanged.

Acceptance: compare matching row geometry across all six tiles at wide widths and responsive row groups in all four languages/both themes at 320/390/1440/1920px and a docked width. The footer contains all four keys and the existing complete caveat, centered without horizontal page overflow. Known zero and unknown/stale meters remain distinguishable. Retained whole-tile/category/dialog focus and record-link proofs pass.


### Business case overview and evidence briefing

- **FR-079**: Add a compact upper disclosure inside the instrument overview named Business cases in operation, with complete per-kind registered/open/automation/human counts from the existing canonical register read. Ownership counts include completed human-owned work and never claim an Agent is currently executing or waiting. Extend the existing tenant-scoped aggregate with grouped kinds without another periodic reader or business-state evaluator. Show order fulfillment and announced returns with their actual responsibility boundaries; Purchasing, Customer inquiries, Financial clarification and Master data remain explicitly unavailable as controllable case kinds, with unknown counts rather than zero. Counts open a bounded read-only, on-demand exact-kind/owner/outstanding preview with original object links, observation time, shown/total limits, keyboard/Escape/focus, company isolation and no automatic business writes.
- **FR-080**: Restore an upper compact Shipping deviations & recorded actions disclosure from the existing shipping snapshot, with affected-order total/scope, at most three original order rows, risk/ownership badges, the first held cause and a directly visible case-linked proposal/action status or explicit missing response. Retain exact action/source/order paths and the visible no-causal/no-external-outcome caveat; do not attribute an action to an Agent without evidence or group a bounded sample into a complete causal total. Full shipping evidence/inspection remains in the existing analysis disclosure. Keep both new disclosures mounted and preserve expansion across live/analysis changes; reset at company change. The German activity heading reads Zuletzt passiert.

Acceptance: per-kind totals are unchanged by register pagination/search/kind/ownership filters, partition the original global counts and remain tenant-scoped, including completed manual work and empty kinds. Browser proof verifies six named families/two supported kinds, all four numeric meanings, exact preview filter requests, no writes, original links, bounded/stale/unavailable/revoked states and company reset. Briefing exposes exact fixture causes/actions and unknown response states without implying successful autonomous remediation. All four locales/themes and narrow/wide viewports retain contained disclosures/table and existing charts/control flows.


### Compact shipping deviation tables

- **FR-081**: Both the upper shipping briefing and the detailed shipping deviations MUST use one compact semantic table presentation with Order, Recorded cause, Responsibility and Recorded case action columns. Keep original sample bounds (three/four), totals, source/object/proposal links, risk/ownership badges, unknown/empty messages and the causal/external-outcome caveat. The detailed table retains all held blockers/actions in native per-order disclosures, initially closed; expanding preview/evidence and live refresh preserve their existing behavior. Long original references wrap, horizontal scrolling stays inside the table on narrow/docked layouts, and all four languages/light and dark themes remain readable. No new read, service, business rule, timer or control permission.

Acceptance: each displayed order occupies one aligned summary row; original full action 39 is hidden until the per-order evidence disclosure opens; Show more still exposes eight fixture orders, and full supporting-order inspection retains exact scope/focus. Both upper and detailed tables remain inside the viewport in four languages, both themes and 320/390/1440/1920 widths.


### Stacked monitoring and one responsibility entry

- **FR-082**: The right column MUST show two independent, simultaneously visible cards: Recorded business activity (German: Zuletzt passiert), followed by Registered Agents (German: Angemeldete Agenten). Remove the right responsibility view and its selector. Whole-case inspection, confirmed takeover/handback, stopped-case list, exact evidence and rollout warnings remain available only within the upper Business cases in operation disclosure through an on-demand Cases & takeover disclosure. Reuse the single existing mounted register reader and omit its duplicate ownership totals; upper totals remain live. Case bookmarks open both containing disclosures; company changes reset local disclosure/inspection state. Closing disclosures, changing analysis or inspecting monitoring MUST retain prepared control review, paused events and Agent inspection without mutation. Preserve owner restrictions, stale/denied behavior, truthful authorization versus runtime distinction, theme/locale/narrow containment and semantic heading hierarchy. No extra polling, business rule, execution permission or schema change. This supersedes FR-065 and the selected-only right-card layout in FR-067; FR-066 shipping disclosure and all control semantics remain.


### Compact risk legend

- **FR-083**: The instrument legend MUST occupy one compact centered row on desktop, retaining all four risk labels/swatches including Unclassified. Move the existing share-of-open-work and evaluated-scope explanation behind a labelled Info disclosure, closed initially and keyboard operable. Preserve exact copy; missing assessment must never imply green. The closed footer is at most 38px high on desktop, and may wrap on narrow screens. Explanation is bounded within the instrument section, readable in four languages/both themes, closes with Escape restoring its summary focus, and changes no analysis selection, URL/history, viewport or business state. No data/read/control change.
