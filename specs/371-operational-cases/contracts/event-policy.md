# Initial event-to-case contract

Draft; names below are existing event types unless explicitly identified as future capability.

| Trigger | Resolver | Classification |
|---|---|---|
| `commitment.created` | Customer delivery commitment → accepted order | Ensure fulfillment case only for outstanding work; ignore other commitment types |
| `document.recorded` / `source_record.interpreted` | Accepted sales order → customer delivery commitments | Ensure/match fulfillment; no duplicate if commitment events also exist |
| `commitment.revised`, `commitment.cancelled`, `commitment.fulfilled`, `commitment.held`, `commitment.hold_released` | Commitment → order case | Reevaluate existing goal/work; no per-event new case |
| `movement.recorded`, `movement.corrected` | Movement → commitment → order/return context | Reevaluate affected cases; do not create unrelated warehouse cases |
| `document_line.item_assigned` | Line → order → newly created customer commitment | Ensure/match outstanding fulfillment, including formerly unassigned line |
| `return.announced` | Accepted ReturnAnnouncement | Ensure separate return goal; link original fulfillment context if present |
| `return.announcement_withdrawn` | Existing announcement/case | Reevaluate abandonment and unsettled actions; never pretend physical execution reversed |
| `shipment.notice_recorded`, `shipment.event_recorded`, `shipment.event_superseded` | Shipment authoritative commitment associations | Reevaluate only known related cases; unsupported associations visible as gaps |
| Accepted refund evidence through `source_record.interpreted` or `document.recorded` | Refund → supported order/return/intent references | Settle/reconcile matched intent; no payout goal from notification alone |
| Explicit authorized refund intent (future capability if no existing anchor) | Exact intent identity | Ensure refund case; requires separately supported authoritative intent path |
| `source_record.received` | SourceStream → already linked order/return contexts | Mark relevant freshness unresolved until accepted/settled; never apply raw payload as business truth |
| Product/location/customer creation | No outstanding initial goal | No new case |
| `operational_case.*` (new audit vocabulary) | Case | No business-goal creation recursion |

Policy resolvers and completion predicates query current authoritative services. No arbitrary correlation-ID grouping. Unknown events have no case side effect; governed actions require declared applicability regardless of event classification.

## Controls and reads

Proposed shared operations: `operational_case_list`, `operational_case_explain`, `operational_case_takeover`, `operational_case_handback_preview`, `operational_case_handback_confirm`, `operational_case_adoption_preview/confirm`. Inputs use opaque IDs, expected revisions and request keys. Confirmation reuses existing canonical proposal review/decision patterns.

Active members may take over/hand back a selected case; owner confirms adoption. Business-effect permissions remain action-specific. Built-in Chat proposes controls for human review; external MCP requires exact tool/scope permission and existing principal/business authority. Human control never grants an agent a mandate.

Explain output includes stable goal/root, control revision, actual responsibility, observed goal state, owned proposals and obsolescence reasons, related cases, unsettled execution, source coverage and consumer lag. All links preserve tenant scope. Mutation failures have safe coded reasons for stale review, human ownership, unresolved effect, coverage gap, missing binding and forbidden action. Unsupported capabilities are labeled unavailable, not ready.

## External correlation preservation

Caller-supplied correlation_id remains external tracing metadata. Preserve it unchanged in supported ingress/action/event/response paths; do not substitute case_id or action_id. Absent external values remain absent. Case assignment follows opaque authoritative object links, never correlation equality. Test multiple external correlations within a case and one external correlation across cases. Historical events are not rewritten.

## Discovery and existing response compatibility

The first-slice case list provides bounded opaque-ID pagination; goal/ownership filtering remains a future read enhancement; object discovery accepts supported record type and opaque object ID. Reads expose `case_ids: []` for unadopted/history, or all matching IDs for associated work. Case detail uses `case_id`; multi-case proposal/receipt read envelopes return every directly affected case without rewriting immutable execution receipts. Associations are canonical service output, never agent-authored ownership. Existing response fields and object inputs retain their meanings. UI provides copyable ID and manual takeover/review/handback, with explicit unsettled-effect explanations.

## Broader candidate list

[Case candidates](case-candidates.md) records supplier procurement, invoice review, quality/warehouse, replacement/unannounced returns and future intent-based families, including triggers, owned/related work, completion and model gaps. These are backlog candidates only: no additional event-to-case rule is enabled by this list.
