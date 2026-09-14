# Facts and Open Questions

[Back to the guide overview](../business-reality-guide)

## “I would have added a custom ERP field” {#facts}

Huber adds a note: “Deliver in the morning only; use the side entrance.” The order for 30 lamps
stays the same. Stock and receivables do not change either. Yet the instruction should be available
to the people handling delivery, with its origin traceable.

In an ERP, you might add a custom field or note to the order line. In Reality, first ask what kind
of information this is. Do you need an additional supported observation, an existing operational
record, or just the original input?

A **Fact** records a supported, source-backed observation about an existing business record. Here,
it describes Huber's delivery promise: the source states a delivery instruction. It does not move a
due date, reserve goods or grant execution authority.

### An observation has a defined meaning

Each supported observation has a defined meaning so every caller understands it consistently. This
contract is a **predicate**. It defines what the observation says, what record it may describe and
which values are allowed.

Huber's note fits `order.delivery_instruction`: a text delivery instruction on a Commitment. The
technical name helps you look it up. For now, the business question is enough: **Who supplied which
information about which delivery promise?**

“Huber wrote this” is the supported statement. It does not establish that the driver will arrive in
the morning. A recorded promise to pay does not establish receipt of money either.

### Fact, operational record or original source?

| Everyday information                      | Appropriate home                                                                     | Business effect                                                 |
| ----------------------------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| Huber states a delivery instruction       | Fact on the delivery promise                                                         | Additional supported context                                    |
| Acme promises a different delivery date   | Date revision (`CommitmentRevision`) on the existing delivery promise (`Commitment`) | The effective date comes from the latest recorded date revision |
| Ten lamps are allocated to Huber          | Reservation                                                                          | Stock is assigned to the promise                                |
| Lamps actually leave the warehouse        | Movement                                                                             | Recorded stock and, where applicable, fulfilment change         |
| A payment is posted                       | LedgerEntry                                                                          | Financial posting                                               |
| An external field is not currently needed | Original SourceRecord                                                                | Input is preserved without an extra field                       |

