# MCP read contracts

Feature 145 implements seven read improvements: balances separated by currency,
ledger discovery, explicit quantity units, location inventory, retained-order
explanation, pagination, and observation/persistence metadata. It adds no schema,
unit conversion, exchange rates, historical snapshots, or business mutations.

## Migration and access

The public MCP tools `business_records_discover`, `inventory_read`,
`commitments_list`, `fulfillment_queue`, `fulfillment_blockers`, and
`item_supply_demand` now default to `response_format: "page"`. Clients must read
`records` instead of treating the response itself as an array. Existing tool names,
tenant authorization, and permission requirements remain unchanged; the generated
MCP tool catalog lists the required permission for each tool.

For a staged migration, explicitly request `response_format: "legacy"` on these
six tools. Internal application-tool callers still default to legacy lists.
Legacy discovery is bounded, and legacy operational reads can refresh and commit
projection caches. Inventory filters and location views require page mode.
`finance_balances` always uses the new currency-safe response; its old hardcoded
single-currency object has no compatibility mode.

## Complete traversal

Send `limit` from 1 through 100 (default 25) and optionally `cursor`. A page has:

```json
{
  "records": [],
  "next_cursor": null,
  "has_more": false,
  "metadata": {}
}
```

When `has_more` is true, pass `next_cursor` unchanged with the same tenant, tool,
and filters. Continue until false. A cursor from another scope is rejected; the
limit can change. No total count is promised. Records sort by opaque ID or stable
record key. This is live keyset traversal: concurrent changes can alter later
pages, and inserted keys before the cursor will not appear. Restart against a
quiescent dataset for reproducible comparisons. Finishing traversal proves only
coverage of matching retained records under those limitations, not upstream
completeness. Operational derivation currently reads the full relevant tenant
state before slicing; bounded output does not promise bounded computation.

## Operational evidence summaries — Spec 366

`business_records_discover` page mode adds `summary` beside the existing page fields.
`shown_record_count` counts only returned records, excluding the pagination lookahead.
Movement `counts_by_type` separates `return` (customer return) and `supplier_return`.
These are record counts, never quantity, order, item or customer totals. The existing
substring query `return` matches both types.

`scope: "shown_records"`, `omitted_before` (cursor excludes the earlier key range),
`omitted_after` (has_more), and `complete_matching_selection` make coverage explicit.
Only a first page without further results covers its matching retained selection at
that read. A final cursor page does not cover the earlier range. Live pages are not
snapshots and upstream freshness/completeness remain unknown. `observation` is a
ready deterministic English description of those same counts and boundaries.
Legacy discovery keeps its bounded list shape, without a summary envelope.

Movement, Commitment and Reservation discovery records expose available canonical
`item_name` and `item_sku` alongside their opaque reference and unit. Missing labels
are null; labels never replace identity. The existing scoped Item lookup owns these
labels. Quantities remain unchanged and are not summed across items or units.

Each `order_explain` fulfillment line adds `unfulfilled_cause`: `unknown` for positive
remaining fulfillment and `not_applicable` otherwise. Existing canonical blocker
codes describe current readiness; they do not establish the historical cause of
nonexecution. Missing outbound-delivery objects do not establish a conversion
requirement. This read does not infer a historical cause from present blockers.

These shared read additions need no new tool, permission or browser access. Native
and external agents receive the same service evidence. Accurate tool output does not
guarantee arbitrary free-form provider prose; the real broad daily response still
has documented inaccuracies. See [spec366 verification](../../specs/366-daily-evidence-summary/verification.md).

## Physical shipments

`shipments_list` returns tenant-scoped real consignments with Package tracking references,
effective Movement contents and current unsuperseded observations. `shipment_explain` follows one
opaque Shipment ID through Packages, Movements, events and SourceRecord references. These reads do
not treat Delivery Commitments as shipments and do not infer old Movements into Packages.

## Money, units, and locations

