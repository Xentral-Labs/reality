# From source data to Reality

Capture original records unchanged, organize their meaning as Evidence, and link them to Reality.
This is the shared concept behind every data integration. It gives your agent facts it can explain
and use through shared application tools; merely copying an external JSON object is not enough.

## The idea: Source → Evidence → Reality

Each layer answers a different question:

| Layer    | Question                                                 | Example                                                                                                     |
| -------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Source   | What did the external system actually send?              | Immutable `SourceRecord` containing the original ERP order payload and its source/version identity          |
| Evidence | What does this record state?                             | `Document` and `DocumentLine` retain the order and its stated line quantity                                 |
| Reality  | What business obligation or execution does it establish? | A `Commitment` promises the customer 10 units; later evidenced shipment supports `Movement` and fulfillment |

Evidence is not just a file attachment. It organizes source statements so obligations and execution
can refer to the right record and line. Reality uses the shortest true relationship; do not copy
source, document and line references onto every related record when an existing link already
provides the trace.

## One order, then an actual shipment

The ERP sends a new order: Mira is promised 10 Blue Chairs. Item/customer identities and units are
resolved. The connector preserves the full original payload; the registered interpreter uses shared
services to establish Evidence and the customer promise. Later, the responsible warehouse supplies
actual shipment of 4 units with its own identity and order-line reference.

```text
Original order SourceRecord → Document / DocumentLine → Commitment: promised 10
Original execution source   → execution Evidence     → Movement: delivered 4
                                                        linked to the promise
Read-time observation: 6 still to deliver
```

The remaining 6 are derived at read time from the held promise and proven execution. They are not
stored as a new authoritative source statement or copied as delivery status onto the order Document.
This example assumes complete relevant revisions/execution from the agreed start; without that
coverage the remainder is unknown. A delivery note or label alone does not prove physical shipment.

**Your agent** can explain “Mira still needs 6 chairs” and follow the links back to the original
records. For stock, payment or automatic release it needs the additional sources and reviewed rules
for that question. More captured data does not automatically authorize an upstream action.

## Original payload, local records and later changes

A Shopify order, ERP record or original tool result can be a source when captured under an agreed
source contract. Not every Agent Tool call creates source data: querying existing Reality reads its
local records.

1. **Capture the original:** the connector supplies the received payload unchanged with source
   system, object type, external ID and version context. Reality stores it as a `SourceRecord`.
   “Complete” means the received object payload, not the ERP's entire database.
2. **Interpret meaning:** the appropriate interpreter uses shared services to create Evidence and
   linked Reality records. Reality then holds its own business records and explainable change
   history; it is more than a live display of the external system.
3. **Capture a later representation:** when the external object changes, the connector supplies its
   new representation under the same source identity. Previously unseen content creates another
   immutable source version; the earlier version remains. An identical payload is recognized as a
   repeat and does not create an additional SourceRecord version.
4. **Interpret the change:** the interpreter's reviewed contract determines what the new
   representation means. Supported changes use shared services; unsupported or contradictory cases
   remain visible for review. A new source version alone does not prove successful Reality updates.

Representations of one external object belong to a `SourceStream`, identified by tenant,
`source_system`, `source_type` and `external_id`. Reality detects identical content with a canonical
payload hash within that stream. An already-known earlier representation is also a repeat. The
version number follows capture order, not automatically the business order of upstream changes.

With reliable `source_version_at` context, Reality can classify late representations as stale and
different content with the same source timestamp as conflicting. Without that context it cannot
infer original chronological order from content; the integration needs a reviewed version contract.

```text
External order, same object ID
  → SourceRecord v1: promised 10 → Evidence → Commitment
  → SourceRecord v2: promised  8 → reviewed interpretation of the same obligation
  → identical payload again    → known source version; no second order
```

