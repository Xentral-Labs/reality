# Manual end-to-end usability learnings — 2026-09-26

**Status:** exploratory usability evidence from a local browser run. This document does
not define approved behaviour. Any selected change must enter the Spec Kit workflow.

## Test story

The run started with an empty company and used Chat for the full small-wholesale flow:

1. create payment terms, customer, supplier, company party, item and warehouse;
2. order 30 units from the supplier and receive them;
3. take a 10-unit order on 14-day terms, reserve, ship, invoice and allocate payment;
4. take another 10-unit order on prepayment, prove that shipment is blocked before
   payment, allocate payment and then ship;
5. inspect stock and open receivables throughout the flow.

The business rules ultimately worked. The flow did not feel like one guided process,
however. A first-time operator needed internal IDs, exact tool vocabulary, retries and
knowledge of hidden prerequisites that the product should have supplied.

## What would have made the run intuitive on the first attempt

### 1. Chat should own the workflow, not merely individual commands

A request such as "set up a small trading company and process its first order" should
produce a visible checklist with prerequisites, current state, next safe action and
completion evidence. Chat should retain the objects it just created and refer to them by
business names. The user should never have to copy opaque party, item, line, commitment,
reservation or document IDs back into a later prompt.

The ideal interaction is progressive: Chat detects missing master data, proposes the
minimum setup, waits for confirmation, executes it, refreshes reality and advances to
the next step. It should explain why a step is unavailable and offer the action that
resolves the prerequisite.

### 2. A claimed proposal must always be a real, reviewable proposal

Several answers said that a proposal had been created while no action card or confirmation
button existed. Some answers also printed proposal-like IDs that did not correspond to a
usable action. This breaks trust at the most important boundary in the product.

Chat should distinguish only three explicit states:

- **Drafting:** no proposal exists yet.
- **Ready for review:** a persisted action card exists and is visible in the answer.
- **Executed:** the result includes the created reality records and links.

If tool invocation fails, Chat must report the failure and must not phrase the response as
success. Proposal IDs should come only from the persisted action result, never from model
text.

### 3. Tool schemas should prevent invalid combinations before review

Party creation initially included an `external_id` without a `source_system`. Execution
correctly rejected the action atomically, but the proposal should never have reached the
review stage. The party tool should either require both fields together in its schema or
omit source identity by default for manually created master data.

Likewise, supplier, customer and own-company roles need first-class labels and examples.
The purchase-order flow briefly selected the customer as the supplier-side party because
the semantic role was not made explicit enough.

### 4. Entity resolution must use names and recent context

The operator supplied normal business language, yet successful shipment required exact
internal IDs. In one attempt Chat invented or selected the wrong item ID and therefore
created no usable proposal. The product should resolve the unique item, warehouse,
customer, order and reservation from the current tenant and recent conversation, show the
match in human-readable form, and ask only when more than one plausible record exists.

Opaque IDs remain correct system identity, but they belong in the inspector and audit
trail—not in the normal operating conversation.

### 5. Setup mode and sandbox mode need a clear capability contract

In a Sandbox company, Chat could prepare normal-looking actions but execution then failed
with "Use the reviewed practice actions for this company." A user should learn this before
creating data or reviewing an action.

The company header and Chat composer should state whether the company is:

- a guided practice environment with a bounded action catalog; or
- a regular company in which the standard confirmed tools are available.

Unsupported actions should be disabled or routed to the equivalent practice action before
a proposal is built.

### 6. Payment terms should drive an understandable fulfilment gate

The prepayment rule itself behaved correctly: shipment was refused with EUR 500 required
and EUR 0 received, then allowed after full allocation. This should be visible before the
user attempts shipment.

The order page should show a single fulfilment readiness panel containing stock on hand,
reserved quantity, payment required, payment received and the exact remaining blockers.
After payment, the panel should update immediately and expose "Ship now" as the next action.

### 7. Read models must be fresh enough to verify the action just completed

After invoice and payment work, Open Items still showed zero records and reported multiple
events not yet considered; refresh found no newer calculation. Even when the write model is
correct, stale verification makes the process appear broken.

For operational confirmation, the UI should either:

- update the affected projection synchronously within a defined latency budget;
- show a clear pending state and automatically refresh when the projection catches up; or
- read the just-written authoritative records as provisional evidence until the projection
  is current.

The page should display the projection watermark and backlog in user language, not merely
an unexplained event count.

### 8. Every execution receipt should link to business evidence

A successful action should return human numbers and direct links: purchase order, goods
receipt/movement, sales order, reservation, shipment, invoice, payment allocation and the
new stock/open amount. This would make Source → Evidence → Reality understandable without
forcing the user to visit several lists and reconstruct the chain.

For the completed run, the most useful receipt would have said, for example: "Received 30;
available 30. Reserved and shipped 10 for SO-E2E-001; invoice RE-E2E-001 is fully paid.
Reserved 10 for SO-E2E-002; shipment blocked until RE-E2E-002 was fully paid, then shipped.
Expected physical stock: 10."

### 9. The product should provide a deterministic first-transaction walkthrough

An empty company needs a compact guided scenario using the real services and confirmation
rules—not special demo writes. It should create or ask for the minimum master data, carry
stable business references across steps, exercise procurement and order-to-cash, and end
with a reconciliation view:

- purchased, received, reserved, shipped and remaining quantities reconcile;
- invoice totals, allocated payments and open balances reconcile;
- prepayment shipment policy is proven by a blocked attempt followed by an allowed one;
- every result links to its evidence and reality records.

This walkthrough would be both onboarding and an executable acceptance test for Chat, Web
and MCP parity.

## Observed strengths worth preserving