`finance_balances` returns `balances`, an array ordered by currency, plus
`metadata`. Each entry contains `currency`, `receivables`, and `payables`; money is
a decimal string. Receivables are debit minus credit on accounts receivable;
payables are credit minus debit on accounts payable. Represented zero and negative
positions remain visible. An empty tenant returns an empty array. There is no FX
conversion or combined currency total. These are ledger account positions, not
net revenue, profit, or bank settlement. Ledger discovery exposes `debit_credit`
and the matching compatibility alias `side`.

Operational quantities include the item's recorded `unit`, `unit_status`, and
`quantity_basis`. Missing units are null/unknown. Where document-line units are
available, they remain visible and `unit_mismatch` flags disagreement. Quantities
are not converted. Commitment quantities and due dates reflect revisions while
original values remain available.

`inventory_read` defaults to `view: "aggregate"`, explicitly labelled
`item_all_locations`. Request `view: "location"` for item/location rows, or pass
`location_id` to select that scope. `item_id` can narrow either view. A location
view includes zero-stock item/location combinations for stock-capable locations;
an explicit valid location can also be inspected. Physical, reserved, and
available quantities use the same location predicates. Incoming commitments are
promises, not received goods or an arrival forecast. An allocation gap does not
by itself establish a physical shortage.

## Retained orders and observation

`order_explain` resolves a tenant-owned order document ID or delivery commitment
ID, including fulfilled and cancelled cases. Display numbers/external references
remain conveniences and ambiguous matches are refused. It returns retained
source, document lines, commitments, reservations, movements, and derived
fulfillment. Closed lines remain visible but have no actionable open quantity;
closed orders are not ship-ready. It does not reconstruct state at a past date.

Page reads, finance, and order explanation return `metadata` containing
`contract_version: 2`, tenant and applied filters, UTC `observed_at`, known
`projection_version` or null, observed local `event_sequence` or null,
`upstream_freshness: "unknown"`, and `consistency` (`live_keyset` or `live_read`).
The local event sequence is an observation, not a snapshot ID or proof that every
external change was imported. Individual SQL reads use the active database
transaction's isolation; no atomic multi-query snapshot is promised.

These diagnostics suppress autoflush, do not write business/projection records,
and do not commit. `metadata.persistence` states those guarantees. Transport
authentication can separately persist token-use telemetry. The guarantee does not
apply to explicitly selected legacy projection reads or to other tools such as
cached price resolution. Business actions still use their existing proposal,
confirmation, execution, and verification contracts.

## Runtime Configuration Boundary — Spec 326

Settings display validates only MCP_URL as an HTTP(S) origin, requiring HTTPS in
production. The separate MCP runtime validates its listener and authorization issuer.
Issuer precedence is explicit MCP_AUTHORIZATION_ISSUER, canonical API_URL (spec265
FR-023), then the local development default. Production issuer HTTPS and origin checks
remain mandatory; unrelated runtime-only settings cannot break the owner's public
endpoint display.


## Existing-tool interpretation boundaries — Spec 367

The existing fulfillment queue, readiness and order explanation share the same
`unfulfilled_cause`: positive open quantity means `unknown`, while no remaining
quantity means `not_applicable`. Current blockers do not establish why past execution
did not happen. Readiness blocker objects and fulfillment blocker rows expose
`blocker_kind`: `recorded_hold` for commitment/customer holds, otherwise
`derived_readiness_condition`. A recorded hold may be system-created. A blocker row's
key identifies a condition for one promise; several promises can share one hold.
Counting conditions does not count distinct holds.

Exception list/explanation preserve each evaluator's own `cause_ids`, values and trace.
Their read-time `interpretation_scope` states that a relationship causing another
condition is not established by this result. Shared references or co-occurrence alone
do not prove cross-condition causality. These fields are added after cached derivation;
they are not persisted as business authority or projection payloads.

Capability index and topic reads expose `external_agent_runtime`, with configuration
states `unknown` and visibility `outside_reality`. Reality tool availability and grants
cannot verify an external client's schedule, mission, checkpoint, next run or pause
state. Use that client's own tools for such verification. This adds no scheduler.

