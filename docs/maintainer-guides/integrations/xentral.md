# Connect Xentral

[What data do I need first? Example ERP step by step](./example-erp.md) explains a small entry scope
and successive stages.

This guide moves from business scope to acceptance, separating existing templates from work still
required.

## What complete means

Completeness is **relative to the selected mode and question**. A small observation entry scope does
not need the entire matrix. The following areas describe the possible broader scope to grow into.

Connect sales, purchasing, warehouse and finance for an agreed Xentral company/project scope.
Include returns, transfers and corrections where used. Add production, bills of materials,
lots/serials, price conditions or other modules to the scope sheet when business processes depend on
them; the base example does not prove these modules. “100 %” means all agreed processes have
verified coverage or an explicit external authority, not every Xentral field.

## Operating modes

### B) Observe Xentral

**Xentral runs the ERP processes; Reality observes and explains.** The adapter accesses Xentral
read-only. It captures articles, business partners, orders, purchase orders, stock/warehouse
execution, invoices, credits, payments and returns within the agreed scope. Each original
`SourceRecord` is interpreted through shared services into local Evidence and Reality records; this
mode makes no changes in Xentral.

Xentral and the named external authorities own allocation, releases, shipping, billing and finance.
Reality explains supported stock, open quantities, obligations and exceptions from the captured
facts. It does not introduce its own operational decisions. Preserve source document statuses as
source evidence; derive delivery/reservation/payment state from Reality records rather than adding
those statuses to Documents.

**Example:** Xentral records an order for 10 units, actual outflow of 4 and an invoice stating its
own amount. Reality links those facts and explains what remains to deliver and invoice, once the
required interpreters are implemented. A delivery-note creation alone is insufficient shipment
proof. Finding a discrepancy does not automatically correct Xentral.

