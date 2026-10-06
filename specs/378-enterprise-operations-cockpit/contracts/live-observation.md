# Proposed all-day live observation contract

**Language**: English
**Status**: Owner-provided product clarification on 2026-10-06; planned implementation, not runtime evidence. The owner subsequently approved the shipping schema/model and these clarifications on 2026-10-06; runtime proof remains pending.
**Requirements**: FR-021–024, US5, SC-007.

## Operational surface

The cockpit is intended to remain open throughout a working day. Shipping by end of day stays the primary performance panel; its daily plan, confirmed handovers, forecast, current observation and site breakdown update in place. A compact rolling activity graph and recent-event stream make recorded company activity visible alongside it. The existing technical Live monitor remains reachable through Inspector.

Activity is an additional observation, not a substitute for shipping performance. Its default window is 15 minutes, with 5/15/60-minute choices and UTC-aligned 60-second buckets. Use the existing Home activity classification and first-recorded-entity deduplication: orders, other documents, reservations and movements. Label counts as recorded entities, never shipments, completed cases or successful agent actions. Full-result aggregation precedes any event-list limit; repeated processing does not multiply an entity's count.

The graph is company-wide and labeled accordingly, independently of the shipping-site selector. Coverage begins at company creation; the first and current buckets disclose partial coverage. Event recording time determines the activity window; original business occurrence time is shown separately when relevant. Imported historical evidence may be newly recorded today without claiming the business happened today. Confirmed shipping continues to use the applicable effective handover occurrence time under FR-005.

Recent activity shows up to 50 canonical event identities with links to existing event/object Inspector paths. Existing bounded, case-linked agent responses may be shown separately with their actual proposal/receipt and outcome states. Do not infer an Agent actor from an agent-owned case or generate processing/decision narratives. Actor attribution and currently executing work require actual recorded execution evidence. A label or newly recorded movement alone does not claim carrier handover.

## Named Agent and access overview

The owner additionally requested visibility of the named Agents/accesses contributing to the company. Show a compact "Agents & connections" region adjacent to recent activity, with at most six initial rows and an explicit paged view of all permitted matching records (maximum 50 rows per page). It must fit alongside the primary shipping performance without displacing that panel. Refresh through the same bounded live lifecycle; preserve expanded detail and selected identity.

Initial coverage comprises named manual MCP access records and company-authorized OAuth client grants. A row shows its recorded display name, connection kind, current effective access state, exact last-used time/age and the latest attributable operation when available. Configured tool permissions may be inspected as permissions; they are not a business mission, assignment, execution mandate or proof of action. Show a business case/reference only when an actual same-company execution or business-event link establishes it. Do not infer specialization from a token name or its allowlist.

Use credential-kind-qualified opaque identities, keeping distinct credentials/grants separate even if names match. Label complete counts as access/connection records, not unique Agents or continuously connected processes. OAuth client names and manual names are recorded labels, not verified person/runtime identities. Names are escaped display text. A shared credential cannot establish which individual external Agent used it. Never assign manual-token interactions to an OAuth grant, or another same-named client, without an exact recorded identity link.

State meanings are explicit:

- **Authorized access**: The existing admission/grant/token contract currently allows access; registration or configuration alone does not establish a live connection.
- **Last used**: The latest recorded credential/grant use, with its timestamp. A recent request does not establish continuous work or successful business completion.
- **Observed action**: An exactly attributable recorded tool operation or execution, with time and observed outcome. A failed request retains its failure; an accepted proposal is not executed work.
- **Working now / connected now**: Only a fresh authoritative runtime/session observation could support these labels. Initial Reality credential/grant and completed-interaction data do not provide that proof, so current external runtime state is explicitly unknown. Missing or old evidence must not become disconnected, stopped or idle.
- **Inactive/revoked access**: Preserve the effective authorization reason; do not claim that revocation stops an external process or cancels already-started actions.

Reuse current company-owner visibility for the full credential/client inventory and owner-only technical interactions. A member cockpit can still load shipping and business activity; it displays an unavailable/restricted Agent panel without leaking names, counts or action metadata. Do not silently broaden settings or telemetry access. Any later member-level sanitized roster or external heartbeat/mission protocol needs its own explicit reviewed scope. The main view is read-only; settings management remains in existing reviewed paths. Returned data omits credentials, prefixes/hashes, approval material and unrelated user email/profile details.

