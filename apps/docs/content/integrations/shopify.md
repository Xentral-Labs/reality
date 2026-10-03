# Connect Shopify

[What data do I need first? Example ERP step by step](./example-erp) explains a small entry scope
and successive stages.

This guide moves from business scope to acceptance, separating existing templates from work still
required.

## What complete means

Completeness is **relative to the selected mode and question**. A small observation entry scope does
not need the entire matrix. The following areas describe the possible broader scope to grow into.

Cover the store’s products/variants, customers, orders, changes, fulfillment and refunds. Name
separate authorities for purchasing, warehouse execution and legal accounting when the store is not
their authoritative source. Shopify plus an ERP/payment provider can cover the agreed business scope
together. “100 %” is the verified combined scope, not all shop settings, marketing content or a full
accounting ledger inferred from order status.

## Operating modes

### A) Observe Shopify

**Shopify runs the store; Reality observes and explains.** The integration accesses Shopify
read-only. Orders, product/variant identities, location quantities, fulfillment, refunds and scoped
payment records arrive as original `SourceRecord` payloads. Supported interpreters create local
Evidence and Reality records; “observe” means no upstream changes, not no local records.

Shopify and the responsible warehouse/payment sources decide and execute the business operations.
Reality shows supported observations and exceptions with their evidence. It neither reserves shop
inventory nor triggers shipping, refunds or invoice creation in this mode. Missing source coverage
stays visible; a shop inventory snapshot does not establish physical movement history.

**Example:** Shopify records an order for 10 units. Later, the responsible source reports shipment
of 4 units. Reality can explain the remaining 6 only after the required order/execution interpreters
and identity links are implemented. It does not send an instruction to ship those 6. A refund
announcement alone also does not prove warehouse receipt or successful cash refund.

