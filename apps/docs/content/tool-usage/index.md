---
aside: false
---

# Tool Usage

Everything Reality can do, ordered the way an ERP professional thinks: by business object and by
process. Pick an object such as **Order**, **Invoice** or **Business partner** and you see the lists
that show it, the actions that change it, the exceptions it can raise, and what a person must state
for each action. Pick a process such as **Order to cash** and you walk it step by step. The
technical view underneath is the same content sorted by system part, for developers and agent
operators.

Everything here is generated from the executable catalogs of the running code. If it is not on these
pages, Reality does not do it yet.

The **Data model** tab shows the central record types with examples, every stored field, defaults
and relevant actions. Start with [Commitment](#model:commitment).

<ToolUsage />

## How to read it

- **Start with the object or the process, not the tool.** An action such as _Post customer payment_
  is the business operation. CLI, Web, API, Chat and MCP are only doors to it; the parameters are
  the same behind every door.
- **Required parameters are the minimum a source must state.** Opaque IDs such as `commitment_id`
  come from a previous list or lookup, never from a human number.
- **Agent tools ending in `_propose` never change anything by themselves.** They prepare a proposal
  that a person approves. Read tools answer immediately. See
  [Agent capabilities](/tool-usage/#choosing-a-tool) for the approval model.
- **Every action names what to check afterwards.** That list or projection is how an agent, or you,
  proves the operation did what it claimed.
- **The [Agent Playbooks](../agent-playbooks/)** tell the same processes as stories with a clerk and
  an agent. The process view here is the index into them.

## How an agent chooses the right tool {#choosing-a-tool}

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

## How to read the lists {#how-to-read-the-lists}

Stock, open work and explanations are calculated from the records at read time. This is what a list
claims and what it does not.

### Inventory formulas

```text
physical  = quantities into a Location - quantities out of it
reserved  = active Reservation quantities
available = physical - reserved
incoming  = open supplier Commitment quantities
projected = available + incoming
```

Physical is what is recorded at the Location now, reserved what is allocated to outgoing promises,
available what can still be allocated without double-promising, incoming what suppliers still
promise, projected what could be available once they deliver.

### What is open?

| Dimension           | Open when                            | Closes when                              |
| ------------------- | ------------------------------------ | ---------------------------------------- |
| Customer Commitment | promise exceeds qualifying shipments | shipments fulfil it, or it is cancelled  |
| Supplier Commitment | promise exceeds qualifying receipts  | receipts fulfil it, or it is cancelled   |
| Reservation         | status is `active`                   | shipment consumes it or release frees it |
| Customer invoice    | active receivable remains            | derived amount reaches zero              |
| Supplier invoice    | active payable remains               | derived amount reaches zero              |

There is no universal “Document open” rule. An invoice can stay financially open after full
delivery, a sales order can have no open delivery quantity while its invoice is unpaid, and a
cancelled promise can still carry an unresolved credit or return.

### Risk, projections and explanations

Risk is computed, not copied onto a Document: it compares an outgoing Commitment's open quantity
with stock and supply, with priority, due time and holds as context, so an explanation can say “30
promised, 18 fulfilled, 12 open, seven reserved, five short” instead of an unexplained red status.
Projections are rebuilt from records and BusinessEvents; a checkpoint that trails the latest event
marks a stale view, and commands never trust it to permit excess shipment or over-allocation.

`explain commitment` returns the promise, parties, Item, Location, due date, state, Reservations,
Movements, fulfilled and open quantity, risk and the DocumentLine → Document → SourceRecord chain
with raw payload when present. Missing evidence is reported honestly. The timeline interleaves the
record kinds:

```text
09-02  SOURCE       Shopify order 4711 v1 received
09-02  COMMITMENT   deliver 12 BIKE-LIGHT
09-02  RESERVATION  allocate 12 BIKE-LIGHT
09-03  MOVEMENT     shipment 5 BIKE-LIGHT
09-04  MOVEMENT     shipment 7 BIKE-LIGHT
09-22  LEDGER       receivable debit EUR 1,470
09-25  LEDGER       receivable credit EUR 500
```

### Interpretation coverage {#interpretation-coverage}

A stored source is not automatically understood. Each attempt to interpret a SourceRecord leaves an
outcome and the identities it produced:

| Classification | Meaning                                                       |
| -------------- | ------------------------------------------------------------- |
| `interpreted`  | Processing completed and identified produced Reality records. |
| `needs_review` | Business meaning remained ambiguous; no Reality was invented. |
| `unsupported`  | No interpreter exists for this source type.                   |
| `stale`        | A newer upstream version is already current.                  |
| `conflict`     | One upstream version identifies different payloads.           |
| `failed`       | Processing failed and attempted business writes rolled back.  |

`pending` and `processing` are live job states. If a SKU is unknown, no partial order survives:
attempt 1 is `failed`, and after the master data is corrected attempt 2 can be `interpreted`, with
both attempts visible. Agents read this through `interpretation_coverage`; the result omits
payloads, credentials and stack traces.

## Manual pages

The same content as plain pages for search engines, printing and permalinks. Search works like
`apropos` on a Linux console:

- [Business resources](./resources) — every business object with its lists, actions and exceptions.
- [Business processes](./processes) — the step lists with their actions, checks and exceptions.
- [Business commands](./commands) — every operation, its agent tools and their parameters.
- [Views, projections and actions](./views) — what each workspace shows and lets you trigger.
- [Operational exceptions](./exceptions) — the derived conditions that need attention.
- [Business events](./events) — how commands reach the timeline.

Regenerate after changing a catalog or an MCP schema:

```bash
make docs-generate
```