The shared service supplies complete eligible totals and keyset-paged rows from the current company, filtering/rechecking effective access state before counting. Default active-access view labels its scope; inactive/revoked records remain available through an explicit filter rather than silently appearing as running Agents. A never-used record shows "No use recorded". If OAuth is disabled or its observation coverage is unavailable, distinguish that from a known empty inventory. Access loss, refresh failure and company switching clear or age this panel under the same lifecycle rules as other reads.

Proof covers duplicate names, several grants for one client, shared credentials, never-used/revoked/inactive records, failed operations, missing OAuth attribution, more than one page, restricted non-owner and foreign-company access, no secrets in the read payload, stale/resume behavior and no fabricated current execution. Registry reads neither register clients, update last-use timestamps nor perform any business mutation.

## Refresh and observation lifecycle

- Refresh a visible cockpit every five seconds while healthy, with an immediate initial read and visible-tab resume read. Newly committed changes appear within ten seconds in healthy SC-004 acceptance conditions. This is a read/display target, not a promise about upstream intake or execution latency.
- Use one active refresh cycle per company/filter context, with no overlapping reads. Abort stalled reads after eight seconds and cancel reads/timers on context change or unmount. Discard obsolete responses even if cancellation arrives late.
- Suspend periodic reads while hidden. On resume, refresh current company/day/filter state immediately; retained data stays visibly aged until successful. A browser-local time marker may advance but does not extend observed coverage.
- On refresh failure retain last successful values marked stale, show their observation time, and represent later elapsed time as unknown. Retry delays are 5, 10, 20 then at most 30 seconds; reset after success. Availability/readiness retains the existing separate contract and cannot be inferred from these reads.
- Auth loss clears company data and pending reads; disabled capability follows the existing permitted-route fallback. Fast company switches cannot merge snapshots, events or pending reviews.
- Retain at most 61 one-minute graph buckets (including partial boundary buckets for the 60-minute window), 50 recent events and one inspected history page of at most 50 rows. Replace/deduplicate buffers rather than append indefinitely; inspect full history through existing paged Inspector navigation. Complete totals are server aggregates, never buffer counts.

This browser read lifecycle introduces no scheduled job, background timer service, business event or stored live-status authority. Only the existing scheduler/worker performs scheduled business work.

## Stable inspection and control

Refresh patches values in place, retaining scroll, selected rows, open records, filters and unsent contextual-chat input. Stable event IDs anchor inspected history. While history is inspected or automatic following is paused, accumulate a bounded unseen-items indication; explicit resume jumps to the latest available page. Overflow is indicated without pretending every unseen item is retained. Pausing activity-following affects only the stream viewport; metrics continue refreshing and the Agent continues working.

Open takeover/handback reviews remain visible. New observations cannot dismiss a review, replace its exact reviewed payload or confirm it. Changed authority, control revision or business meaning requires the existing fresh-review/refusal path before execution. Unchanged reviews remain usable. Case responsibility and the human-owned register update from their canonical current reads.

URL state distinguishes `cockpit_day=today` from a specific ISO date. Resolve Today against CompanyTimeZone at every successful snapshot, disclose rollover and missing new-day plan coverage, and retain site/filter choices. A pinned date remains pinned. A rolling live panel is always labeled with its current window, independently of a historic shipping date. Rollover must not reset an open record, silently alter a control review or reinterpret a historical business day.

## Proof

Failing service tests prove classification/deduplication, recording-time meaning, complete totals, coverage and tenant isolation without writes. Fake-clock browser proof covers real fixture changes, advancing quiet windows, failed/recovered reads, hidden-tab resume, rapid company switches, historic versus Today dates, DST/day rollover, stable scroll/chat/reviews and bounded eight-hour operation. Confirm no confirmation/control endpoint is called by refreshing or presentation-only following.

Measure ten observers refreshing at this cadence against SC-004's full workload, with concurrent actual fixture changes. Report display latency, query budget, requests and sustained response timing; satisfy the ten-second healthy-display target without reducing the cohort. Before a pilot, record a separate eight-hour real-time soak including retained state and bounded memory/DOM/request behavior. Neither deterministic elapsed time nor a short preview is evidence of that soak.
