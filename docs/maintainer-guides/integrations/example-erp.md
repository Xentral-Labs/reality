# Connect an example ERP step by step

You are building an autonomous system: **your agent should understand what was promised, what is
missing and what needs to happen next.** It needs reliable facts in Reality. You do not need to
connect an entire ERP at once; start with a question your agent should answer. This chapter uses a
fictitious **Example ERP** to show how its capabilities grow with captured data.

The agent reads through Reality’s shared application tools and services. The connector captures
sources; interpreters make their meaning usable. Permitted agent operations are explicitly defined
separately: more data does not automatically grant write permissions. The agent capabilities below
describe target scope after verified implementation, not an already-running autonomous integration.

**Connecting starts with reading:** the ERP supplies original records and Reality interprets them.
You do not need to implement new allocation, shipping or invoicing logic in the ERP for observation.
You need an authorized export/read API and a suitable Reality interpreter. These examples describe
proposed integration scope, not an implemented Example ERP connector. Outputs are illustrative
business answers, not screenshots or executable API responses.

## The small beginning

Our company sells **Blue Chair**. Customer **Mira** orders 10 units. We start at an agreed
**cutover**, before this new order has any delivery, allocation or revision. There is no unknown
earlier execution for this order.

| Stage | Additional capture                       | Question your agent can answer               |
| ----- | ---------------------------------------- | -------------------------------------------- |
| 1     | Identities, orders and changes           | What item has our company promised to whom?  |
| 2     | Actual deliveries                        | How much remains to ship?                    |
| 3     | Opening stock and actual movements       | How much is currently in the warehouse?      |
| 4     | Supplier promises and linked receipts    | What is still expected to arrive?            |
| 5     | Existing reservations                    | What has already been allocated?             |
| 6     | Invoices and payments                    | What has been invoiced and paid?             |
| 7     | Confirmed outbound Commands and feedback | What should the ERP do at Reality's request? |

These stages are a learning path, not a mandatory sequence. Stop after 1 or 2, or add finance first
if that is your question; the necessary dependencies must exist. Existing orders require a contract
for open promises and earlier execution already at stage 1. Otherwise “no delivery imported” means
**unknown**, not “nothing delivered”.

## 1. Items, customers and orders: make promises visible

**Capture from the ERP:** required item/customer identities, units, order/line IDs, stated
quantities and dates, and relevant subsequent changes/cancellations. Master records can be mapped
once; you do not need to synchronize every article/address field. External IDs identify records. SKU
and human order numbers are display values, not implicitly unique keys.

Example IDs: item `item_b7`, customer `party_m2`, order `order_q9`, line `line_k4`. The line
promises 10 Blue Chairs to Mira. Preserve the original payload and version:

```text
SourceRecord → Document → DocumentLine → Commitment
                                           Mira: 10 Blue Chairs promised
```

**Output:** your agent can list promises by customer or item. Our explicitly new order needs
delivery of 10 units. For an older order with unknown execution history, initially show only its
captured promise. A calculated open quantity must not be presented as established truth without
complete execution coverage.

**Still unknown:** actual shipment, stock, allocation and payment.

**Your agent:** It can look up and explain promises by customer or item. For older orders with
incomplete history, it identifies delivery progress as unknown.

**Check:** importing twice creates one promise. A subsequent cancellation is a new source version
processed under the reviewed change contract, not a second order.

## 2. Actual deliveries: what remains to ship?

**Add:** actual execution with its own event/line identity, item, quantity, time and order-line
link. Include reversals/corrections in the selected scope. A delivery note, label or shipping
release alone does not prove physical outflow.

The warehouse reports actual shipment of 4 units from `line_k4`. A reviewed interpreter uses shared
services to link execution to the promise; appropriate `Movement` records evidence execution.

| Customer | Item       | Promised | Delivered | Remaining |
| -------- | ---------- | -------- | --------- | --------- |
| Mira     | Blue Chair | 10       | 4         | 6         |

**Output:** “Mira still needs 6 chairs” is now evidenced. Your agent can aggregate open quantities
by item across orders with complete capture.

**Still unknown:** whether those 6 are available. An outgoing delivery alone does not establish
complete stock. Return receipt and reopening a promise also need a separate reviewed contract;
returned quantity does not automatically create a new delivery obligation.

**Your agent:** It can answer “What item do we still owe to whom?” and aggregate evidenced delivery
remainders by customer or item. Read-only mode does not issue shipping requests.

**Check:** replay execution. Delivered stays 4, not 8; remaining stays 6.

## 3. Opening stock and receipts: what is in the warehouse?

**Add:** reliable opening quantities per item/location/unit at a fixed boundary and all subsequent
physical movements relevant to that warehouse scope: receipts, issues, transfers, corrections and
return receipts. A receipt needs its own identity, quantity, location and time. Without a purchase
line link, it can answer stock questions while supplier-promise allocation remains unknown.

Open stock **after stage 2's shipment**: 3 units are now in the warehouse. The earlier shipment of 4
still fulfills the order, but must not be subtracted again from the later opening snapshot. A
subsequent actual receipt adds 3 units.

```text
Opening stock at warehouse cutover: 3
Subsequent actual receipt:          3
Physical stock now:                 6
Open customer promise:              6
```

**Output:** “6 in stock; Mira still needs 6.” This does not establish that Mira can receive all 6:
other reservations, holds, locations or conditions may matter.

