# Connect Odoo

[What data do I need first? Example ERP step by step](./example-erp) explains a small entry scope
and successive stages.

This guide moves from business scope to acceptance, separating existing templates from work still
required.

## What complete means

Completeness is **relative to the selected mode and question**. The following areas describe the
possible broader scope, not mandatory coverage for small observation entry.

Define coverage by installed modules and company: sales, purchase, inventory and accounting are the
baseline when used. Manufacturing/BOM, projects/services, subscriptions, lots/serials, pricing,
analytic accounting and custom modules need their own explicit coverage if relevant. “100 %” means
every agreed company/process is verified, not importing every model in the Odoo database.

## Operating modes

### Read only: observe Odoo

**Odoo runs the processes; Reality reads and explains.** Grant only the read permissions needed for
the selected companies and source areas. Original `SourceRecord` payloads are interpreted into local
Evidence and Reality records. Reality makes no upstream writes and requests no Odoo operation in
this mode.

A small entry scope needs orders, lines, relevant changes and required identities. Stock, delivery,
invoice or payment data is needed only for the corresponding observations and exceptions. Capturing
every installed Odoo module is not a prerequisite for observation.

**Example:** Reality captures an order for 10 units and shows its stated promise. Explaining that 6
remain to deliver additionally requires evidenced execution of 4 units. Without that source,
delivery progress stays unknown; Reality does not request shipping. Existing Odoo automation can
continue to direct the processes.

### Reality directs, Odoo executes

**Reality specifies what Odoo should do and when.** Examples include “Release order X with these
lines for shipping” or “Create an invoice for order X.” Odoo processes the requested operation,
performs its business and technical validation, and returns the result and resulting evidence. These
are business examples, not implemented Command names or verified API calls. Verify supported
methods, rights and workflows for the actual version and installed modules.

Transfer authority per decision. Odoo can retain master-data maintenance, order entry, picking,
actual shipping, legal invoice creation and accounting. Review and disable or coordinate competing
Odoo automation for transferred decisions before activation. “Passive execution” means no
independent control of those decisions; technical validation and warehouse work remain active.

**Example:** Reality proposes releasing 4 units of order X for shipping. Mutating agent/chat
Commands require human confirmation. A separately reviewed adapter requests the operation with
idempotency and correlation keys. Reality records fulfillment only from actual execution evidence; a
request, planned picking or label alone does not prove physical shipment. Timeouts stay visible and
retries must not create a second operation.

This execution is **not implemented by the connector shell**. It requires a separately reviewed
outbound adapter with durable feedback, retries and reconciliation under the shared scheduling
contract. Automatic rules need their own explicit reviewed execution contract. Start with reading
and then transfer a narrow decision; purchasing or manufacturing is not universally required.

## Before you start

Identify Odoo version, hosting/edition, installed modules, companies and the dedicated integration
user’s record/field permissions. For Odoo 19 JSON-2, official documentation describes
`/json/2/<model>/<method>`, Bearer API keys and database-specific models/fields at `/doc`; its
published plan conditions must be checked for your deployment. Other versions need their own API
contract. Inspect actual field definitions and relations rather than assuming all installations
match. Read the [From source data to Reality](./connector-contract).

## Current implementation

The `odoo` shell in `packages/reality-core/config/connector_catalog.yaml` advertises `sale.order`,
`purchase.order`, `product.product`, `res.partner` and `account.move`. There is no Odoo pair in
`SOURCE_INTERPRETERS` in `services/core.py`. Transport and all object interpreters must be
implemented. Candidate line/stock/payment models below are a discovery checklist to verify against
the installed database, not registered Reality capabilities or a guaranteed API schema.

## Coverage matrix

**Baseline for observation:** orders/lines, relevant changes and required identities/context.
Existing Reality master data can supply context; a full master-data import is not automatically
required. This matrix is **not a mandatory list**. Additional data serves the stated goal. For
execution, add only the inputs and outbound Command path for transferred decisions.