Use the acquisition table below for baseline, Webhooks and reconciliation. For purchasing, legal
invoices and warehouse evidence beyond the shop, add the responsible sources. Compare
[B) Observe Xentral](./xentral#b-observe-xentral) when the ERP owns those processes. These are
target operating contracts; the implementation section below identifies existing and missing
capabilities.

For transferring decisions to Reality, see
[C) Reality decides, Xentral executes](./xentral#c-reality-decides-xentral-executes). This is a
separate mode with a reviewed outbound path.

## Before you start

Use a development/test shop and an authorized app with the read permissions and
order-history/customer-data access your scope requires. Pin an Admin API version. Select GraphQL
Admin API for retrieval; verify HTTPS webhook deliveries using Shopify’s documented signature
contract before accepting source data. Bulk operations can support the initial capture. Document
which raw GraphQL/webhook shapes you actually receive. Read the
[From source data to Reality](./connector-contract).

## Current implementation

The `shopify` shell in `packages/reality-core/config/connector_catalog.yaml` advertises
order/product/customer/fulfillment/refund. `SOURCE_INTERPRETERS` in `services/core.py` registers
only `("shopify", "order")` and `("shopify", "refund")`. Order handling supports specified quantity
reductions/cancellations through `shop_order_changes.py`; unsupported changes remain reviewable.
`shop_refunds.py` interprets supported refunds; it does not prove full payment, warehouse or
accounting coverage. Vendor authentication, live retrieval and webhook transport are not supplied by
the shell. The existing order interpreter consumes the fixture’s `line_items` shape, not an
arbitrary GraphQL response.

## Coverage matrix

**Small entry scope for A: explain orders.** Capture orders/lines, relevant changes/cancellations
and the item, party and source identities needed for interpretation. Existing Reality master records
can supply context; a full master-data import is not automatically required. Add shipping, payments,
purchasing and returns only for the corresponding questions.

This matrix is **not a mandatory list for every observation deployment**. “Baseline” applies to this
entry scope; other rows are required only for their stated goal. Without execution evidence, you can
display an order but cannot claim a reliable open delivery quantity.

| Source area                             | Mode and necessity                    | What to capture                                                                             | Reality purpose                                                          | Work still required                                                                                       |
| --------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| Products/variants, customers, locations | A: Baseline context as needed         | Vendor object/variant IDs, units, identity links and responsible warehouse                  | Item, Party, Location references                                         | No registered product/customer/fulfillment interpreter; resolve source identities explicitly              |
| Orders and lines                        | A: Baseline                           | Order/line IDs, quantities, source-stated amounts/currency, dates and versions              | Document/DocumentLine and customer Commitments                           | Registered order example exists; real API shape, context and supported update policy must be verified     |
| Changes/cancellations                   | A: Baseline                           | Later source version, affected lines and causal identity                                    | Revisions/cancellation through shared services                           | Supported reductions/cancellations exist; other changes require review/extension                          |
| Fulfillment                             | A: Explain delivery progress          | Actual execution and line quantities; do not treat routing requests as completed shipment   | Shared fulfillment/Movement services                                     | Transport and interpreter missing; choose Shopify or warehouse authority to avoid duplicate outflow       |
| Inventory                               | A: Observe inventory                  | Location snapshot and authoritative subsequent changes                                      | Stated observation or opening/movement evidence under an agreed contract | Distinguish available-to-sell from physical stock; missing history cannot be invented                     |
| Refunds/returns                         | A: Check refunds/returns              | Refund ID, order/line links, successful transaction, return announcement and actual receipt | Existing refund/return services                                          | Refund interpreter exists; physical receipt needs its own warehouse evidence                              |
| Payments/payouts                        | A: Check cash/settlement              | Transactions, allocations, fees, payouts and disputes where in scope                        | Shared finance/payment services                                          | Separate Shopify Payments/other provider transport and interpreters; refund support alone is insufficient |
| Invoices/credit notes                   | A: Check invoicing; additional source | Actual legal financial documents with stated tax and totals                                 | Financial Evidence and supported finance services                        | Obtain from the responsible invoice/accounting source; do not treat an order total as an invoice          |
| Purchasing/production                   | A: Additional ERP scope only          | Supplier promises and manufacturing records where relevant                                  | Supplier/domain services                                                 | Usually another responsible system; explicitly include it in the coverage sheet                           |

## Step by step

### How and when to fetch data

Fetch only the source areas selected in your matrix scope; this table does not require every read
for every mode. Observation needs authorized read access only.

Use **Bulk for the baseline, Webhooks for changes, API reads for reconciliation**. These intervals
are **recommended starting values**, not Shopify guarantees or an implemented Reality connector.
Adjust them to volume, API limits and how long your business can tolerate stale data.

| Data                            | Initial capture                                                           | Change trigger / read                                                                                               | Suggested fallback                                          |
| ------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Products/variants and customers | GraphQL Bulk query where supported                                        | `products/create`, `products/update`, `products/delete`; `customers/create`, `customers/update`, `customers/delete` | Daily reconciliation                                        |
| Orders and changes              | Bulk orders with required related records; authorized history only        | `orders/create`, `orders/updated`, `orders/cancelled`; fetch missing detail                                         | Every 5–15 minutes                                          |
| Fulfillment and refunds         | Related order data or separate paginated reads                            | `fulfillments/create`, `fulfillments/update`, `refunds/create`                                                      | Every 5–15 minutes; return lifecycle separately if in scope |
| Inventory and locations         | Current levels per item/location; paginated reads or supported Bulk query | `inventory_levels/update`; reread affected level and location context                                               | Every 15–30 minutes for active locations                    |
| Payments and payouts            | Order transactions; separate paginated Shopify Payments reads             | `order_transactions/create`; query `shopifyPaymentsAccount` payouts and related balance transactions                | Hourly, plus daily financial reconciliation                 |

The named topics come from the
[Shopify webhook reference](https://shopify.dev/docs/api/webhooks/latest). They are signals to
interpret, not proof of physical receipt or successful cash settlement. An available-to-sell
inventory value is not automatically physical stock.

[Bulk queries](https://shopify.dev/docs/apps/build/apis/graphql-admin/bulk-operations/queries) are
asynchronous exports. `bulk_operations/finish` reports export completion, not a business change.
Test the exact query against the pinned API version; not every query supports Bulk. Use pagination
for unsupported reads. Payouts need separate
[Shopify Payments access](https://shopify.dev/docs/api/admin-graphql/latest/queries/shopifyPaymentsAccount);
other payment providers need their own source. This plan does not depend on a payout webhook.

Before the baseline, enable verified Webhook intake into durable storage. Record the capture
boundary, import the baseline, then replay buffered changes without applying stock twice. Treat this
as a reconciliation protocol, not an atomic cross-object snapshot. Advance a durable checkpoint only
after successful capture. Use supported change filters with overlapping windows, deduplicate by
source identity/version and reconcile scoped records daily (in batches for large shops). Preserve
raw event and fetched-object payloads separately. Record last successful capture, backlog and
missing permissions; retries use shared scheduled jobs with rate-limit backoff.

### Implementation sequence

Shared ingest stores the original payload as a `SourceRecord` and creates an `ImportJob`. Only the
registered interpreter maps its meaning into Evidence and Reality.

1. Decide which facts the shop owns and which come from ERP, warehouse or payment provider. Preserve
   identities across sources without duplicating orders, shipments or refunds.
2. Capture an original order and refund fixture, then products/variants and relevant
   location/customer context. Follow `fixtures/shopify/order_10473.json` and
   `tests/test_shop_refunds.py` for the current accepted shapes.
3. Implement authorized GraphQL capture and initial pagination/bulk retrieval. Preserve the actual
   original response as source evidence. If adaptation is required, keep it in the interpreter; do
   not replace the raw SourceRecord with a lossy REST-like reconstruction.
4. Supply opaque `company_party_id`, `customer_party_id` and `location_id` context. Resolve
   variants/source IDs; the existing order example’s SKU lookup is not proof that SKU is globally
   unique or a canonical identity. Unknown item lines remain explainable rather than silently
   assigned.
5. Use `enqueue_source`/`process_import_job` and the registered order/refund paths. Adapt/test the
   interpreter for your pinned source shape. Add missing required source interpreters through the
   normal spec workflow.
6. Verify webhook signatures, deduplicate deliveries, handle out-of-order updates and fetch needed
   authoritative object versions. Use a durable intake/retry path and periodic reconciliation
   through shared scheduled jobs, not browser timers.
7. Test supported reductions/cancellations, held changes, missing line quantity/price, successful
   versus pending refunds and unknown line references. A refund is not evidence that stock
   physically returned.
8. Connect the responsible warehouse/invoice/payment sources to complete the scope. Verify the
   combined acceptance story before enabling ongoing intake; outbound shop actions have a separate
   design and confirmation boundary.

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
the [shared acceptance checklist](./connector-contract#completeness-and-acceptance).

## References and next steps

Vendor references checked on 2026-10-03. Use the version applicable to your installation; these
links are not implementation claims.

- [Shopify bulk retrieval](https://shopify.dev/docs/apps/build/apis/graphql-admin/bulk-operations/queries)
- [Shopify webhook verification](https://shopify.dev/docs/apps/build/webhooks/verify-deliveries)
- [Shopify order/fulfillment concepts](https://shopify.dev/docs/apps/build/orders-fulfillment/order-management-apps)

Repository templates: `packages/reality-core/tests/test_source_ingestion.py`,
`test_shopify_and_explain.py`, `test_shop_order_changes.py`, `test_shop_refunds.py` and
`test_shop_line_gaps.py`. They prove their existing services, not a complete live Shopify connector.

[From source data to Reality](./connector-contract) · [First pilot](./parallel-test) ·
[Develop interpreters](../development/connectors)
