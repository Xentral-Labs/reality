# Shipping observations and forecast contract

**Language**: English
**Version**: Owner-approved `completion-slot-v1`, 2026-10-06; implementation verification pending.
**Inputs**: [Proposed source-backed model](../data-model.md).

## Cohort and observed basis

Select the company business day using CompanyTimeZone (default UTC), plus an optional exact dispatch Location. Accepted current plan statements define the shipping cohort and retain their explicitly stated company-day zone. A changed company zone that conflicts with the accepted plan's calendar context creates an unresolved coverage gap until review; it does not move planned work silently between dates. Do not substitute generic Commitment.due_at, outbound delivery slot, reservation location, event free text or source ingestion date.

Include required non-cancelled commitments even if they are now fulfilled; otherwise successful work would vanish from today's denominator. A quantity revision incompatible with the accepted requirement creates an explicit coverage gap. Empty known cohort is zero; absent planning evidence is unknown. Work without a plan/site remains discoverable as unassigned/unplanned work, without a fabricated shipping deadline.

One site-cohort work unit is `(order opaque ID, plan's day, dispatch location)`, containing all of that order's requirements in that scope. Company order counts deduplicate order IDs. A company order completes only when every applicable site-cohort unit completes; site counts therefore need not sum to the company count.

Return observation time, business-day/zone, selected location, current source/statement IDs, relevant-input fingerprint and data watermark. This is a current read basis, not a historical authority. Supporting-list reads re-evaluate current facts; changed basis returns new totals with `re_evaluated=true`, never silently mixes snapshots.

## Effective physical and handover coverage

- Read canonical commitment terms and exclude corrected original movements.
- Only compatible outbound customer-delivery contents linked to the requirement's commitment and actual declared stock-exit Location count for its physical coverage. Missing/incompatible linkage is a coverage gap, not guessed from tracking numbers.
- Movement → exact ShipmentPackage → Shipment is the shortest actual-content path. Unpackaged legacy movements retain physical meaning but cannot invent a consignment/handover.
- Exclude superseded ShipmentEvents. A shipment-wide handed_over observation covers compatible contents of that shipment; package-scoped observations cover only that package.
- Count each compatible movement quantity once, regardless of repeated reports. Sum effective covered quantities; do not multiply by event rows.
- Use attributed stated event time. Missing time, future/contradictory chronology, or unresolved conflicting handover times for the same content scope produces explicit incomplete timing. Do not choose recorded_at or a convenient report. Reconciliation uses existing correction/supersession mechanisms.
- A requirement completes when its entire current valid planned quantity is physically covered and has applicable handover coverage. Site-cohort order completion time is the latest requirement completion time. Company completion time is the latest applicable site completion.

Series uses cumulative completed order-work counts at returned UTC instants, displayed in the explicit day/zone. Completions before the selected day's start are disclosed as an opening baseline, not fabricated as events within the day. No confirmed series extends beyond observation time. A late-arriving observation with a valid older business time changes the current curve and basis; it does not become shipping at ingestion time.

## Soll

Each valid requirement's source-stated planned_handover_at provides its planned completion. Site-cohort and company planned completion use the latest applicable requirement/site time. Count complete planned units cumulatively at those instants. These counts are observations over stated input, not a recomputation of a separately stated source total. The v1 input has no externally stated target-total field to overwrite.

A daily deadline without planned times does not determine an hourly curve. Any required missing planned time makes the affected timed Soll incomplete/unavailable; retain the known daily cohort and explain the missing input. Do not interpolate a fictional plan from day start to day end.

## completion-slot-v1 baseline forecast

This deterministic scenario is an estimate, not a fulfillment promise, provider confirmation or learned probability. Its explicit assumptions are: the declared plan-specific capacity is reserved for the stated work mix; current ready work remains feasible; no unknown future stock/workforce/collection is added; completion pace is uniform within each accepted capacity window. Approved source values themselves are never changed to fit the model.

