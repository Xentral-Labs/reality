# Try Reality Alongside Shopify, Xentral or Odoo

You do not need to replace your ERP to learn whether Reality helps. Run it as a **parallel,
read-only observer of the upstream system**: copy selected records into an isolated Reality tenant,
let Reality build its own Evidence and operational view, and compare the result with people who know
the business case.

The first pilot proves understanding, not automation. Reality writes its own Source, Evidence and
Reality records, but it does not write back to Shopify, Xentral or Odoo. Do not enable outbound
actions during this phase.

## What is ready today?

| Source  | Present in the repository                                                                                             | Still needed for a live connection                                    |
| ------- | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Shopify | Connector shell and a working `("shopify", "order")` interpreter                                                      | Authentication, polling/webhooks and production mapping for your shop |
| Xentral | Connector shell with `order`, `purchase_order`, `article`, `contact` and `payment` capabilities                       | Vendor transport and an interpreter for each source type you test     |
| Odoo    | Connector shell with `sale.order`, `purchase.order`, `product.product`, `res.partner` and `account.move` capabilities | Vendor transport and an interpreter for each source type you test     |

A connector shell describes possible source types. It is not a finished connector and contains no
credentials, vendor API calls or field mapping. The executable source of truth is
`packages/reality-core/config/connector_catalog.yaml`; registered object interpreters are in
`SOURCE_INTERPRETERS` in `services/core.py`.

## The four-phase pilot

### 1. Capture — choose one narrow business story

Create a separate Reality tenant or company for the test. Select 10–50 records that include normal
and difficult cases, for example an open order, a partial delivery, a cancellation and an unknown
SKU. Record the upstream object type, opaque upstream ID and version timestamp or revision.

Start with one story:

- Shopify: orders and later fulfilment events;
- Xentral: orders and articles;
- Odoo: `sale.order` and `product.product`.

Fetch through a small adapter or export JSON/CSV. Submit the original object unchanged through the
tenant-scoped ingest boundary. `source_record_ingest_propose` shows the proposed mutation and needs
human confirmation; the HTTP API exposes the same application capability. Never paste credentials
into a payload or log.

These are representative learning envelopes, not vendor API contracts:

```json
{
  "source_system": "shopify",
  "source_type": "order",
  "external_id": "gid://shopify/Order/4711",
  "payload": {
    "id": 4711,
    "name": "#1042",
    "line_items": [{ "sku": "CHAIR-BLACK", "quantity": 4 }]
  }
}
```

```json
{
  "source_system": "xentral",
  "source_type": "order",
  "external_id": "order-4711",
  "payload": {
    "number": "SO-4711",
    "status": "released",
    "positions": [{ "article": "CHAIR-BLACK", "quantity": "4" }]
  }
}
```

```json
{
  "source_system": "odoo",
  "source_type": "sale.order",
  "external_id": "sale.order:4711",
  "payload": {
    "name": "S04711",
    "state": "sale",
    "order_line": [{ "product_code": "CHAIR-BLACK", "product_uom_qty": 4 }]
  }
}
```

Use the field names and complete payload actually returned by your system. Do not reshape it into
the example before storage.

### 2. Interpret — teach only proven meaning

For Shopify orders, start with the existing interpreter and its required tenant context. For Xentral
or Odoo, the first accepted records will remain `unmapped` until you implement and register the
exact `(source_system, source_type)` interpreter. This is safe: the immutable payload is retained
without pretending its business meaning is known.

Map only what the chosen story needs. A sales-order interpretation will commonly resolve party, item
and location, create Document/DocumentLine Evidence, and derive an outgoing Commitment. Follow
[the complete order example](./order-example) and
[Connect an ERP System](../development/connectors).

### 3. Compare — reconcile meaning, not row counts

Use `interpretation_coverage` to see whether each source was interpreted, needs review, failed or is
unmapped, and which Reality records it produced. Then compare these questions with the ERP owner:

| Question                                | Inspect in Reality                    |
| --------------------------------------- | ------------------------------------- |
| What did the ERP actually send?         | immutable SourceRecord payload        |
| What document and lines were evidenced? | Document and DocumentLine             |
| What is still promised?                 | open Commitment quantity              |
| What is allocated or physically moved?  | Reservation and Movement              |
| Why is an order at risk?                | Projection, Exception and their trace |

An empty queue does not prove that there is no work: first check interpretation coverage. Record
every disagreement as one of four causes—missing source data, wrong mapping, missing core rule or a
wrong expectation—and correct the appropriate layer.

### 4. Act — enable automation only after acceptance

Keep Reality observational until the sample is explainable and repeatable. Before enabling any
action, agree on:

- the action's business owner and allowed scope;
- preview and explicit confirmation for every mutation;
- idempotency and the upstream write-back identity;
- how the effect is verified in Reality and in the ERP;
- how the integration is disabled without losing evidence.

Begin with read-only questions and projections. Add one proposed action only after the Agent
Operator accepts the comparison results. A pilot is successful even when it reveals that a required
interpreter or business rule is still missing.

## Done for the first pilot

- [ ] One isolated tenant and one narrow business story are defined.
- [ ] Original payloads for normal and edge cases are stored losslessly.
- [ ] Retries do not create duplicate source versions or business effects.
- [ ] Every record has an explicit interpreted, review, failed or unmapped outcome.
- [ ] Produced records trace back through Evidence to their SourceRecord.
- [ ] Differences from the ERP are classified and reviewed with a business owner.
- [ ] No outbound ERP mutation is enabled.

Next, read the [Connector contract](./connector-contract) before turning the pilot adapter into a
production integration.