With actual shipment of 4 already evidenced, a supported reduction from 10 promised to 8 leaves 4
open, under complete execution coverage and the reviewed update contract. The existing Shopify order
interpreter supports specific reductions and cancellations; other changes require review. It also
compares the requested change with current Reality so replay or a later source version does not
simply undo actual execution or human revisions. This is **not a generic automatic field diff** that
understands arbitrary upstream records without a business interpreter.

Some sources deliver events or change notifications rather than a complete object. Preserve those
original payloads too; capture authoritative detail reads according to the source contract when
needed. Missing fields do not license inventing a new truth.

Provenance here refers to **Source**, not **Surface**. A Surface is an entrypoint or interface. A
source trace may follow Commitment → DocumentLine → Document → SourceRecord; every record does not
need another direct source link. Other sources, such as actual shipment, add their own identities
and evidenced relationship to the promise.

## Who does what?

- **Connector:** authenticates, reads authorized original records and captures them losslessly at
  Reality's application boundary. It supplies tenant, source identity and version context.
- **Interpreter:** knows the meaning of that source type, resolves identities and calls shared
  services to establish Evidence and Reality. Unsupported meaning remains visibly `unmapped` or
  requires review.
- **Services, Views and Projections:** calculate current observations from held records. Agent Tools
  provide access to these same application capabilities, without an alternative set of rules.

Start with [the example ERP stages](./example-erp) to choose the facts your agent needs. Use
[the technical order-import example](./order-example) for implementation orientation. The rules
below explain how to keep any integration lossless, repeatable and traceable.

## Responsibilities

A connector authenticates to its upstream source, selects authorized records, captures them
losslessly, and submits them with tenant and source identity through Reality's application boundary.
It does not write domain tables, infer operational status in transport code, or bypass confirmation.

## Lossless payloads

Store the original record and relevant envelope metadata. Do not drop unknown fields. Binary source
files belong in private object storage and are referenced by opaque keys; business identity and
metadata remain in PostgreSQL.

## Idempotency and versioning

Repeated delivery of the same upstream version must not manufacture duplicate business events. A
changed upstream record creates a new SourceRecord version or event so history remains explainable.
Human document numbers are not idempotency keys unless an explicit source contract proves their
scope and version behavior.

## Typing criteria

Promote a source field into the typed model only when core logic repeatedly:

- calculates with it;
- filters or joins on it;
- constrains or validates it;
- predicts from it; or
- acts on it.

## Error model

Classify connection/authentication errors, invalid envelopes, unsupported interpretation, and
downstream service failures separately. Preserve accepted source input, expose a safe operator
message, log diagnostic context without secrets, and make retry behavior explicit.

## Traceability outcome

Where applicable, a reader can traverse SourceRecord → Document/DocumentLine → Fact, Commitment,
Reservation, Movement, or LedgerEntry. When a stage does not apply, the connector does not invent
it.

> **Normative invariant:** Connectors call shared services/tools. They never perform direct ORM
> writes or implement a second set of business rules.

## Completeness and acceptance

“100 %” means **complete for a written company, process and time scope**. It does not mean every API
field or the source’s entire history. Coverage from a cutover date is not a reconstruction of
earlier history. Explicitly name excluded modules and unavailable data.

The end-to-end guides cover scope, source areas and implementation gaps: [Xentral](./xentral),
[Shopify](./shopify), [Odoo](./odoo).

### Shared coverage matrix

This matrix lists possible areas, not mandatory coverage for every observation deployment. Select
only rows relevant to your mode and question. Acceptance also verifies only that agreed scope.

For every row, record **responsible source, original object/line identity, source type/interpreter,
scope, status and acceptance evidence**. Use planned, captured only, interpreted, verified, or
outside agreed scope with a reason. A shell entry only advertises a capability; a SourceRecord only
proves capture. Neither means verified business coverage.

