# Research: enterprise shipping and case control

**Date**: 2026-10-06
**Language**: English
**Method**: Read-only repository inspection, including two focused research agents required by the planning skill. No business mutations, external provider work or runtime tests.

## Handover observation

**Decision**: New shared quantity-aware domain/read interpretation, not a renamed dispatch KPI.
**Evidence**: `db/core.py` ShipmentEvent records attributed `handed_over`, nullable occurred_at, package/shipment scope and source. `services/shipments.py` excludes MovementCorrection and ShipmentEventSupersession. `domain/shipments.py:current_observations` derives physical dispatch/external delivery, not complete cohort handover.
**Rationale**: Label/announcement/stock exit cannot prove carrier handover; duplicate events do not add quantities.
**Alternatives rejected**: Count event rows, rename dispatch_rate_percent, substitute ingestion time or call detail per order.

## Missing planning inputs

**Decision**: Three proposed source-backed input tables with a separate schema-approval gate.
**Evidence**: Commitment dates have generic delivery meaning. Spec 334/outbound_deliveries retain booked delivery slots, not dispatch targets. Location has hierarchy but no site designation/zone. CompanyTimeZone supplies the company business-day zone. No shipping completion capacity, carrier cut-off or forecast policy exists.
**Rationale**: Populated SC-001/005 requires explicit plan inputs; keys/times/quantities/units are repeatedly selected/joined/calculated. Direct Location scope avoids a new site hierarchy; requirement completion times avoid a stored curve table.
**Alternatives rejected**: Treat arrival slots as shipping cut-offs; generic Fact text/raw JSON as unvalidated forecast authority; fabricate default targets; persist forecast results.

## Forecast policy

**Decision**: Propose completion-slot-v1, explained in [shipping contract](contracts/shipping.md).
**Rationale**: Explicit accepted completion-slot budgets for the declared work mix, known readiness, current plan and confirmation evidence make units/limits reviewable. Multi-site work is aggregated before company completion. Requested collection is not confirmed capacity.
**Alternatives rejected**: AI-invented capacity, intake-based extrapolation, assume packages equal orders, infer future stock arrivals or workforce.
**Approval state**: Proposed. Earlier product-scope approval does not approve this model or schema.

## Existing control and missing read depth

**Decision**: Reuse operational_cases controls, add a new filtered register and derive attribution/evidence.
**Evidence**: Existing list caps a page at 100 and lacks ownership filter/full count. Explanation has takeover_user_id without takeover time/decision. The exact control revision BusinessEvent links a ChangeProposal with decision time/actor/reason. Action explanations need bounded existing review/receipt enrichment. Web reason field exists but current frontend does not submit it.
**Alternatives rejected**: Filter the first page, duplicate mutable takeover timestamps, expand case scope, generate next-check times or equate executed with delivery.

## Additive UI and authorization

**Decision**: /app/cockpit, default-off server capability, safe namespaced return context, on-demand chat.
**Evidence**: routing.ts owns destinations/serialization/company reset. Shell opens chat at desktop width and persists it. OrdersPage/Inspector have document-case detail. Chat handoff uses business records; CaseAssistant expects a commitment ID. Engine Room business endpoint is owner-only; case controls allow active members and adoption is confirmed owner-only.
**Alternatives rejected**: Separate app/account model, wholesale replacement, widened telemetry router, platform-admin control bypass, browser-history-only return context or passing case IDs as commitments.

## Scale and proof

**Decision**: New cohort-bounded batched read; aggregate before pagination and measure the declared workload.
**Evidence**: Current business_performance overview reads broad history and caps example rows at 200. Test strategy uses isolated PostgreSQL and fixture-backed browser scripts; canonical shipment/case/DST regressions already exist.
**Alternatives rejected**: Per-order explanation loops, capped totals, stale cache authority and a revenue-based scaling claim.

## All-day observation clarification

**Decision**: Make the owner's 2026-10-06 clarification a first-increment story, with a five-second foreground read lifecycle, stable inspection and bounded rolling recorded-business activity. See [live contract](contracts/live-observation.md).
**Evidence**: `BusinessLive.tsx` currently polls at five seconds with a busy guard; `HomePulse.tsx` uses ten-second visible polling, eight-second aborts and visible-tab resume. `LiveCharts.tsx` renders rolling technical interaction series. `services/activity_volume.py` supplies canonical first-recorded-entity classification/deduplication and recording-time coverage; its current 30-minute buckets cannot provide the requested short-term live window.
**Rationale**: Reuse canonical business-activity meaning in a short-window read; preserve daily shipping meaning, time/coverage truth and current control reviews. Existing activity and runtime availability remain distinct. Reads need no schema or new scheduler.
**Proof required**: Ten-second healthy commit-to-display under ten observers, deterministic eight-hour lifecycle checks and a separate eight-hour real-time soak before a pilot. Existing polling is reusable evidence of mechanics, not proof of these new acceptance criteria.

## Named Agent/access overview clarification

**Decision**: Add FR-024/C25 as a compact primary-surface overview, based on existing access/client records, without a new Agent registration or heartbeat system.
**Evidence**: `MCPAccess.tsx` already displays manual token names, last-used times and interaction links. `services/mcp_authorization.py:_grant_view` exposes recorded client name, effective access state and last use; `company_grants` enforces owner access. `web/api.py:get_ai_configuration` also requires company owner. `services/interactions.py:_actor` attributes observed calls to exact manual token IDs, not names. The `external_agent_runtime` capability explicitly reports visibility outside Reality.
**Boundary**: Grants/tokens can identify access records but not a unique external process, mission or current execution. Missing OAuth operation attribution remains unknown. Preserve owner disclosure and sanitize the read; no secret material, wider member telemetry, registration writes or runtime-state inference is introduced.

## Outcome

Technical unknowns have concrete proposed contracts, not runtime workarounds. The remaining authorization gate is the source-input/schema and forecast policy. An unavailable-only shell cannot satisfy the fully populated shipping story.


## Current-main integration note (2026-10-06)

The evidence above describes the original design baseline. Spec 377 on current
main supersedes legacy owner activation with default operational coordination.
The cockpit preserves that contract: register existing cases without CaseAdoption,
expose canonical platform reconciliation readiness and keep reads side-effect-free.
Migration 0146 follows current-main 0145; the original numbering is historical.
