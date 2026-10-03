---
aside: false
---

# How to read the lists {#how-to-read-the-lists}

[Back to the tool overview](/tool-usage/)

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
