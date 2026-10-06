# Reality Company Simulator

## Live company with an external code agent (spec 376)

Use the [live startup and operating guide](../../packages/reality-core/scenarios/company_simulator/LIVE.md). This is a retained PostgreSQL company, paced by the existing scheduler/worker, with a simulator-local inbox/outbox and a separate live console. The external Claude/Codex agent uses ordinary Reality tools; no built-in policy acts for it. The default target is 180 new orders/hour for 72 hours (150–200/hour and 96 hours are configurable). These are configured targets; a multi-day throughput trial and an actual external-model trial have not been measured.

The live console offers **Trigger an event → Preview → Release** for customer/supplier mail, new orders, delivery enquiries, cancellations and return requests. Preview creates no records. A released email alone does not book stock, money or an order. Every manual release has its own immutable identity and is counted separately. No real email integration or open desktop is required.

The commands below this section remain **finite regressions and artifact replay**. They do not start this sustained runtime. The old replay Play button controls viewing only.


## Separate simulator spectator (spec 375)

From `packages/reality-core`, run `../../.venv/bin/python -m scenarios.company_simulator.viewer`
and open http://127.0.0.1:8765. Select a recorded run to follow the company timeline,
customer messages, supplier business activity, delivery goals and last independent checkpoint.
The viewer is local, read-only and separate from Reality's product UI; no database is needed.
It refreshes every five seconds and follows new atomic spectator snapshots.

Only actually recorded correspondence is shown. The complete v2 profile includes customer follow-ups, supplier notices and simulated baseline-agent replies; custom replies are unsent drafts. Shopify/operational and historical journals retain their original coverage. Actions never stand in
for mail send/approval evidence. [Viewer guide](../../packages/reality-core/scenarios/company_simulator/viewer/README.md).

Established working name: **Reality Firmensimulator**. The owner clarified this
direction on 2026-10-05. There is one simulation engine with two company profiles,
not separately maintained day, week and month simulators.

Status: the finite reactive company and synthetic Shopify profiles are implemented
under specs 373/374. The [reference-week replay](reality-reference-week.md) remains
a separate fixed-action core regression. The broader direction below includes future
extensions; durable continuation, real-time pacing and unbounded autonomous dialogue remain
outside the current finite controller. Spec374 FR-009 adds finite local customer/supplier correspondence; spec375 provides the separate spectator UI.

## What the owner wants to test

An independently simulated outside world supplies customers, supplier offers and
physical evidence. Different operators manage the same starting company and try to
meet the same business objectives. The principal customer objective is the correct
item and quantity delivered to the correct recipient and destination by the agreed
deadline. Correct dispatch alone is not proof of customer receipt.

Run duration is configuration: a day for debugging, a week for a shorter comparison,
or roughly 30 days for the broader business portfolio. Longer runs use versioned
episode identities and retain pending promises, stock and financial balances across
episode boundaries. They never reset stock merely because another month starts.
Repeat runs for operator comparison start fresh; continued runs retain their company.
Initially use a bounded run with explicit limits, not an unbounded producer.

## Two profiles, one engine

| Profile | External world and inputs | Additional business objectives |
| --- | --- | --- |
| General company | Customer orders, changes, cancellations, correspondence; supplier terms and deliveries; warehouse/carrier evidence; invoices and stated bank movements | Delivery service, procurement, stock and financial reconciliation |
| Shopify company | The same physical world, with authentic-shaped simulated Shopify orders and related payment, refund and payout evidence derived from examined original examples | Order/payment/payout association, fees, refunds, provider clearing and stated bank deposit reconciliation |

The Shopify profile is a complete company profile, not a payout-only test. Payouts
alone cannot establish customer delivery, invoice or payment correctness. Shopify
format coverage must be determined by examining original anonymized payloads/exports;
no such examples have been supplied in this conversation. Retain original structure,
identities, currency, totals and timezone meaning. Author synthetic fixture copies
with a documented relationship to those examples, not guessed provider fields.

The existing `src/reality/integrations/shopify/` owns order interpretation and the
existing `services/payouts.py` owns normalized provider statement booking. Their
existence does not prove a native Shopify payout connector or every provider event
is supported. Analyse the exact source-to-service boundary before implementing it.
A real Shopify shop connection is a separate later transport choice; the first
Shopify profile must run without a real shop or actual outgoing payments/email.

## Responsibilities and main rhythm

1. **World simulator:** releases the authored exogenous events and reacts to observed
   accepted operator actions. A supplier delivery requires a valid recorded purchase;
   carrier arrival requires an actual recorded dispatch. It never quietly purchases,
   reserves, invoices or ships for the operator to rescue a missed objective.
