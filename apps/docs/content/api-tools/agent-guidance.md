---
aside: false
---

# How an agent chooses the right tool {#choosing-a-tool}

[Back to the tool overview](/tool-usage/)

Every capability comes with a description that says when to use it, what its result proves and what
it does not, and which read verifies the effect. Agents never write tables directly and keep no
private copy of the business rules; Chat and MCP read the same descriptions and call the same
application tools as the Web app.

### The governed agent loop

```text
discover records and opaque IDs
        ↓
describe the candidate capability
        ↓
select and explain, or safely decline
        ↓
propose the typed command
        ↓
human confirmation or adopted policy
        ↓
shared Reality service executes
        ↓
re-read the declared business projection
        ↓
verified / refused / unknown / reconciliation required
```

Use `business_records_discover` to find tenant-scoped records and their opaque IDs, then call
`capability_describe` with the public tool name, for example `{"tool_name": "reservation_propose"}`.
The lookup is read-only. For proposal tools it returns preconditions, confirmation and retry
guidance, refusals, events and verification projections; for read tools the data basis, freshness,
limitations, empty-result meaning and what the read proves or explicitly does not prove.

### Read capabilities are capabilities too

| Read capability               | Use it for                                                                         | Do not infer                                                         |
| ----------------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `business_records_discover`   | Find tenant-scoped records, current values, and opaque IDs                         | That a discovered record proves an end-to-end outcome                |
| `interpretation_coverage`     | See how a SourceRecord was interpreted and which Reality identities were produced  | That the interpretation is complete or correct merely because it ran |
| `order_explain`               | Trace one order through Source, Evidence, Commitments, Reservations, and Movements | External delivery or payment without corresponding Reality records   |
| `commitments_list`            | Read promises and their derived fulfillment state                                  | Physical stock, allocation, delivery, or payment                     |
| `inventory_read`              | Read physical, reserved, and available quantities                                  | That goods were promised, shipped externally, or paid                |
| `exceptions_list`             | Read registered operational attention conditions                                   | That an empty list proves the whole business is correct              |
| `fulfillment_queue`           | Prioritize derived order readiness and work state                                  | That a ready order physically shipped                                |
| `fulfillment_blockers`        | Inspect registered causes blocking orders or items                                 | That every possible blocker is modeled                               |
| `item_supply_demand`          | Compare item-level supply, demand, and shortages                                   | That expected supply will physically arrive                          |
| `exception_explain`           | Explain one selected current exception through its Reality context                 | External root cause or successful remediation                        |
| `proposals_awaiting_approval` | Review governed intent waiting for human approval                                  | Authority, execution, or resulting Reality                           |
| `proposal_execution_status`   | Reconcile one confirmation and verify its receipt against current Reality          | Fulfilment, delivery, or the final customer outcome                  |
| `finance_balances`            | Read receivable and payable positions derived from LedgerEntries                   | Bank settlement, reconciliation, or accounting completeness          |

Describe a read by its public MCP name even when the internal application tool is called
differently; the returned `application_tool` is routing, not a second identity. Before a result
becomes a claim, check its `data_basis`, `freshness`, `limitations`, `empty_result`, `unknown_when`
and `verification`.

### Fact or typed Reality?

Use the shortest record that truthfully represents what happened:

| Business meaning                                                     | Capability                |
| -------------------------------------------------------------------- | ------------------------- |
| A source explicitly states an approved contextual observation        | `fact_observe_propose`    |
| A new order establishes customer or supplier promises                | `order_create_propose`    |
| Available stock is allocated to an existing promise                  | `reservation_propose`     |
| Goods physically arrived, moved, shipped, returned, or were adjusted | `movement_create_propose` |

A Fact does not mirror typed Reality and a model prediction is not a Fact. A Reservation does not
prove that goods moved, a Movement does not replace the Commitment that explains why fulfilment was
due, and unknown fields stay in the SourceRecord until a reviewed Fact predicate or typed use case
exists.

### Confirmation and unknown outcomes

Proposal tools create a `ChangeProposal` and change nothing. Execution needs the confirmation or
policy boundary: a person approves, and the confirming client calls `proposal_approve_and_execute`
with `approved=true`. Reality claims a proposal atomically, so exactly one caller moves it from
`proposed` to `executing`; a later call against `executed` returns the stored receipt, a call
against `executing` is refused because the outcome may be unknown.

To verify, re-read the projection the description names. After a reservation, `inventory_read`
should show reserved quantity up and available quantity down; that proves allocation, never that
goods moved. After a timeout or lost response, call `proposal_execution_status` with the proposal
ID: it checks the receipt against the tenant's Proposal, Reservation, Commitment and event and
states `business_outcome=not_proven` explicitly. If the status stays `executing` or any ID, quantity
or event disagrees, the outcome stays unknown. A successful response is not sufficient proof;
escalate and inspect the named records instead of inferring success from an exception that
disappeared.

### Refusals carry a code

When a tool refuses, the result is an MCP error result whose text is one JSON object:
`{"code": "...", "message": "...", "tool": "..."}`. The code is stable and says why Reality refused:
`not_found` (the record the arguments name does not exist in this tenant), `invalid_operation` (the
request is not valid for this record or these arguments), `conflict` (the request was valid in shape
but based on stale state), `needs_review` (an interpreter declined because the business meaning is
ambiguous), `reality_error` (any other business-readable refusal). The message is the sentence a
person reads; it is for people and must not be parsed. An agent that has to decide whether to retry,
ask, or stop reads the code and shows the message. Failures that are not refusals, such as a missing
scope or an unknown tool, keep their plain text and no code; they are not business outcomes.

### Adding guidance for another capability

1. Name the exact public MCP tool; do not share one description between tools with different intent,
   such as reservation creation and release.
2. For a proposal, state purpose, use and non-use conditions, preconditions, confirmation,
   idempotency, refusals, events, verification reads and examples. For a read, state purpose, data
   basis, limitations, freshness, empty-result meaning, unknown conditions and next steps.
3. Reference only registered Business Events, known Reality records and read-only projections, and
   use opaque IDs, never document numbers.
4. Add selection and planted-drift tests before advertising the capability. Validation stays in the
   application service; guidance explains the boundary, it does not authorize anything, and no
   conversation activates new guidance or Fact predicates by itself.
