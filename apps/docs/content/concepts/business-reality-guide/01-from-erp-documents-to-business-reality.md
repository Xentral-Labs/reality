# From ERP Documents to Business Reality

[Back to the guide overview](../business-reality-guide)

## Foundations {#foundations}

### The familiar ERP picture

In your ERP, you find a sales order through its header, lines and linked documents. You see what was
ordered, reserved, delivered and invoiced. Warehouse journals, open items and document flow help you
explain those figures. This remains useful business knowledge.

Reality gives these statements explicit responsibilities. The order document records the order
received. Separate operational records hold what was promised, allocated, moved or posted. The
current position is derived from those records. This separation matters more than the table count.

### One order, several questions

Huber orders 30 bicycle lamps from Acme. The order is recorded and Acme has created a delivery
promise for 30. Eight lamps are in stock. Nothing has been reserved or shipped yet.

“Is the order open?” now needs a more precise answer:

| Business question                   | Answer in this case | Basis                                            |
| ----------------------------------- | ------------------- | ------------------------------------------------ |
| What did Huber order?               | 30 lamps            | Recorded order and line                          |
| What must Acme still deliver?       | 30 lamps            | Delivery promise with no fulfilling shipment yet |
| Which goods are allocated to Huber? | None yet            | No active reservation                            |
| What has shipped?                   | Nothing             | No recorded shipment                             |

The **delivery promise** is a **Commitment**: who should supply what quantity to whom. A
**Reservation** allocates existing stock to that promise. A **Movement** records a physical goods
movement, such as a shipment out of the warehouse.

When Acme later ships 18 lamps and records that shipment against the promise, twelve remain open.
That answer comes from 30 promised and 18 delivered. The order needs no delivery-status field of its
own. A screen can still say “partially delivered”; the promise and shipment explain that label.

### Why the order document remains

The document answers another question: “Which commercial statement did we record?” Reality calls the
document a **Document** and its line a **DocumentLine**. The document and promise are linked. You
can follow an outstanding delivery back to the line that supports it.

This matters when something changes. If Huber later requests a different quantity, a recorded
shipment does not disappear. The changed request and the work already done need a business
resolution. Chapter 2 explains those paths.

### How does Reality know what was ordered?

An order can arrive through a supported connection or through a supported manual order operation.
Reality preserves the original input unchanged. This provenance record is a **SourceRecord**. It
lets you ask later: “Did the input actually say that?” A source can be wrong; preserving it makes
its statement checkable, not automatically correct.

The supported importer or manual order operation creates the appropriate documents and delivery
promises through defined rules. An arbitrary file or document does not automatically create a
promise.

The sequence **Source → Evidence → Reality** therefore has a practical meaning:

| Layer                                   | In our order                            | Purpose                                      |
| --------------------------------------- | --------------------------------------- | -------------------------------------------- |
| Source: original input                  | Submitted or manually entered order     | Check what was originally stated             |
| Evidence: recorded commercial statement | Order and line                          | Record the order we accepted into the system |
| Reality: operational records            | Promise, later reservation and shipment | Run and explain the work                     |
| Derived answer                          | Twelve remain after shipping 18         | Answer a current business question           |

This is a path for traceability. Not every case needs every stage. Unexpected goods can be received
without an existing supplier promise. Missing documents are not invented to complete a chain.

## What carries over from ERP work {#data-model}

Customers, suppliers, items, locations and postings retain their familiar meanings. One business
partner can have several roles, such as customer and supplier. Showing an operational answer on a
partner or document screen does not make that record own the answer.

| Familiar question                         | Authoritative basis in Reality                         |
| ----------------------------------------- | ------------------------------------------------------ |
| What is in the warehouse?                 | Recorded receipts and issues: Movement                 |
| How much remains available?               | Stock less active Reservation                          |
| What do we still owe the customer?        | Commitment less fulfilling Movement                    |
| What does the customer owe on an invoice? | Postings and applied settlements                       |
| What else did the source say?             | Original input, and where appropriate a supported Fact |

Financial postings are **LedgerEntry** records. Chapter 3 explains their allocation to invoices. A
**Fact** records particular source-backed additional information; chapter 6 covers that. You do not
need either concept in detail yet.

Work lists prepare answers for people and agents. A list is a **View**; a rebuildable prepared read
model is a **Projection**. The list helps you work, while the underlying records explain its
figures. An outdated list cannot authorise reserving or shipping more than current operational
records allow.

## Three rules to remember {#reality-model}

1. **Read the document and its execution separately.** An order does not prove shipment. A
   reservation does not prove goods left the warehouse.
2. **Separate received values from derived answers.** A stated invoice amount is recorded as
   received. Open quantity, stock and outstanding amount are derived from their respective bases.
3. **Be able to inspect an answer's basis.** A number leads to operational records and, where
   available, through documents to the original input.

<details>
<summary>Technical detail: identity, provenance and tables</summary>

Order numbers such as `SO-1001` help people search. Relationships use opaque internal IDs so equal
numbers from different systems are not confused. Every business record and query belongs to a
tenant. Records in another tenant behave as not found.

A Reservation points directly to its Commitment. The Commitment's document and source links avoid
extra provenance links on the Reservation. SourceRecord records are immutable; changed external
content is preserved as a new version. Operational lifecycle states can change. The model therefore
does not promise full reconstruction of every historical state.

The [table map and detailed explanations](../../reference/table-map) cover master data, source
processing, documents, promises, movements, postings and read models. Their business responsibility
is enough for this first pass.

</details>

### Check your understanding

Huber's 30 lamps are ordered. Eight are reserved and none have shipped. How many remain to deliver,
and how many of those are already allocated?

<details>
<summary>Show answer</summary>

Thirty remain to deliver; eight are allocated. Reserving does not fulfil a delivery promise. That
requires a recorded actual shipment against the Commitment.

</details>

Next: [Follow Huber's order through warehouse and purchasing](./02-orders-stock-and-deliveries).