Unlike [A) Observe Shopify](./shopify.md#a-observe-shopify), this scope can also include supplier
promises, receipts and legal financial documents from the ERP. Use the acquisition table below and
verify each source area in the coverage matrix. These are target operating contracts, not a claim
that the Xentral integration is already implemented.

### C) Reality decides, Xentral executes

**Reality owns the agreed operational decisions; Xentral carries them out.** Start with mode B's
read path, then add separately reviewed outbound operations. Xentral can remain the interface for
article/address maintenance, order entry, warehouse execution, labels, legal invoice creation and
accounting export. Master ownership is assigned per decision, not to every field of an application.

**Reality directs; Xentral executes requested operations.** “Passive” refers to the transferred
decisions: Xentral does not initiate those operations independently. Command processing, technical
validation and warehouse workflows remain active.

**Execution means that Reality issues the Command specifying what Xentral should do and when.** For
example: “Release order X with these lines for shipping” or “Create an invoice for order X.” Xentral
processes the requested operation and returns success, failure and resulting evidence. These are
business examples, not implemented Command names or verified API calls. A shipping release directs
the warehouse workflow; the warehouse still performs physical shipment.

| Area                                                      | Responsible system                                                 |
| --------------------------------------------------------- | ------------------------------------------------------------------ |
| Master data and original order entry                      | Xentral or the named original source                               |
| Allocation, credit/payment release and shipping selection | Reality, for explicitly transferred decisions                      |
| Picking, packing, labels and actual warehouse execution   | Xentral / the responsible warehouse                                |
| Decision to request an invoice                            | Reality, if included in the reviewed scope                         |
| Legal invoice amounts, tax, PDF and accounting export     | Xentral / the responsible accounting source; capture stated values |
| Payment and warehouse facts                               | The actual execution source; return as immutable evidence          |

**Example:** An order for 10 units arrives from Xentral. Reality proposes releasing 4 units after
its shared services check the relevant conditions. A person explicitly confirms a mutating
agent/chat Command. A separately designed outbound adapter requests the supported Xentral operation
with an idempotency key. Xentral executes picking/shipping. Reality records fulfillment only when
the responsible source supplies actual execution evidence for those 4 units; a request,
delivery-note creation or tracking number alone is insufficient. A scoped invoice request follows
the same request/execution/evidence pattern. Timeout or contradictory feedback stays visible for
review.

Transfer one decision at a time. Before enabling it, review and disable or coordinate competing
Xentral automation for that exact decision. Preserve unrelated Xentral responsibilities. Record
confirmation, correlation, retries and reconciliation; a retry must not create a second shipment or
invoice. Agent/chat mutations require human confirmation. Automatic rules need their own explicit
reviewed execution contract; a rule is not a substitute for that confirmation boundary.

This mode is **not implemented by the connector shell**. An outbound outbox/external-effect handler
requires a separately reviewed scheduling design. The existing read adapter and proposed polling
intervals do not implement outbound execution. Start in B, verify the evidence chain, then transfer
a narrow decision under that design.

## Before you start

Use a test instance or an authorized export, identify the installed API/resource versions and
confirm the actual authentication/permission contract. Xentral documents products and sales orders
across different API versions; do not assume one version prefix works for every object. Record
company/project boundaries, locations, units, currencies, time zones, pagination and
modification/deletion visibility. Keep credentials in the adapter’s secret configuration, outside
payloads and fixtures. Read the [From source data to Reality](./connector-contract.md).

## Current implementation

The `xentral` shell in `packages/reality-core/config/connector_catalog.yaml` advertises `order`,
`purchase_order`, `article`, `contact` and `payment`. There is no Xentral pair in
`SOURCE_INTERPRETERS` in `services/core.py`. Vendor transport, object interpreters, cross-object
identity resolution and production verification must be implemented. Invoice, movement and other
needed source types also need reviewed catalog/capability additions. Capturing a payload alone is
not business interpretation.

## Coverage matrix

**Small entry scope for B: explain orders.** Capture orders/lines, relevant changes/cancellations
and the item, party and source identities needed for interpretation. Existing Reality master records
can supply context; a full master-data import is not automatically required. Add shipping, payments,
purchasing and returns only for the corresponding questions.

This matrix is **not a mandatory list for every observation deployment**. “Baseline” applies to this
entry scope; other rows are required only for their stated goal. Without execution evidence, you can
display an order but cannot claim a reliable open delivery quantity.

C also follows the selected scope: controlling invoice creation does not require controlling
purchasing or production. Capture the inputs for transferred decisions plus the reviewed outbound
Command path and resulting evidence.

| Source area                    | Mode and necessity                                             | What to capture                                                               | Reality purpose                                                                | Work still required                                                                      |
| ------------------------------ | -------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Articles, contacts, locations  | B: Baseline context; C: decision context                       | Stable object IDs, variants, units, party roles, warehouse identity           | Item, Party, Location and source references                                    | Master-data transport and interpreters; explicit ambiguity handling                      |
| Sales orders and lines         | B: Baseline; C: order decisions                                | IDs, stated quantities/amounts/dates, revisions, cancellations                | Document/DocumentLine and customer Commitments                                 | `order` interpreter and update policy                                                    |
| Purchase orders and receipts   | B: Observe purchasing; C: control purchasing                   | Supplier promises, line IDs, arrivals and actual receipt evidence             | Supplier Commitments and receipt Movements                                     | `purchase_order` plus receipt transport/interpretation                                   |
| Stock                          | B: Observe stock; C: stock decisions                           | Cutover quantities by location; later movements, transfers and corrections    | Opening and subsequent stock evidence/Movements                                | Stock source types, cutover and movement interpreters                                    |
| Reservations and deliveries    | B: Explain allocation/delivery; C: control shipping/allocation | Allocation identity, actual delivery line links, reversals                    | Reservations and fulfillment Movements                                         | Separate allocation/execution interpretation; avoid deriving shipments from order status |
| Invoices and credit notes      | B: Check invoicing; C: request invoices                        | Sales/purchase direction, line amounts, tax, currency, due terms              | Financial Evidence and appropriate shared finance services                     | Financial source types and interpreters; no new ledger rule in transport                 |
| Payments and allocations       | B: Check cash; C: payment/credit release                       | Transaction IDs, currencies, amounts, invoice links                           | Shared payment/settlement path; LedgerEntry only under its accounting contract | `payment` interpreter and allocation semantics                                           |
| Returns/refunds                | B: Check returns; C: related decisions                         | Announcement, receipt, credit and cash refund as separate evidence            | Return and financial services                                                  | Supported return source types and resolution links                                       |
| Optional modules               | B/C: Used modules only                                         | Production/BOM, lots/serials, pricing or other scoped records                 | Existing supported domain services or separately specified extension           | Assess each module; do not declare it covered by sales/stock import                      |
| Outbound Commands and feedback | C only: each transferred operation                             | Confirmed request, idempotency/correlation key, result and execution evidence | Separate requested operation from proven execution                             | Separately reviewed adapter/scheduling design; B needs no write permissions              |

## Step by step

### How and when to fetch data

Fetch only the source areas selected in your matrix scope; this table does not require every read
for every mode. Observation needs authorized read access only.

Start with **paginated API reads**, then add verified Webhooks per resource. Do not assume a
Shopify-style Bulk API. These intervals are **recommended starting values**, not vendor guarantees
or an implemented Reality connector. Verify resources, filters, permissions and event subscriptions
in the actual installation.

| Data                                        | Initial capture                                           | Ongoing capture                                                            | Suggested interval                                          |
| ------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Articles, contacts and locations            | Page through required master records                      | Supported incremental reads, otherwise paginated comparison                | Hourly for active master data; broader daily reconciliation |
| Sales and purchase orders                   | Open records with lines; required history separately      | Supported changed-record queries; available Webhooks only after testing    | Every 5–15 minutes                                          |
| Stock and movements                         | Opening stock by location at the agreed cutover           | Read `/api/v3/stockMovements`; periodically compare current stock          | Every 5–15 minutes; daily reconciliation                    |
| Delivery and warehouse execution            | Delivery notes, shipments and required execution evidence | `salesOrder.dispatched`, `deliveryNote.created`; then fetch object details | React to events; reconcile every 5–15 minutes               |
| Invoices, credits, payments and allocations | Open financial items and scoped original records          | Paginated reads; add verified resource events if available                 | Every 15–60 minutes; daily financial reconciliation         |
| Returns and optional modules                | Read each agreed source separately                        | Resource-specific queries/events; prove coverage before activation         | Start at 15–60 minutes; shorten when operations require it  |

Xentral documents [stock reads](https://developer.xentral.com/docs/read-stock) and
[stock movement reads](https://developer.xentral.com/reference/getapi-v3-stockmovements). Keep
opening quantities separate from subsequent movements. Never infer movement history from snapshot
differences alone. Only use modification filters actually supported by each endpoint; otherwise
compare paginated records and retain source identities/versions.

The [fulfillment guide](https://developer.xentral.com/docs/fulfillment) documents the two named
Webhooks and detail reads such as `/api/v1/salesOrders/{id}` and `/api/v3/deliveryNotes/{id}`.
`salesOrder.dispatched` starts fulfillment; it does not prove physical shipment. Delivery-note
`sent` describes document communication. Tracking creation alone also does not prove carrier
handover. Import the responsible warehouse's execution evidence for that fact.

Before baseline capture, durably buffer available events. Record the cutover and replay subsequent
versions after importing opening records, reconciling changes during pagination. A durable
checkpoint advances only after successful capture. Use overlapping change windows where supported,
idempotent replay, bounded retries and shared scheduled jobs with rate-limit backoff. Reconcile the
scoped identities and quantities daily; show last success and backlog. Missing events or filters
require a documented polling strategy, not a claimed complete live integration.

### Implementation sequence

Shared ingest stores the original payload as a `SourceRecord` and creates an `ImportJob`. Only the
registered interpreter maps its meaning into Evidence and Reality.

1. Agree a source-authority sheet. If Shopify sends the same sale, choose the order authority and
   preserve both source identities without creating two promises.
2. Capture real article, contact, location and order fixtures. Document source ID, line ID, version
   and Xentral project/company boundary. Store raw responses without normalization loss.
3. Implement the adapter through `services/core.py::enqueue_source`; provide
   `(source_system, source_type)`, original payload and context. Follow `process_import_job` and the
   shared source lifecycle. An unknown interpreter must remain visibly `unmapped`.
4. Implement and register each required interpreter. Start with master identities and `order`, then
   purchasing, stock/delivery and finance. Follow `_shopify_interpretation` for version/provenance
   structure, not as an Xentral field mapping.
5. Choose a cutover timestamp. Import opening quantities and open financial items using supported
   services; process subsequent movements once. Never add the entire earlier movement history on top
   of the opening snapshot.
6. Implement incremental retrieval with a durable checkpoint, overlapping reads and idempotent
   replay. Determine whether this installation supplies usable webhooks; otherwise use supported
   polling through shared scheduled jobs. Never assume an undocumented webhook exists.
7. Test order revisions, delivery reversals, invoice credits and payment allocations independently.
   Preserve stated amounts and historical Evidence. Use the shared finance services rather than
   recomputing postings from document statuses.
8. Reconcile the scope by source identity and business values, then enable recurring intake. Treat
   any upstream write-back as a separate reviewed operation.

## End-to-end acceptance story

The following story tests a broader scope. For small observation entry, verify order import,
changes, identity resolution and replay. Other steps become acceptance criteria only when you select
their corresponding goal; test confirmed outbound operations separately for C.

This is a **proposed acceptance scenario for your integration**, not a claim that all these source
types are implemented. Use original fixtures from each responsible system. Monetary amounts are
explicitly stated in those fixtures, not recalculated from quantities by this guide.

| Step                | Source evidence/action                                                                                   | Expected result                                                                                         |
| ------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 1. Baseline         | Item, customer, warehouse and opening 10 units; open order for 10 units stating 100 EUR total            | Order/line Evidence and Commitment; physical 10, reserved 0, available 10                               |
| 2. Allocation       | Responsible source or confirmed Reality Command reserves 4 units                                         | Physical 10, reserved 4, available 6; no second Reservation for the same allocation                     |
| 3. Partial shipment | Actual outflow of 4 linked to order/line                                                                 | Physical 6, reserved 0, available 6; fulfilled 4, open delivery quantity 6                              |
| 4. Invoice/payment  | Original invoice states 40 EUR; successful payment states 40 EUR and invoice allocation                  | Preserve both values; explain financial allocation without inferring payment from order status          |
| 5. Cancel remainder | Later order version cancels the remaining 6 units                                                        | Preserve original Evidence and execution of 4; open delivery quantity 0                                 |
| 6. Return/refund    | Return of 2 shipped units, evidenced receipt of 2, credit of 20 EUR and successful cash refund of 20 EUR | Physical 8; announcement, receipt, credit and cash event separately linked; no duplicate refund posting |
| 7. Replay           | Deliver all original versions again and an old version after a newer version                             | No second promise, shipment, refund or return receipt; do not revert current state                      |

In read-only integrations, step 2 imports the existing external allocation. A confirmed Reality
Command is a separate operating mode. Do not use both as independent reservations. Receiving a
return does not automatically reopen the fulfilled delivery promise.

Add purchasing: a supplier promises 5 units, delivers 3, then 2. Open incoming quantity: 5 → 2 → 0;
stock increases only on actual receipt. If purchasing belongs to another system, obtain this case
from the additional source named in scope.

## Verify and operate

For each source type, verify original payload, stable identity, version, tenant, provenance and
actual business result. In the story above, quantities and stated amounts match the responsible
source. Report missing or uninterpreted records explicitly; HTTP success is not acceptance evidence.

Also test unknown items/partners, missing quantities/prices, units/currencies, holds, ambiguity,
deletion/archiving, partial failure, expired permissions, API limits, recovery replay and foreign
tenant/company IDs. Unsupported changes remain reviewable rather than silently overwritten.
Reconciliation must not fabricate corrective movements.

Agree freshness, intake lag, error/review ownership, alerting, periodic quantity/amount
reconciliation and recovery. Read `docs/features/scheduled-jobs.md` before recurring intake. Apply
the [shared acceptance checklist](./connector-contract.md#completeness-and-acceptance).

## References and next steps

Vendor references checked on 2026-10-03. Use the version applicable to your installation; these
links are not implementation claims.

- [Xentral product/API example](https://developer.xentral.com/docs/create-a-product-v2-api)
- [Xentral sales-order lifecycle](https://developer.xentral.com/docs/create-sales-order-xentral-api-guide)
- [Xentral stock reads](https://developer.xentral.com/docs/read-stock)
- [Xentral stock movements](https://developer.xentral.com/reference/getapi-v3-stockmovements)

Repository templates: `packages/reality-core/tests/test_source_ingestion.py`,
`test_shopify_and_explain.py`, `test_shop_order_changes.py`, `test_shop_refunds.py` and
`test_shop_line_gaps.py`. They prove their existing services, not a complete live Xentral connector.

[From source data to Reality](./connector-contract.md) · [First pilot](./parallel-test.md) ·
[Develop interpreters](../development/connectors.md)