**Still unknown:** future receipts and existing allocation. A snapshot does not replace movement
history. Do not invent movements from snapshot differences or present available-to-sell source
quantities as physical stock.

**Your agent:** It can compare open demand with captured physical stock and explain what allocation
or hold data is missing for a reliable release.

**Check:** count opening and subsequent movements once. Reconcile cutoff quantities with the ERP. A
late-arriving earlier movement must not change the later snapshot a second time.

## 4. Purchase orders: what is expected to arrive?

**Add:** supplier identity, purchase orders/lines, stated quantities/dates, changes/cancellations
and actual receipt links to the purchase line. A purchase order is a promise, not stock.

A supplier promised 5 units. Stage 3's receipt of 3 belongs to this purchase order. The interpreter
creates a supplier `Commitment` and links the existing receipt without recording another stock
movement.

**Output:** “3 received, 2 still expected.” Physical stock remains 6; the expected 2 increase it
only when actually received. A stated date helps your agent explain expected arrivals; a forecast
remains separate from current stock truth.

**Still unknown:** which stock is already allocated to customers.

**Your agent:** It can explain outstanding supplier quantities and stated dates alongside customer
demand. Expected goods are not treated as stock already on hand.

**Check:** import the purchase order and receipt out of order. Receipt is counted once and supplier
remainder is 2.

## 5. Reservations: what is already allocated?

**Add:** existing allocations with stable identity, customer-promise link, item, location and
quantity, including releases and consumption. A bare ERP field “reserved: 2” still needs a
relationship/version contract before its meaning is known.

Within the agreed warehouse scope, 2 of the 6 units are reserved for another customer promise.
Shared services retain the allocation as a `Reservation` linked to its `Commitment`.

**Output:** “Physical 6, reserved 2, calculated available 4; Mira still needs 6.” This explains a
quantity gap in the selected scope. Operational release may require additional holds/rules.
Observation does not create a competing independent ERP allocation.

**Your agent:** It can identify quantity gaps despite physical stock and propose an allocation for
review. Creating a reservation is a separately authorized operation.

**Check:** replay, release and actual consumption update the same allocation under its contract,
without double-counting reservations or outflow.

## 6. Invoices and payments: what is financially open?

**Add:** original financial documents with stated amounts, currency, tax, due terms and order/line
links; actual payments with their own identity, amount, currency and allocation. Credits and refunds
are separate events.

An invoice states 80 EUR; a successful allocated payment states 30 EUR. Under the agreed finance
contract, 50 EUR remains open. Both source amounts are preserved; Reality does not manufacture a
replacement invoice amount from quantity and price.

**Output:** your agent can explain invoicing and payment. A posted invoice does not prove payment;
payment does not prove delivery. This stage is optional when your question concerns delivery only.

**Your agent:** It can explain open invoice amounts and evidenced payments. Payment or credit
release additionally requires reviewed rules and permissions.

**Check:** verify invoice, partial payment, credit and replay separately; original evidence and
allocation stay explainable.

## 7. From observation to control

Reading is sufficient through the previous stages. **Only now add the outbound path:** Reality
issues a Command such as “Release order X for shipping” or “Create an invoice for order X”; the ERP
executes the agreed operation. Only dependencies for the transferred decision are required, not
universally every previous stage.

Mutating agent/chat calls need **human confirmation**. Outbound execution requires a separately
reviewed design for supported ERP operations, permissions, idempotency, correlation, retries and
result reconciliation. Review and coordinate competing ERP automation for the transferred decision.
Automatic rules need their own reviewed execution contract.

**Output:** Reality can direct requested operations. A successful request still is not physical
shipment evidence. Execution and resulting documents return through the read path; timeouts and
contradictions stay visible. These examples do not implement outbound execution.

**Your agent:** It can prepare permitted operations, request them through shared tools and check
feedback. Explicitly reviewed automatic workflows form an observe, assess, act and verify loop.
Missing data or contradictory feedback leaves a case visibly open rather than successfully
completed.

**Check:** repeated requests do not create a second operation. Missing feedback is not displayed as
completed execution.

## What data your agent needs through Reality

In the external system, obtain readable access to selected original objects and lines, IDs,
relationships, versions and required execution evidence. Begin with an authorized fixture/export for
learning; add baseline capture, updates and reconciliation for ongoing operation. A Webhook can
signal a change; authoritative API reads supply missing detail. A daily export only establishes the
last captured state.

In Reality, implement transport to the shared `enqueue_source` boundary, context/identity resolution
and registered interpreters for the selected source types. Transport does not write independent
domain tables and stores raw payloads losslessly. Without an interpreter, a record stays visibly
`unmapped`; merely synchronizing a JSON file does not produce a business answer.

For each source area, record initial scope, complete-history boundary, how changes/cancellations/
deletions/replays are detected, and freshness. Failures make answers visibly stale or incomplete.
Recurring capture uses shared scheduled jobs, not browser timers.

For your first attempt: **stage 1 with a new order, then stage 2 with an actual partial shipment**.
That makes promise versus fulfillment concrete. Add stock and receipts afterwards when you want so
your agent can answer availability questions.

[Technical order example](./order-example.md) · [From source data to Reality](./connector-contract.md) ·
[Shopify](./shopify.md) · [Xentral](./xentral.md) · [Odoo](./odoo.md)