| Source area                    | Mode and necessity                                            | Candidate models/records to verify                                                          | Reality purpose                                              | Work still required                                                                                   |
| ------------------------------ | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| Master identities              | Read: Baseline context; Execute: decision context             | `product.product`, `res.partner`, companies, units, warehouse/location relations            | Item, Party, Location and source references                  | Identity interpreters; define company scope and shared partner handling                               |
| Sales                          | Read: Baseline; Execute: order decisions                      | `sale.order` and related order lines, dates/revisions/cancellations                         | Document/DocumentLine and customer Commitments               | `sale.order` interpreter; line/version contract                                                       |
| Purchasing                     | Read: Observe purchasing; Execute: control purchasing         | `purchase.order` and related lines, receipts                                                | Supplier Commitments and receipt Evidence                    | `purchase.order` plus receipt interpretation                                                          |
| Stock                          | Read: Observe stock; Execute: stock decisions                 | Location quantities; executed `stock.move`/move-line records and transfers                  | Opening/receipt/issue/transfer Movements                     | Verify installed fields, done quantities, units and cutover; do not import planned moves as execution |
| Reservations/deliveries        | Read: Delivery progress; Execute: control shipping/allocation | Picking/line allocations and executed operations                                            | Reservations and fulfillment links                           | Distinguish allocation, planned quantities and executed quantities                                    |
| Financial documents            | Read: Check invoicing; Execute: request invoices              | `account.move` and lines, document type, stated amounts/tax/currency/terms                  | Financial Evidence and shared finance services               | Classify invoice, bill, credit and journal semantics; no blanket invoice interpretation               |
| Payments/settlement            | Read: Check cash; Execute: payment/credit release             | Installed payment and reconciliation records, invoice links                                 | Shared payment/settlement services                           | Payment/reconciliation interpreters; posted invoice alone is not evidence of payment                  |
| Returns                        | Both: Return questions/decisions only                         | Return stock operations, credit documents and refund transactions                           | Return receipt and financial services                        | Separate physical and financial identities; preserve original links                                   |
| Optional modules               | Both: Used modules only                                       | Installed manufacturing/BOM, lot/serial, service/subscription, pricing and analytic records | Existing domain capability or separately specified extension | Scope and test each dependency; do not claim base coverage                                            |
| Outbound Commands and feedback | Execution only: each transferred operation                    | Confirmed request, idempotency/correlation key, result and execution evidence               | Prove requested operation and actual execution separately    | Separately reviewed adapter and scheduling contract; observation needs no write permissions           |

## Step by step

Apply the following steps only to your selected source areas. Small read-only entry does not require
full stock, purchasing or finance import. Writes belong exclusively to separately reviewed
execution.

Shared ingest stores the original payload as a `SourceRecord` and creates an `ImportJob`. Only the
registered interpreter maps its meaning into Evidence and Reality.

1. Record an explicit company/module/authority scope. Choose which Odoo company maps to which
   Reality tenant and how shared partners/products are resolved; never use ambient company context
   as tenant authorization.
2. Inspect the database’s model/field contract and capture real master/order/line/stock/financial
   fixtures with their relations. Record original opaque source IDs, company and
   version/modification identity.
3. Implement the version-appropriate authenticated adapter. Capture related lines as well as
   headers; relation IDs alone do not supply quantities, amounts or execution evidence. Preserve
   original record values and envelopes.
4. Submit through `enqueue_source`/`process_import_job`, implement tenant-scoped interpretation and
   register each source pair. Extend the shell only for the proven additional source types. Follow
   existing import tests for unknown/held/error outcomes.
5. Define a cutover with open sales/purchase promises, inventory and open financial balances.
   Classify historical, planned, reserved and executed operations before processing subsequent
   changes; avoid counting a picking and its move lines twice.
6. Read incrementally using an installation-proven modification cursor plus stable ordering, overlap
   and reconciliation. Preserve archiving/deletion signals or document how missing records are
   investigated. Poll through shared scheduled jobs unless a separately proven event adapter exists.
7. Map invoice/credit/payment/reconciliation meaning through shared finance services. Keep
   source-stated prices, taxes and totals; verify units and currencies rather than recomputing
   received amounts.
8. Run the acceptance story for each company and relevant module. Verify cross-company isolation and
   restricted records. Enable recurring intake only after reconciliation; treat Odoo writes as a
   separate approved application capability.

## End-to-end acceptance story

This story tests a broader scope. For small read-only entry, verify order import, changes, identity
resolution and replay. Other steps apply only to the selected question; additionally verify outbound
Commands and feedback only for execution.

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
the [shared acceptance checklist](./connector-contract#completeness-and-acceptance).

## References and next steps

Vendor references checked on 2026-10-03. Use the version applicable to your installation; these
links are not implementation claims.

- [Odoo 19 external JSON-2 API](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)

Repository templates: `packages/reality-core/tests/test_source_ingestion.py`,
`test_shopify_and_explain.py`, `test_shop_order_changes.py`, `test_shop_refunds.py` and
`test_shop_line_gaps.py`. They prove their existing services, not a complete live Odoo connector.

[From source data to Reality](./connector-contract) · [First pilot](./parallel-test) ·
[Develop interpreters](../development/connectors)
