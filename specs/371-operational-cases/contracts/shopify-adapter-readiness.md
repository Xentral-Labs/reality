# Shopify adapter and repair acceptance plan

Status: proposed next feature, not implemented or live-qualified. The owner requested this concrete follow-up after local verification of operational cases. Spec impact: planning only; a separately numbered, reviewed adapter specification must precede observable transport or schema changes.

## Responsibility and order-change boundary

Shopify supplies the order and its changes. Reality supplies derived operational work and exact approved decisions. The warehouse/carrier supplies the actual dispatch outcome. A webhook alone proves neither accepted business changes nor physical dispatch.

| Situation | Required behavior |
|---|---|
| New accepted order | The canonical intake transaction creates its fulfillment case with the commitments. Raw capture does not create an accepted goal. |
| Customer edits before dispatch commitment | Capture the new version, stop dependent work until interpretation/acceptance, invalidate previous reviews and prepare current work. |
| Worker queued before manual takeover | Recheck case control and current facts at child execution; keep the old approval obsolete. |
| Customer fixes a mistake in Shopify | Capture and accept the repair through ordinary intake. Do not require the customer to restate the changed business facts in chat. |
| Customer intends to replace/cancel Reality's pending plan | Explicitly take over the case. An external edit changes business facts; it does not establish that the member wants all automated responsibility stopped. |
| Dispatch claim exists, outcome unknown | Show unresolved execution, reconcile using the exact provider operation reference and prohibit automatic redispatch or handback. |
| Physical dispatch already confirmed | Preserve the shipment fact. An order edit cannot recall the parcel; handle supported correction, interception or return as a separate reviewed action. |

The proposed change cutoff is the warehouse/provider's authoritative acceptance of the dispatch instruction. Before that point, accept supported order changes and rebuild the plan. After it, offer cancellation/interception only when the provider confirms it is still possible. Mark physical shipment complete only from verified outcome evidence. Shopify's editable order screen is not the authority for whether a parcel can still be stopped.

## Capture and freshness work package

Inspect current `services/shopify_intake.py`, `services/shop_order_changes.py`, `services/shop_refunds.py`, `services/intake.py` and Source stream admission before specifying the transport. Existing helpers process retained payloads; they do not prove a live webhook installation, full historical capture or provider API coverage.

1. Specify authenticated installation, shop-to-tenant mapping, least required scopes, uninstall/revocation and webhook signature validation. Reject mismatched shops before business interpretation.
2. Preserve raw payloads losslessly, including provider IDs, supplied correlation and timestamps. Deduplicate verified deliveries without heuristically merging different business versions or goals.
3. Define the supported order/change/cancellation/fulfillment/return/refund capture surface from the selected Shopify API version. Delivery time is not business version ordering: delayed old notifications must not replace newer accepted state.
4. Acknowledge only durable capture. Use shared queued jobs for retries, authoritative API retrieval and bounded reconciliation/backfill. No provider calls in the database-only case consumer.
5. Qualify coverage explicitly: captured boundary, supported fields and event families, retrieval failures, unresolved evidence and revoked access. Silence or an empty queue does not prove freshness. Block dependent work on known gaps; keep health visible.
6. Reuse normal Source → Evidence → Reality acceptance. A supported, current automatic mandate may accept changes; unknown changes, unsupported fields with operational impact or conflicting versions require review. Source arrival alone never approves effects.

## Dispatch work package

Use existing proposal review, execution claim and recovery contracts in `services/delivery_actions.py`, `services/outbound_deliveries.py`, `services/shipments.py` and `tools/application.py`.

1. Before claiming dispatch, fetch current authoritative order/fulfillment eligibility. Capture new evidence, accept its supported meaning and compare exact business prerequisites, case revision, quantities, address, cancellation and holds against the prepared instruction. A mismatch refuses the old instruction and requires fresh review.
2. A final reread alone leaves a race with an external edit. Determine whether the selected fulfillment provider offers version fencing, a cancellable preparation stage or an exclusive release mechanism. Do not describe an unfenced read-then-send as atomic. If no mechanism can enforce the promised cutoff, constrain automation to a supervised release policy and record that limitation.
3. Claim only the exact approved instruction under existing current authority. Reuse one operation/idempotency key across a safe retry, with exact payload matching. Do not hold database locks across network calls.
4. Separate claim, provider acceptance and actual dispatch. Persist the real response/evidence, use bounded shared reconciliation for timeouts, and prohibit blind resend when the outcome is unknown.
5. Manual takeover blocks future starts; it does not cancel an already accepted provider instruction. Request provider cancellation as its own reviewed operation and wait for its actual result.

## Pilot repair journey

1. Use a dedicated test shop and isolated company. Enable only explicitly supported new work; no implicit takeover of old orders or autonomous refund/payout capability.
2. Accept a two-line order and prepare delivery. Introduce a supported address or quantity mistake before dispatch.
3. The operator opens the case, confirms takeover, edits Shopify and does not repeat the facts in Reality chat.
4. Verify durable capture, newer-version recognition and normal acceptance. Show the same fulfillment case, repaired current facts, obsolete original plan and no additional shipment.
5. Preview handback. Unaccepted evidence, access failure and unknown executing actions must block it. Confirm the exact current review after resolution.
6. Prepare a new plan and release once. Verify actual provider outcome and the current order/case explanation. The old plan remains unusable after handback.

Also prove duplicate/reordered/delayed/missing notifications; correction during queued work; correction between final read and release; lost HTTP response after provider acceptance; repeated operator clicks; worker restart; access revocation; partial dispatch; post-dispatch edit; independent return; and cross-shop/cross-tenant IDs. Test the race using a controlled provider stub before the sandbox provider acceptance run.

## Delivery sequence and release evidence

1. Write a separately numbered adapter spec with supported Shopify API/version and fulfillment-provider boundary, exact permission/mandate model, cutoff semantics and acceptance tests. Inventory available fencing/cancellation behavior before promising autonomy.
2. Implement and prove durable authenticated capture plus bounded reconciliation through the shared queue.
3. Implement and prove authoritative pre-dispatch review, exact provider claim and outcome recovery.
4. Run the complete repair journey and failure injection in the test shop. Retain capture/review/claim/outcome evidence; success of the internal case tests is not a substitute.
5. Start a supervised pilot with an identified operator and a documented manual dispatch fallback. Expand autonomous actions only after the specific capture and provider boundaries pass.

No test shop, Shopify credential, carrier transport, external schema expansion or deployment is created by this planning artifact.