Native OpenAI `length` and Anthropic `max_tokens` stops are handled before tool
argument decoding/dispatch, in streamed and ordinary responses. The adapter replaces
partial output with a localized incomplete-response notice; streaming emits reset
then the same notice used for the durable answer. It executes no calls from that
incomplete response and never automatically retries or replays business proposals.
The bounded output budget remains unchanged. Calls from earlier completed rounds may
already have run; the notice does not claim those were undone.

Verification: [spec 367](../../specs/367-tool-evidence-boundaries/verification.md).
Normal completions, genuine transport failures, tenant scope, grant boundaries and
confirmation semantics retain their existing behavior. Deterministic tool boundaries
do not guarantee every free-form external model answer.

## Payment evidence and retained selection counts (spec 368)

Existing readiness and queue/exact-order reads add transient `payment_interpretation`.
Standard policy reports payment `not_evaluated`; stated gross is an order basis,
not an unpaid invoice, and legacy zeroes establish neither absence of actual payments
nor settlement. Missing, ambiguous and unstated prepayment evidence is qualified;
canonical qualifying amounts describe this order, not a customer balance. Actual
owner release is distinct from payment and preserves surviving canonical blockers.
Interpretation never enters cached payloads or dispatch review hashes.

Discovery `selection_record_count` is known only for a complete first response;
it is null for every partial page, including final cursor pages. Counts refer to
the matching retained selection at that read, not upstream completeness, Movement
quantities or Shipment consignments. No extra query or public tool is added.
See [verification](../../specs/368-payment-evidence-scope/verification.md).

## Executed Decisions by affected order (spec 369)

Use the existing `business_records_discover` tool with `family: "executed_decision"`.
An optional opaque `document_id` selects a retained sales/purchase order. Selection
follows exact execution events on that order, its lines, commitments, reservations
and movements to `BusinessEvent.action_id`. Line membership takes precedence over
a commitment's document fallback. Several effects of one Decision produce one row.
Shared human numbers, items, parties, source co-occurrence and JSON text never
establish membership. Without an order filter, only company-scoped retained executed
Decision metadata is listed; no affected-order association is claimed.

Records contain opaque `id`/`proposal_id`, tool, executed status, creation/decision
times, `association_scope`, and callable `review_read: "proposal_review"` and
`verification_read: "proposal_execution_status"`. Use those existing tools with the
returned ID to read actual review/receipt and verification; do not repeat execution.
Raw inputs, outputs, credentials and approval tokens are absent. Discovery grants
no approval rights and does not bypass the exact readers' own permissions/policies.

Page `metadata.decision_coverage` states that historical completeness is unknown.
An empty order-filtered result means no matching retained exact execution event,
not that no historical action affected the order. Pending, rejected, failed and
executing Decisions are outside this family. Events without an action do not invent
Decisions. Page and bounded legacy shapes, cursor filters and existing permissions
are preserved. No schema, business write, extra report command or browser is needed.
See [spec 369](../../specs/369-business-decision-discovery/spec.md).


## Evidence limits beside observations (spec 370)

Executed Decision page summaries repeat the existing coverage as `selection_scope`
and `historical_completeness`. The first count sentence names
`retained_execution_events` for an order filter or `retained_executed_decisions`
without one. Complete matching selection still means only the retained filtered
selection at this read; it never proves complete historical actions. Empty and
partial/final-page semantics and legacy discovery are unchanged.

`order_explain.interpretation_scope` distinguishes current inventory and order-linked
Movements from complete inventory history (`inventory_history:
not_established_by_this_read`). Neither present stock nor a shipment proves receipt
timing or an alternative inventory context. Report uninspected history as “not
checked” instead of adding conditional explanations. `inventory_read` is also a
current stock read, even with exact item/location filters.

The existing `movement_explanation(movement_id)` follows an exact retained movement's
source/business/correction links; it does not establish complete inventory history.
Movement discovery has no item/document filter; its substring query matches movement
type. Do not invent filters or source relationships. Guidance is shared, transient
and non-authoritative: it changes no quantities, operational rules, permissions or
stored history and cannot guarantee an external provider's free-form answer.
See [spec 370](../../specs/370-read-evidence-boundaries/spec.md).