| Area                    | Required source/Evidence                                                                | Business purpose                                                           | Acceptance proof                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Identity/master data    | Companies, party roles, items/variants, units, locations and source IDs                 | Unambiguous tenant-scoped references                                       | No ambiguity; retain source IDs; reject foreign identities                         |
| Sales                   | Order headers/lines, quantities/dates, changes/cancellation                             | Document/DocumentLine and Commitment                                       | Promise matches source; versions and replay are explainable                        |
| Purchasing              | Purchase lines, supplier promises, receipts                                             | Supplier Commitment and receipt                                            | Partial receipt, remainder and cancellation agree                                  |
| Inventory               | Evidenced opening stock and subsequent receipts/issues/transfers/corrections            | Stock Evidence and Movement                                                | Reconcile item/location/unit; no duplicate opening quantities                      |
| Reservation/fulfillment | Existing allocation and actual shipment lines                                           | Reservation, executed Movement and shortest promise link                   | Reserved is distinct from shipped; no duplicate allocation/execution               |
| Invoices/credits        | Stated amounts, tax, currency, terms and document/line references                       | Financial Evidence and shared finance services                             | Preserve values; do not invent invoices from order totals                          |
| Payment/settlement      | Successful transaction, invoice allocation, fees/payouts where applicable               | Payment/settlement services; LedgerEntry under a valid accounting contract | Explain open items and cash; prevent duplicate imports                             |
| Return/refund           | Announcement, physical receipt, credit and cash refund                                  | Separate stock/finance operations                                          | Do not invent stock from refund; prevent duplicate financial events across sources |
| Additional modules      | Manufacturing/BOM, lots/serials, conditions, services/subscriptions/analytics when used | Existing capability or separately specified extension                      | Verify every business dependency or explicitly exclude it                          |
| Operations              | Initial load, changes, deletion/archiving, retry, lag and reconciliation                | Durable explainable intake                                                 | Prove recovery, tenant isolation, error/review ownership and freshness target      |

### Agree source authority and cutover

A shop and ERP can report the same order. Retain both original sources but select an authority per
fact and phase with an evidenced linking contract. Shop order, ERP shipment and payment provider may
own different areas. Later handoff needs a contract; equal amounts, SKUs or document numbers do not
prove identity. Unresolved duplicates remain reviewable.

An inventory snapshot states a condition rather than proving historical movements. Decide whether it
is interpreted as an observation or an evidenced opening through an existing service. Opening at
time T is followed only by agreed subsequent movements; do not add earlier history again. Apply the
same cutover principle to open financial balances. Reserved/available quantities are not
automatically physical stock.

Changes and deletion need an explicit contract: a missing API row alone does not prove cancellation,
shipment or correction. Preserve prior SourceRecords, version sequence and review outcome. Do not
recalculate monetary values the source states.

### Completion checklist

- [ ] Agree companies/tenants, sources, modules, operating mode, cutover and exclusions in writing.
- [ ] Every in-scope area has a responsible source, identity/version contract, interpreter and
      verification evidence; captured only is not business coverage.
- [ ] Resolve identities and relationships; retain original payloads and unknown fields.
- [ ] Pass the relevant acceptance steps using real source fixtures, including partial quantities,
      cancellation, return and financial allocation where in scope.
- [ ] Reconcile initial and incremental intake at record level and by quantities/amounts; explain
      differences. Equal totals alone are insufficient.
- [ ] Verify replay, reversed version order, partial failure, missing records, ambiguity and foreign
      tenant identities.
- [ ] Verify renewed access, API limits, durable checkpoints, recovery, freshness and recurring
      reconciliation. Recurring intake follows `docs/features/scheduled-jobs.md`.
- [ ] Keep unsupported cases visible with a responsible operational role; do not report them as
      successfully interpreted.

### Outbound writes are a separate scope

A complete read integration can be finished without upstream writes. Define each outbound operation
with allowed effect, authorization, server preview/confirmation, idempotency, error handling and
subsequent verification read. Mutating Agent Tools need explicit approval. External effects or new
scheduling infrastructure require separately reviewed design under the scheduling contract. Capture
authorization does not authorize arbitrary write-back.