2. **Controller:** advances the simulation timeline, releases due external events,
   gives the selected operator a bounded opportunity to act, observes state, records
   checkpoints and continues. Supports pause/inspect and explicit resume only after
   durable episode/event identities and uncertain-outcome recovery are specified.
3. **Operator:** the Reality agent or another selected agent uses the same normal
   authenticated services/tools and approved authority scope. It sees only currently
   released evidence, supplier conditions and customer requirements; no future event
   schedule, private oracle or other operator's results.
4. **Observer/evaluator:** reads independently and uses deterministic arithmetic for
   reconciliation and deterministic criteria for customer objectives. It does not
   repair Reality or treat an operator's narration as evidence.

The simulator/controller/evaluator can be programs; they do not require additional
AI agents. Named operator agents still need existing explicit finite owner mandates
or supervised exact confirmations. A launch never creates authority implicitly.

Define the controller/world clock and the operator's real elapsed-time budget separately.
Compressed time is useful for repeatable comparisons; a paced run is useful for
watching operations. Neither implies that Reality's own clock supports virtual time.
Date-sensitive services and future-dated financial evidence must be examined and
specified before promising an accelerated financial month. Do not bypass validation
or fabricate transport evidence to achieve authored dates.

## Fixed goals, conditional consequences

Example: a customer orders ten lamps for a particular address, due Friday. The
world fixes the requirement, available suppliers, lead times, purchase quantities,
prices and any authored disruption. The operator chooses when and how to procure,
reserve and dispatch. A purchase actually placed on Wednesday receives its simulated
supplier response and arrival according to those rules, not on a fixed date that
assumes Monday procurement.

Use a finite conditional rule table and stable event identities. Responses for the
same accepted action and world state must repeat; operator speed must not alter a
random event stream arbitrarily. Different valid action paths may produce different
correct closing stocks and costs. Do not grade all operators against the reference
week's one prescribed closing balance.

## Two independent results

| Result | What is measured | What a failure means |
| --- | --- | --- |
| Core correctness | Stock from independently retained physical events, live commitments and cancellations, allocations, invoice/payment/credit and provider/bank conservation; provenance, tenant scope and no duplicates | Reality or its intake/projection boundary may have booked or exposed incorrect state |
| Business/operator performance | Quantity and item delivered by destination/deadline; shortages and lateness; completed procurement; unresolved cases; cost according to explicitly stated valuation evidence | The operator missed the objective even if every actual booking is correct |

For core correctness, derive the oracle from the world's original evidence and
verified command receipts, not from Reality's displayed totals. Keep incoming source,
prepared/approved proposal, command receipt and independently verified effect distinct.
A received but unapproved source must not be treated as accepted business truth.

Wrong or late operator choices are recorded and the game continues where safe. An
unexplained booking discrepancy or uncertain mutation outcome pauses affected work
for diagnosis; it must not be retried or repaired silently. End-of-run reports mark
every objective as met, missed, blocked or unknown, retaining the underlying evidence.

## Business portfolio for the first broader episode

The following is a scope checklist, not an invented overall coverage percentage.
Each case needs exact source inputs, conditional outcomes, objectives and assertions
before it is enabled in a profile.

| Case family | Required observable outcomes |
| --- | --- |
| Normal fulfillment | Correct item/quantity, recipient/address and deadline; separate dispatch and arrival evidence |
| Shortage and procurement | Supplier lead times, minimum/multiple constraints where supported; purchase created before any dependent receipt |
| Partial and delayed delivery | Partial supplier receipt and customer dispatch, outstanding quantities and changed risk |
| Customer change and cancellation | Changes before/after partial dispatch; correct effective promise and released allocation |
| Return and exchange | Announced and arrived quantities, condition/location, credit or replacement explicitly requested |
| Invoicing and payment | Stated invoice amounts; partial and combined receipts; exact allocation and open amounts |
| Credit and refund | Source-linked credit, refund, remaining claim/credit and separate physical return |
| Physical corrections | Count difference, transfer, wrong/failed delivery and append-only correction with retained reason |
| Recovery and competition | Duplicate source/confirmation, stale review, bounded concurrent demand, interrupted action and safe reconciliation |
| Shopify finance | Payment versus payout, fees/refunds/chargebacks when present in supported examples, clearing balance and actual bank deposit |