**Where do you record a new delivery date?** Use
[Revise commitment (`revise_commitment`)](../../tool-usage/#command:revise_commitment) for the
existing, still-open delivery promise. Supply the promise and the newly stated date (`due_at`).
Reality stores a separate `CommitmentRevision` record; the original date on the Commitment remains.
The current view uses the latest stated date. An agent prepares this change for approval with
`commitment_revise_propose`. No additional Fact is created and the order document is not rewritten
for it.

Normal Commitment, Reservation, Movement, and Ledger commands do **not** manufacture mirror Facts.
An extra Fact saying “ten reserved” would duplicate existing allocation state. A **Business Event**
announces an executed change; it does not replace that change's records.

## How Facts come into being {#how-facts-arise}

Every Fact needs an existing target record and a stored source. The source is a **SourceRecord**;
the described object is technically called its **subject**.

1. **The source already exists.** If a supported connection imported Huber's instruction, select
   that source and the appropriate Commitment. The Web action **Record source-backed Fact** uses a
   registered predicate. An agent prepares the same operation with `fact_observe_propose`; the
   change requires authorised approval.
2. **Information arrives by telephone, email or paper.** First preserve the statement as a manual
   source, including its content and traceable origin. A supported Fact can then refer to it.
   Without a stored source there is no Fact.
3. **The information regularly appears in source data.** Through Open questions, an owner can
   prepare, test and activate a bounded Fact rule. It records the supported observation from future
   matching sources. The rule and its version remain traceable.

The first two paths use the registered predicate catalog. A configured Fact rule has its own
reviewed contract and supported targets. It cannot invent arbitrary observations or run arbitrary
code. Both paths produce traceable Facts; their configuration and approval differ.

## Reality Is Missing Something Important {#missing-information}

Suppose you want to ask: “Which open orders contain special delivery instructions?” Sources carry
that information, but it is not yet usable in the way you need. This is an **Open question**: a gap
between your work and what the model currently answers. It is neither an operational exception nor
an established observation.

Record the question, its business significance and representative sources under **Open questions**.
Members can raise questions; the company owner controls classification and rules. First decide where
the needed information belongs:

| What is missing?                                          | Appropriate path                                                   |
| --------------------------------------------------------- | ------------------------------------------------------------------ |
| Additional supported information about an existing record | Supported Fact or reviewed Fact rule                               |
| A recurring calculation or work list                      | View or Projection; new derivation through development             |
| A new operational warning condition                       | Reviewed Exception class through development                       |
| A new business effect or operational state                | Application operation or domain model with specification and tests |
| Preservation of an unused source field                    | Already possible in the original SourceRecord                      |

A Fact is therefore not a universal substitute for custom ERP fields. If core behaviour repeatedly
calculates, filters, joins or acts on a concept, its place in the typed model needs review. A new
field follows a proven use case, not merely its availability in an upstream system.

### Owner-configured rules are a separate entry path

For a supported Fact rule, proceed in stages:

1. **Prepare:** Select the source, meaning and a supported existing target such as a Commitment or
   DocumentLine. Uninterpreted sources do not create that target by themselves.
2. **Simulate:** Use representative sources to check the observations that would result. Include
   missing values, missing targets and conflicts. Missing does not automatically mean “no”.
3. **Activate:** The reviewed rule may be used for future evaluations. This does not silently
   process historical sources.
4. **Replay:** A separate replay evaluates older sources in bounded steps. Inspect the results.
   Repeated processing should not create duplicate observations.
5. **Deactivate if needed:** Future evaluations stop; already recorded Facts are not deleted.

Every rule-produced Fact retains its source, target and rule version. The rule does not reserve
stock, change due dates, send payments or define a new Exception class. It does not authorize an
agent action. Additional information may support a reasoned proposal; the operational effect still
needs its normal controlled operation.

## What is supported today

The following seven meanings are registered for direct observation. This is current product scope,
not an open-ended runtime catalog. Open-question rules use the separate path described above.

### Registered predicates {#registered-predicates}

The vocabulary is small on purpose and grows through review, never through conversation.

| Predicate                      | Subject       | Value                   | Typical statement                              |
| ------------------------------ | ------------- | ----------------------- | ---------------------------------------------- |
| `order.shipping_priority`      | commitment    | `standard` or `express` | The order source states a shipping priority    |
| `order.delivery_instruction`   | commitment    | text                    | “Deliver mornings only, use the side entrance” |
| `order.customer_reference`     | document      | text                    | The customer's own purchase order number       |
| `invoice.payment_promise_date` | document      | calendar day            | “We will pay RE-1042 by 30 September”          |
| `invoice_line.dispute_reason`  | document line | text                    | “The price differs from the quotation”         |
| `lot.quality_release`          | lot           | `released` or `blocked` | The inspection report releases lot 4711        |
| `movement.damage_report`       | movement      | text                    | “Two cartons arrived crushed”                  |

A new kind of observation needs a new predicate, added in the catalog with tests; see
[Adding another predicate](#adding-another-predicate). A rule brings its own contract and does not
need a catalog entry.

### Check your understanding

Huber promises by telephone to pay the remaining EUR 870 next week. Can that close the invoice?

<details>
<summary>Show answer</summary>

No. The statement can first be preserved as a manual source, then recorded as a supported payment
promise on `INV-1001`. EUR 870 remains open. Only actually recorded and applied payments or other
appropriate settlements change that amount.

</details>

<details>
<summary>Technical detail: complete example, validation and predicate extension</summary>

The following integration example is a separate variant. Shopify is a shop supplying structured
order data; JSON is its exchange format. Read this section if you want to trace provenance and the
tool call down to individual fields.

Every new Fact requires a source and target in the same company, internal IDs, a reviewed predicate,
a valid value, an observation time and an idempotency identity. Agents never write directly to the
Fact table.

### Complete example: shipping priority

Assume Shopify sent this order fragment:

```json
{
  "id": "ORDER-42",
  "shipping_priority": "express",
  "customer_note": "Use the loading dock"
}
```

Reality first keeps the complete payload unchanged:

```text
SourceRecord src_7f...
source_system: shopify
source_type: order
external_id: ORDER-42
payload: complete original JSON
```

After an order interpreter has created the related Commitment, an agent or deterministic interpreter
may propose this observation:

```json
{
  "source_record_id": "src_7f...",
  "subject_type": "commitment",
  "subject_id": "com_91...",
  "predicate": "order.shipping_priority",
  "value": "express",
  "observed_at": "2026-09-02T14:06:00Z",
  "idempotency_key": "shopify:ORDER-42:v1:shipping-priority"
}
```

The current predicate contract permits only a Commitment subject and the values `standard` or
`express`. An unknown predicate, a foreign-company source or subject, or a value such as `overnight`
is rejected.

### How agents create one safely

Chat and external MCP agents use `fact_observe_propose`. Calling it creates a `ChangeProposal`, not
a Fact. The proposal shows the exact source, subject, predicate, value, and observation time for
review.

```text
fact_observe_propose
        ↓ no Reality mutation yet
ChangeProposal(status=proposed)
        ↓ explicit human confirmation
fact_observe
        ↓ one transaction
Fact + fact.observed
```

The confirmed application operation validates the same rules for every caller. A repeated request
with the same idempotency key and identical content returns the original Fact. Reusing that key for
different content fails instead of silently changing the first observation.

> **Current behavior:** The public Fact-observation vocabulary holds the seven
> [registered predicates](#registered-predicates). Source-specific extraction and automatic
> promotion into typed Reality are not part of the Fact core.

### How Facts are used

Facts provide explainable context for people, operators, and later decisions. A reader can traverse:

```text
Fact
  → subject: Commitment
  → SourceRecord
  → original Shopify payload
```

A later operation may use the Fact as evidence when proposing a typed action, but the transition is
explicit. For example, an `express` observation may help an operator recommend an earlier Commitment
due time. The Fact itself does not change the Commitment, reserve stock, or authorize an effect.

Use the **Facts** register for the business-readable list and **Inspect** for opaque identity,
predicate, observation time, source details, event history, and original payload.

### Adding another predicate

Do not let a parser or model invent predicate names at runtime. Before adding one, document a real
business example and answer:

- Which existing subject type does it describe?
- What canonical value type or allowed values does it use?
- Why is the observation operationally relevant?
- Why does no existing typed Reality record already own it?
- Which source and acceptance test prove the complete trace?

If core logic repeatedly calculates, filters, joins, constrains, predicts, or acts on the value,
promote that concept through a separate specification into an appropriate typed field or entity. Do
not keep growing an unbounded Fact vocabulary as a substitute for a proven domain model.

</details>

To finish: [Summary](./07-model-at-a-glance) brings together the core concepts and the shared work
of people, agents and workflows.