1. Evaluate actual site-cohort completions at the observation time. An unfinished unit is a candidate only if every remaining requirement is canonically ready, or its required physical contents already exited stock and are waiting for applicable handover, and no unresolved relevant source/execution uncertainty blocks it. Do not infer future readiness from a supplier promise or dispatch uncertainty.
2. Use only current confirmed non-overlapping capacity windows for the exact site/day/plan. Confirmation must explicitly support the completion-slot unit and work mix. Missing required baseline input makes forecast unavailable, not zero. An explicitly requested window is known unconfirmed capacity and contributes zero baseline capacity while its pending status is visible.
3. For a confirmed window, let B be its stated completion_slots for the full stated interval, s its starts_at, e its ends_at, c its collection_cutoff_at, and U the actual applicable site-cohort completions during `[s, min(observed_at, c)]`. Remaining total budget is `max(0, B-U)`; disclose if observations exceed the stated budget. An observed completion before s does not consume this window. Overlapping windows are refused to avoid counting a completion twice. At a shared boundary of adjacent confirmed windows, the earlier window owns that actual completion once.
4. At future t ≤ c, available remaining model slots are `min(max(0, B-U), floor(B * max(0, t-max(s, observed_at)) / (e-s)))`. This is read-time uniform-pace estimation, never a new stored capacity value. The denominator uses the original capacity interval: an earlier collection cut-off cannot compress the stated budget into a faster rate. B=0 is a known zero window. No capacity is assigned after c. Use Decimal/rational math, not binary floating quantities.
5. Sort candidate units by earliest still-outstanding dispatch deadline, then opaque order identity. Consume windows chronologically and assign predicted completion to the earliest instant with a remaining slot. Each site-cohort unit consumes one slot once; it is never equated to one package. Previously completed requirements keep their actual times.
6. A company order receives a projected completion only if all its required site-cohort units have an actual or projected completion. Take their latest time and deduplicate the order. Unknown site input makes the global forecast incomplete; show supported site results and the gap, not a precise company trajectory.
7. Start the future forecast at the actual observed cumulative count; visually distinguish it from confirmed progress and disclose that newly ready work, replenishment and requested extra collections are excluded. Forecast policy/source versions, window assumptions and supporting candidates are inspectable.

Eligibility changes and future outcomes can change a later forecast; the read does not reserve work, execute shipping or claim certainty. General package/labor/weighted-order scheduling requires a later reviewed policy version.

## Deadline risk and cut-offs

Evaluate individual still-outstanding requirement shipping deadlines, not customer arrival dates. A known blocker, no feasible confirmed slot before deadline or a projected completion after deadline produces explained risk for its affected order. If the needed plan/capacity basis is unknown, risk coverage is unknown and cannot be displayed as zero. Count unique orders per selected scope and disclose the current-day horizon. Do not relabel existing two-hour findings as the reference's 48-hour/value measure.

Display source-stated relevant site collection cut-offs with their meaning and site zone. Aggregate view keeps differing cut-offs distinct; no fabricated single global cut-off. A requested extra collection is a pending scenario input, not proof of executed transport or confirmed new capacity.

## Independent populated acceptance oracle

Use day 2026-10-06, company Europe/Berlin, observation 14:30, two explicit dispatch locations. Build accepted commitments, original planning Sources and actual movement/package/event records through shared services.

- Order A: one Venlo commitment, quantity 1, stated planned completion 14:00/deadline 16:00, fully physically shipped and handed over at 14:10.
- Order B: two Venlo requirements of quantity 1 each; the first has planned time 14:00 and actual handover 14:20, the second planned time 15:00 and is ready but unfinished. Both shipping deadlines are 15:30. It counts zero completed order-work units so far.
- Order C: one quantity-1 Venlo and one quantity-1 Leipzig requirement, both planned for 15:30/due 16:00, ready and unfinished. It is one company order and one unit at each site.
- Order D: one quantity-1 Leipzig requirement planned/due at 16:00; announcement/label only, no physical contents and an actual canonical delivery hold. It is not a handover or forecast-ready completion by the label alone.
- At 14:30, actual company handover count and timed Soll are each one. Company Soll is two at 15:00, three at 15:30 and four at 16:00. Venlo final Soll is three and Leipzig two; their overlap is C. Partial Order B is not actual-complete.
- Venlo confirmed window `[14:30,16:00]`, cut-off 16:00, two completion slots. Leipzig confirmed window `[14:30,16:00]`, cut-off 16:00, one completion slot. The assigned mix is explicitly confirmed in original source evidence. Due-order sort and source times make B complete at 15:15, C's Venlo unit at 16:00 and its Leipzig unit at 16:00. Company projected final count is three; C is not counted twice.
- In a separate extension, add ready Venlo Order E planned/due at 17:00 and a requested, non-overlapping window `[16:00,17:00]` with one slot. The new company Soll is five, but baseline forecast remains three; confirming that exact window in a reviewed plan revision makes E project at 17:00 and baseline four. Add duplicate handover evidence for A: actual count remains one. An effective conflicting handover time without reconciliation makes affected timing/coverage incomplete; a superseded record is excluded, never a new confirmed shipping event.
- Add separate cancellation, late import, foreign source, multi-page supporting-order and DST stories. Expected values must be hard-coded/calculated independently of the production evaluator.

This oracle proves calculation semantics only; it does not claim real carrier capacity or full-company autonomy.

Fingerprint format `shipping-inputs-v2` hashes every canonical frozen fulfillment-readiness field for every included requirement, preserving exact values and ordering. The disclosed first-fifty readiness preview and every selected supporting/deviation order retain the existing readable evidence shape. Unused readable dictionaries are not materialized; complete calculation and fingerprint inputs remain unsampled.