The portfolio must include legitimate incomplete cases at episode end. A company
with open supplier orders or unpaid invoices is not inherently corrupt or failed.
Only the explicit goals and obligations determine whether the operator missed one.

## Proposed source layout

```text
packages/reality-core/scenarios/
  harness/                     # Existing replay controller/observer/reporting
  company_simulator/           # Future reactive world and operator orchestration
    README.md
    controller.py
    world.py
    evaluation.py
    profiles/
      general_company/
        scenario.yaml          # Initial state, external events, response rules, goals
        fixtures/
      shopify_company/
        scenario.yaml
        fixtures/              # Reviewed synthetic Shopify source examples
  reference_week/              # Existing fixed-action kernel regression
```

Reuse existing harness components where their contracts fit; do not make the fixed
replay secretly become an agent game. New runtime paths above are proposed, not
present callable modules. Keep business interpretation in the existing Reality
services/integrations. Runtime reports belong in ignored
`artifacts/company_simulator/<run-id>/`, with separate world evidence, accepted actions,
core-check results and operator scores. No business truth is written to artifact files
as a replacement for existing Sources and Reality records.

## Next implementation sequence

1. Specify the reactive world/action boundary, customer goal records, clock policy,
   agent visibility, finite authority and two-part evaluation. Reuse the existing
   reference cases as stories, not mandatory operator actions.
2. Build one independently runnable general-company episode: normal order, shortage,
   actual purchase-dependent receipt, dispatch/arrival and one financial settlement.
   Compare a successful scripted operator with one that deliberately misses a deadline.
3. Expand the authored portfolio to a bounded approximately 30-day episode with
   explicit per-case goals and exact reconciliation checks. Add pause/resume and
   longer continuation only after their state/recovery contracts are proved.
4. Examine original Shopify order/payment/refund/payout examples, document which
   links and amounts they actually state, and implement the second profile using
   the same world/controller/evaluation. No guessed native Shopify mapping.

This clarification supersedes the earlier idea of separate week/month scenarios
as the main product and of grading agents by a single fixed action sequence.
It does not invalidate the existing reference-week booking test or its verification.

## First executable operational slice (spec 373)

The shared simulator now has a bounded 1–30 day general-company profile with twelve customer requests, two items and demand-dependent purchasing. Built-in prompt, delayed and idle policies receive copied released observations. Daily independent expectations cover stock, reservations, open quantities, per-order fulfillment/source amounts and order counts. Business deadline outcomes are separate from core correctness. Execution errors are unknown outcomes and are never automatically retried.

See [launch instructions and coverage limits](../../packages/reality-core/scenarios/company_simulator/README.md). Financial scenarios, destination/package verification, richer exceptions and arbitrary AI enrollment remain future slices. The Shopify profile is reserved without invented native data.

## Extended executable company month (spec 374)

The default profile now models the trading-company month through warehouse, delivery and gross financial settlement. The central script is `packages/reality-core/scenarios/company_simulator/profiles/general_company/complete.yaml`; the explicitly synthetic Shopify variant is beside it under `profiles/shopify_company/`. [Launch, file map, coverage and supervised external-operator interface](../../packages/reality-core/scenarios/company_simulator/README.md).

The extended profile uses an ordinary named local test company because existing Sandbox policy refuses outbound delivery plans. It preserves that policy and requires normal active-owner admission. No external service is connected. Original small Sandbox and fixed day/week proofs remain separate regression profiles.

Source-stated invoices, partial payments, supplier settlement, physical returns, credits/refunds, package destination evidence, partial dispatch/cancellation, carrier failure/re-dispatch, stock counts and transfers now have independent checkpoints. Delayed/idle/wrong-destination policies are graded separately from core correctness. Coverage inventory records what each run actually exercised. Live policy callables require exact supervised approval; the repository does not choose a model provider.

The bounded test-company model does not claim VAT/payroll/regulatory or real transport coverage. Native Shopify payout formats still need authentic original evidence. Durable unbounded running/resume remains outside this controller.

[Readable central month protocol with selected fixed prompt checkpoints](company-simulator-protocol.md) complements the authoritative YAML and the independent dynamic oracle. It also distinguishes unallocated known customer funds from provider lines with an unknown customer reference.


## Essential live-order completeness (spec 379)

Future automatic live orders explicitly state the world's EUR 10 unit quotation, one actual order/release instant and its company-local document day. Normal services retain those statements so the customer-order register has its source-backed date. A manual composer amount without a unit quotation remains an unknown price, never a reverse calculation. Existing orders/Sources are not rewritten. See the [shared completeness rules](../features/intake-completeness.md).