- Mutations remained behind explicit confirmation.
- Invalid party source identity was rejected atomically.
- Stock reservation and movements produced the expected inventory arithmetic.
- The prepayment shipment gate used allocated payment evidence and correctly changed from
  blocked to allowed after settlement.
- Payment allocation receipts exposed the remaining open amount.
- The same domain objects and controls were reachable through the normal application tools;
  no direct database workaround was required.

## Suggested acceptance criteria for a future usability specification

1. A first-time user can complete this story using business names only.
2. Chat never claims that a proposal exists unless a reviewable persisted action is shown.
3. Invalid tool argument combinations are rejected before confirmation.
4. Sandbox limitations are visible before an unsupported action is drafted.
5. Fulfilment readiness explains both stock and payment blockers on one surface.
6. Open Items reflects a completed payment within a documented latency budget and exposes
   pending projection work until then.
7. The final reconciliation proves `30 received - 20 shipped = 10 physical`, both invoices
   fully allocated, and no premature prepayment shipment.
8. The same scenario passes through Chat and MCP using the shared application services and
   produces equivalent evidence.

## Evidence note

This assessment is based on two isolated local runs on 2026-09-26. The browser scenario
completed in the regular company. A separate Sandbox attempt exposed the practice-action
mismatch. The MCP scenario then completed in its own regular company through Claude
Desktop and a tenant-scoped Reality MCP token.

## MCP run findings

### Result and reconciliation

The MCP run completed the same procurement and order-to-cash story without direct database,
shell, browser or private API access. All mutations used MCP proposals and MCP approval and
execution. The final authoritative reads showed:

- 30 units received, 20 shipped and 10 physical/available units remaining;
- both EUR 500 customer invoices fully allocated with an open amount of zero;
- the second payment fully allocated at `07:34:30.545Z` and the second shipment executed
  later at `07:34:54.752Z`;
- all three purchase/sales commitments fulfilled with zero open quantity; and
- no remaining customer receivable balance or operational exception.

### Critical parity defect: VORKASSE was not an automatic MCP fulfilment gate

The most important result is a real browser/MCP behaviour mismatch. In the browser Chat
run, an attempted dispatch for the VORKASSE order was refused because EUR 500 was required
and EUR 0 had been received. In the MCP run, the equivalent unpaid order reported
`ship_ready: true`, had no blocker, and produced a valid dispatch proposal. The proposal
was deliberately rejected before execution, so no premature movement occurred.

To finish the safety proof, the MCP agent had to create a manual document hold with reason
`other`, verify that dispatch was refused while the hold was active, post and allocate the
payment, release the hold, and then dispatch. This proves the manual hold mechanism but does
not prove native prepayment enforcement. The product should derive the same payment gate
through every surface that calls the shared fulfilment service. A transport-specific agent
must not have to invent a compensating hold.

Related evidence from the MCP run:

- payment terms expose `due_days` but no explicit prepayment characteristic;
- invoices returned `payment_term_id: null` even when their orders used NET14 or VORKASSE;
- the pre-payment and post-payment dispatch review tokens were identical, suggesting that
  payment/hold readiness was absent from or not reflected in the preview token.

### Proposal lifecycle defects

Preview accepted several actions whose invalidity was only discovered during execution: a
second posting of an already posted invoice and multiple unsupported document-hold reason
codes. Checked failed proposals remained in `executing` with no receipt instead of reaching
a terminal failed or rejected state. This creates permanent ambiguity in the approval
inbox and makes safe retries harder.

Preview should run all deterministic validation available before review, and execution
must transition every proposal to a terminal state even when the underlying application
service refuses it.

### MCP discovery and schema friction

The MCP agent completed the flow, but only after learning inputs from validation errors:

- `capability_describe` returned `not_found` for the attempted public tool names;
- shipment receipt and dispatch tools exposed an empty input schema, so the agent had to
  infer `purpose`, `counterparty_id`, `movements[]` and the purpose values
  `supplier_delivery` and `customer_delivery`;
- document-hold reason codes were not discoverable; several plausible values failed and
  only `other` worked;
- the sales-invoice record action already posted the invoice, making a separately requested
  post action redundant and invalid;
- payment execution receipts exposed ledger entries but not the payment document ID; an
  additional payments read was needed to obtain it;
- no discoverable open-items resource was available, so the agent used party balances and
  settlement context as the verification path; and
- `finance_payments` accepted `incoming`/`outgoing`, not the intuitive `customer` direction.

Every public MCP tool used in an advertised capability should publish its complete input
schema, enumerated business codes, effect and refusal conditions. Capability discovery
should return the canonical tool names the client is expected to call.

### Read freshness and observability

Financial reads were internally consistent and showed EUR 500 open before payment and zero
after allocation without visible staleness. Inventory and commitment reads also returned
current values. However, several responses kept reporting `projection_version: 5` while
the event sequence advanced from 14 to 48. Either that version label was stale or its
meaning was not clear enough to support freshness decisions.

The browser and MCP runs therefore exposed different observability problems: the browser
Open Items page visibly lagged, while MCP finance reads were current but the projection
metadata was confusing. Both surfaces need an unambiguous watermark contract.

### MCP-specific acceptance criteria to add

1. The same unpaid VORKASSE order must be non-shippable through Web Chat, direct Web actions
   and MCP without a manually added hold.
2. A dispatch preview token must change when payment or hold state that affects readiness
   changes.
3. Every failed execution reaches a terminal proposal state with a refusal receipt.
4. Shipment and hold tools publish complete schemas including enumerated purpose and reason
   codes.
5. Invoice record/post semantics are explicit and cannot invite an invalid duplicate-post
   step.
6. Payment receipts include the payment document, ledger entries, allocations and open
   amount in one result.
7. MCP exposes a documented open-items read equivalent to the operational finance view.
8. Projection metadata lets a client prove whether a read includes a known event sequence.
