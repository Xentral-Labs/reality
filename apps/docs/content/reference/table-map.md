# Table map and common misconceptions

Two appendices of the [handbook](../concepts/business-reality-guide): which table is responsible for
what, and which assumptions from the ERP world do not hold here.

## Table map by responsibility

The exact current inventory is maintained in
[Data Model](https://github.com/Xentral-Labs/reality/blob/main/docs/DATA_MODEL.md).

| Responsibility        | Principal tables                                                                                                               |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Company access        | `tenant`, `tenant_membership`, `company_invitation`, `invitation_delivery`, `security_audit_event`                             |
| Master data           | `party`, `party_role`, `party_hold`, `item`, `location`, `payment_term`                                                        |
| Pricing               | `price_list`, `price_list_entry`, `party_price_list`, `party_group`, `party_group_member`, `party_group_price_list`            |
| Integration           | `source_system`, `source_capability`                                                                                           |
| Source intake         | `source_stream`, `source_record`, `source_artifact`, `import_job`, `interpretation_outcome`, `interpretation_record_reference` |
| Evidence              | `document`, `document_line`                                                                                                    |
| Promise and execution | `commitment`, `commitment_hold`, `reservation`, `movement`, `movement_correction`                                              |
| Warehouse identity    | `handling_unit`, `lot`, `serial_unit`                                                                                          |
| Finance               | `ledger_entry`, `ledger_reversal`, `settlement_allocation`                                                                     |
| Observation and audit | `fact`, `action`, `business_event`                                                                                             |
| Read optimization     | `projection_row`, `projection_checkpoint`                                                                                      |
| Conversation          | `chat_session`, `chat_message`                                                                                                 |

## Common misconceptions

**“The sales order is fulfilled, so the invoice must be paid.”** No. Delivery and payment are
independent Reality axes.

**“Reserved stock has left the warehouse.”** No. Only a Movement changes physical stock.

**“Incoming supply is available stock.”** No. It contributes to projected availability but cannot be
shipped before receipt.

**“A new source version edits the old order.”** No. It preserves a new SourceRecord. Shopify updates
currently require review and leave prior Evidence and Reality intact.

**“A correction deletes the mistake.”** No. It appends an inverse and optional replacement,
preserving the explanation.

**“A payment belongs directly to an invoice.”** The payment has its own Evidence and posting.
SettlementAllocation expresses how much applies to an invoice.

**“A projection is another source of truth.”** No. It is a rebuildable read model.

**“Every upstream field needs a column.”** No. SourceRecord preserves the payload. A field becomes
typed only when repeated core behavior proves the need.

## The Data Model: Tables and Responsibilities {#data-model}

### Tenant boundary and master data

Every business record belongs to a tenant and every query carries that boundary; an ID from another
tenant behaves as not found. Master data is deactivated, never deleted, so old Documents,
Commitments and Movements stay readable. Only fields that repeatedly drive calculations, filters,
joins or decisions are typed; the raw payload keeps the rest.

| Table          | Meaning in business language                                       |
| -------------- | ------------------------------------------------------------------ |
| `tenant`       | The company boundary inside the shared database.                   |
| `party`        | A company or person participating in business.                     |
| `party_role`   | Whether a Party acts as company, customer, supplier, or several.   |
| `party_hold`   | A current or historically released delivery hold for a Party.      |
| `item`         | A product or service; only stocked Items have physical Movements.  |
| `location`     | A warehouse, bin or virtual place.                                 |
| `payment_term` | A reusable payment condition with an opaque identity.              |
| Pricing tables | Price lists, tiers, Party assignments and Party-group assignments. |

### Source tables: preserving what arrived

| Table                             | Role                                                        |
| --------------------------------- | ----------------------------------------------------------- |
| `source_system`                   | A configured origin such as one Shopify shop.               |
| `source_capability`               | What kind of data that origin may provide.                  |
| `source_stream`                   | The stable head for `(system, type, external ID)`.          |
| `source_record`                   | One immutable, lossless payload version.                    |
| `source_artifact`                 | Immutable original file bytes and metadata.                 |
| `import_job`                      | Mutable work-queue state for interpreting one SourceRecord. |
| `interpretation_outcome`          | Immutable result of each terminal attempt.                  |
| `interpretation_record_reference` | Audit references to records produced or recognized.         |

A `SourceStream` says “all versions of Shopify order 4711 belong together”; each `SourceRecord` is
one exact payload at one time. An identical delivery is recognised by its hash and ignored, a
changed one becomes a new version, an unknown format is kept as `unmapped` rather than guessed. A
failed interpretation leaves no half-created business records, and every attempt stays visible.

### Evidence tables: Documents and lines

`document` is a minimal evidence header: type, number, Party, currency, agreed total, dates, payment
term and provenance. `document_line` records the agreed Item, quantity, unit and price. Every amount
is the one the source stated; Reality never multiplies quantity by price or adds lines up, and a
total that disagrees with its lines is kept as a finding about the source.

A Document status describes the statement's lifecycle, such as `recorded` or `superseded`. It never
means delivery, reservation, fulfilment or payment. “Is order `SO-1042` open?” is four questions: is
the external version current, is quantity still promised, is stock still reserved, is an invoice
amount unpaid. No single status field answers all four truthfully.

### Commitments: directional promises

| Type                | From     | To       | Fulfilled by                |
| ------------------- | -------- | -------- | --------------------------- |
| `customer_delivery` | Acme     | Customer | linked `shipment` Movements |
| `supplier_delivery` | Supplier | Acme     | linked `receipt` Movements  |

A Commitment names Item, Location, promised quantity, due time and priority. It may be backed by a
DocumentLine, by a Document only, or by neither, so a real promise can exist before a formal
document.

```text
fulfilled quantity = linked qualifying Movements
                     - qualifying original Movements that were corrected

open quantity = max(0, promised quantity - fulfilled quantity)
```

The stored state is `open`, `fulfilled` or `cancelled`; “partially fulfilled” is derived.

### Reservations: allocation without movement

A Reservation allocates stock at one Location to one outgoing customer Commitment; its only
provenance link is `commitment_id`.

```text
active --shipment--> consumed
active --release---> released
```

Both terminal states stay visible. A partial shipment consumes the original and creates a new active
Reservation for the remainder. Incoming supplier Commitments are not reservations: future goods
raise projected availability, but they are not stock.

### Movements: the physical journal

Stock is the net result of the Movement journal, not an editable balance.

| Movement type   | From             | To               | Meaning                                               |
| --------------- | ---------------- | ---------------- | ----------------------------------------------------- |
| `opening_stock` | none             | required         | Establish initial physical quantity.                  |
| `receipt`       | none             | required         | Receive goods, optionally against a supplier promise. |
| `shipment`      | required         | none             | Ship goods, optionally against a customer promise.    |
| `transfer`      | required         | required         | Move goods internally.                                |
| `return`        | none             | required         | Bring returned goods back into stock.                 |
| `adjustment`    | exactly one side | exactly one side | Record a counted difference with a reason.            |

Quantity is positive, locations express direction, and outbound Movements cannot exceed stock.
Movements may carry handling-unit, lot and serial identity.

### Financial Reality

`ledger_entry` is an append-only subledger entry; entries form balanced posting groups in one
currency. A payment has its own Document and LedgerEntries, and `settlement_allocation` connects the
payment's control entry to the invoice's. One payment can settle several invoices and one invoice
can take several payments. “Open”, “partially paid” and “paid” are derived, never stored.

### Facts, events, proposals and projections

| Table                       | Purpose                                                            | What it is not                          |
| --------------------------- | ------------------------------------------------------------------ | --------------------------------------- |
| `fact`                      | Immutable source-supported observation using a reviewed predicate. | Current stock or a copied master field. |
| `business_event`            | Notification that a domain change committed.                       | The authoritative business record.      |
| `action` (`ChangeProposal`) | Audit of a prepared change, approval and execution.                | An alternative direct write path.       |
| `projection_row`            | Rebuildable materialized read data.                                | Business truth.                         |
| `projection_checkpoint`     | Latest incorporated tenant event sequence.                         | Proof of the underlying action.         |

A Projection is like an ERP worklist or index: if it is stale or lost it is rebuilt from the records
and BusinessEvents, and commands never trust it to permit over-allocation or excess shipment. Facts,
the one record kind not walked through here, have their own chapter:
[Facts and Open Questions](../concepts/business-reality-guide/06-facts-and-open-questions).
