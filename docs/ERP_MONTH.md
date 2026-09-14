# Business Reality: A Practical Guide for ERP Practitioners

This guide explains Business Reality as a coherent operating model. It is written for
readers who know conventional ERP systems and want to understand why this system does
not put the order document at the center of every process.

The examples follow one representative month at **Acme Bikes GmbH** in September 2026.
They deliberately revisit the same orders, goods and payments. The purpose is not to
show as many screens as possible, but to make the relationships between source data,
business evidence and operational reality intuitive.

This is an explanatory guide, not a second normative specification. The authoritative
contracts remain [Architecture](ARCHITECTURE.md), [Data Model](DATA_MODEL.md), the
documents under [features](features/), and the applicable specifications under
`specs/`.

## Part I — A different center of gravity

### 1. The familiar ERP picture

A conventional ERP often presents a sales order as the center of the commercial
world. The order header carries a status such as “partially delivered”; its lines may
carry an open quantity; an invoice may be considered “paid”; and a stock table stores
the latest balance. These fields are convenient, but they mix several kinds of truth:

- what an external system said;
- what a commercial document records;
- what the company promised;
- what warehouse staff physically did;
- what accounting posted;
- and what the application currently concludes from all of the above.

This becomes fragile as soon as reality is untidy. A customer changes an order after
five units were shipped. A supplier delivers in two parts. A payment covers three
invoices. A warehouse receipt was entered with the wrong quantity. If every document
owns its own operational status, several copies of “the truth” must be synchronized.

Business Reality chooses a different center of gravity. It records small, precise
business objects and derives the current answer from them.

### 2. Source, Evidence and Reality

The foundational chain is:

```text
SourceRecord -> Document -> DocumentLine -> Commitment
                                             |       |
                                             v       v
                                      Reservation  Movement

Document or SourceRecord -> LedgerEntry
Payment LedgerEntry + Invoice LedgerEntry -> SettlementAllocation
```

| Layer | Main question | Typical records |
| --- | --- | --- |
| Source | What exactly arrived from outside? | `SourceStream`, `SourceRecord`, `SourceArtifact`, `ImportJob` |
| Evidence | What business statement did we record? | `Document`, `DocumentLine` |
| Reality | What was promised, allocated, moved, observed or posted? | `Commitment`, `Reservation`, `Movement`, `LedgerEntry`, `Fact` |
| Derived view | What does all recorded reality mean now? | stock, availability, open quantity, risk, open receivable, projections |

A Shopify JSON object is Source. The interpreted sales order and its lines are
Evidence. The promise to deliver ten lamps is a Commitment. Setting aside six lamps is
a Reservation. Taking four lamps out of the warehouse is a Movement. Posting an
invoice creates LedgerEntries. “Six still open” is a calculation.

Three sentences make the model memorable:

1. A **Document** says, “this commercial statement was recorded.”
2. A **Commitment** says, “this party is expected to provide this quantity to that
   party.”
3. A **Movement** says, “this quantity physically changed location.”

A Reservation is neither a promise nor a physical event. It says, “this part of
current physical stock is allocated to that outgoing promise.” An invoice is not proof
of delivery. A delivery is not proof of payment. A reservation does not reduce
physical stock.

### 3. Identity and traceability

Every important record has an opaque ID. Human values such as order number
`SO-2026-1042`, SKU `BIKE-LIGHT`, or payment reference `PAY-88` are useful for people
and search, but never serve as relationships. Numbers can be reused, corrected or
collide across systems.

Links follow the shortest true relationship. A Reservation points to its Commitment,
not redundantly to a Document, DocumentLine and SourceRecord. Those can be reached by
walking back through the Commitment. A settlement points from the payment's control
account entry to the invoice's control account entry; it does not copy their evidence
references.

### 4. Immutability and correction

Historical truth is appended, not silently rewritten.

- A changed external payload becomes a new SourceRecord version.
- A physical error receives an inverse Movement and, when necessary, a replacement.
- A financial error receives a complete inverse posting group.
- A released or consumed Reservation remains visible.
- A cancelled or superseded Commitment remains visible.

This makes it possible to reconstruct what the system knew, what it did and why
today's answer differs from yesterday's.

## Part II — The vocabulary and tables

### 5. Tenant boundary and master data

Every business record belongs to a tenant. Every repository query includes that
boundary. An opaque ID from another tenant behaves as not found and cannot be linked
into the current company's graph.

| Table | Meaning in business language |
| --- | --- |
| `tenant` | The company boundary inside the shared database. |
| `party` | A company or person participating in business. |
| `party_role` | Whether a Party acts as company, customer, supplier, or several. |
| `party_hold` | A current or historically released delivery hold for a Party. |
| `item` | A product or service; only stocked Items have physical Movements. |
| `location` | A warehouse, bin or virtual place. |
| `payment_term` | A reusable payment condition with an opaque identity. |
| Pricing tables | Price lists, tiers, Party assignments and Party-group assignments. |

Master data is deactivated rather than deleted. Historical Documents, Commitments and
Movements must remain understandable after an Item or Party leaves active use.

Only fields that repeatedly drive calculations, filtering, joining, constraints or
decisions are typed. An upstream system may supply hundreds of attributes; the raw
payload preserves them without turning all of them into schema.

### 6. Source tables: preserving what arrived

| Table | Role |
| --- | --- |
| `source_system` | A configured origin such as one Shopify shop. |
| `source_capability` | What kind of data that origin may provide. |
| `source_stream` | The stable head for `(system, type, external ID)`. |
| `source_record` | One immutable, lossless payload version. |
| `source_artifact` | Immutable original file bytes and metadata. |
| `import_job` | Mutable work-queue state for interpreting one SourceRecord. |
| `interpretation_outcome` | Immutable result of each terminal attempt. |
| `interpretation_record_reference` | Audit references to records produced or recognized. |

`SourceStream` says “all versions of Shopify order 4711 belong together.” Each
SourceRecord says “this was the exact payload received at this time.” Only the stream's
current pointer moves.

An identical delivery is idempotent because canonical payload hashing recognizes it.
A changed payload creates a version. Unknown formats are retained as `unmapped`, never
guessed or discarded. Interpretation can be retried when an explicit interpreter
exists. `ImportJob.status` is queue state; InterpretationOutcome is audit history. A
failed interpretation transaction leaves no half-created business records.

### 7. Evidence tables: Documents and lines

`document` is a minimal evidence header. It records type, number, Party, currency,
agreed total, dates, payment term and source provenance. `document_line` records the
agreed Item, quantity, unit and price details.

A Document status may describe the source statement's lifecycle, such as `recorded` or
`superseded`. It must never represent delivery, reservation, purchase fulfilment or
payment state.

Asking whether order `SO-1042` is open may mean four different things:

- Is the external order version still current?
- Is there a quantity Acme still promised to ship?
- Is stock still reserved for it?
- Is an invoice amount still unpaid?

There is no truthful single order-status field that answers all four.

### 8. Commitments: directional promises

| Type | From | To | Fulfilled by |
| --- | --- | --- | --- |
| `customer_delivery` | Acme | Customer | linked `shipment` Movements |
| `supplier_delivery` | Supplier | Acme | linked `receipt` Movements |

A Commitment normally names an Item, Location, promised quantity, due time and
priority. It may be backed by a DocumentLine, by a Document only, or by neither. A real
operational promise can therefore exist before a formal document.

```text
fulfilled quantity = linked qualifying Movements
                     - qualifying original Movements that were corrected

open quantity = max(0, promised quantity - fulfilled quantity)
```

The stored state is `open`, `fulfilled` or `cancelled`. “Partially fulfilled” is a
derived condition: fulfilled is greater than zero and open is also greater than zero.

### 9. Reservations: allocation without movement

A Reservation allocates stock at one Location to one outgoing customer Commitment. Its
shortest provenance link is `commitment_id`.

```text
active --shipment--> consumed
active --release---> released
```

Both terminal states remain visible. If a shipment consumes only part of one
Reservation, the original becomes consumed and the unused remainder becomes a new
active Reservation. This preserves the transition and the remaining allocation.

Incoming supplier Commitments are not reservations. Future goods contribute to
projected availability, but they are not yet physical stock.

### 10. Movements: the physical journal

Stock is the net result of the Movement journal, not an editable balance.

| Movement type | From | To | Meaning |
| --- | --- | --- | --- |
| `opening_stock` | none | required | Establish initial physical quantity. |
| `receipt` | none | required | Receive goods, optionally against a supplier promise. |
| `shipment` | required | none | Ship goods, optionally against a customer promise. |
| `transfer` | required | required | Move goods internally. |
| `return` | none | required | Bring returned goods back into stock. |
| `adjustment` | exactly one side | exactly one side | Record a counted difference with a reason. |

Quantity is positive; locations express direction. A transfer changes two location
balances but not company-wide stock. Movements may carry handling-unit, lot and serial
identity. A serial Movement has quantity one. Outbound Movements cannot exceed stock.

### 11. Financial Reality

`ledger_entry` is an append-only operational subledger entry. Entries form balanced
posting groups in one currency. A payment has its own Document and LedgerEntries; it
does not reuse invoice Evidence. `settlement_allocation` connects the payment's control
entry to the invoice's control entry.

This supports one payment for several invoices and several payments for one invoice.
Open amount is derived from invoice posting, credits and active allocations. “Open”,
“partially paid” and “paid” are views, not stored invoice states.

### 12. Facts, events, proposals and projections

| Table | Purpose | What it is not |
| --- | --- | --- |
| `fact` | Immutable source-supported observation using a reviewed predicate. | Current stock or a copied master field. |
| `business_event` | Notification that a domain change committed. | The authoritative business record. |
| `action` (`ChangeProposal`) | Audit of a prepared change, approval and execution. | An alternative direct write path. |
| `projection_row` | Rebuildable materialized read data. | Business truth. |
| `projection_checkpoint` | Latest incorporated tenant event sequence. | Proof of the underlying action. |

A Projection is similar to an ERP view, worklist or operational index. If it is stale
or lost, it is rebuilt from authoritative records and BusinessEvents. Commands still
validate against Commitments, Reservations, Movements and LedgerEntries.

## Part III — One business month, step by step

### 13. Day 1: opening stock

Acme begins with 20 `BIKE-LIGHT` units in Augsburg:

```text
Movement opening_stock: none -> Augsburg, quantity 20

physical = inbound 20 - outbound 0 = 20
reserved = 0
available = 20
```

An inventory snapshot never overwrites this balance. Its interpreter calculates a
delta and appends an adjustment Movement.

### 14. Day 2: entering a sales order

Müller GmbH orders 12 lights at EUR 49. The manual-order operation records atomically:

```text
SourceRecord (manual sales order payload)
  -> Document SO-1001
       -> DocumentLine 1: 12 x BIKE-LIGHT at EUR 49
            -> customer_delivery Commitment: Acme -> Müller, quantity 12
```

Creating an arbitrary Document alone creates Evidence only. The dedicated order
operation explicitly creates Commitments; the system does not guess warehouse intent
from a document type label.

```text
Commitment quantity = 12
fulfilled = 0
open = 12
physical = 20
reserved = 0
available = 20
```

The order exists, but no stock moved and no invoice became payable merely because it
was entered.

### 15. Reserving the order

The service compares the request with the Commitment's unfulfilled, not-yet-reserved
quantity and physical availability at its Location and tracked identity. All 12 are
available, so one active Reservation is created.

```text
physical = 20
active reserved = 12
available = 8
Commitment open = 12
```

The Commitment remains open because nothing shipped. If only eight were available,
the result would be `requested = 12`, `reserved = 8`, `shortage = 4`. The system does
not create negative allocation to make demand appear covered.

### 16. Shipping in parts

Acme ships five against the Commitment:

```text
Movement shipment: Augsburg -> none, quantity 5, commitment = COM-...
```

Physical stock falls to 15, fulfilled rises to five, open falls to seven, and five
units of allocation are consumed. Seven remain actively reserved.

```text
physical = 15
active reserved = 7
available = 8
fulfilled = 5
open Commitment quantity = 7
```

Shipping the remaining seven creates another Movement. Fulfilled becomes 12, open
becomes zero, the Commitment becomes `fulfilled`, and the last Reservation is
consumed. No delivery status is written to `SO-1001`.

### 17. A shortage and incoming supply

Huber Handel orders 30 lights when only eight are available. Its Commitment is 30; a
reservation allocates eight and reports 22 short.

| Question | Answer |
| --- | --- |
| What was ordered? | DocumentLine quantity 30. |
| What was promised? | Commitment quantity 30. |
| What shipped? | Linked shipment quantity 0. |
| What remains promised? | Open quantity 30. |
| What is allocated? | Active Reservation quantity 8. |
| What is short? | 22. |

Acme orders 22 from LightWorks AG:

```text
SourceRecord -> Purchase Document PO-2001 -> DocumentLine
             -> supplier_delivery Commitment: LightWorks -> Acme, quantity 22
```

```text
incoming open = 22
physical = 8
active reserved = 8
available = 0
projected availability = 22
```

Projected availability is planning information, not permission to ship. A supplier
promise does not put goods on the shelf.

### 18. Day 7: partial goods receipt

LightWorks delivers ten:

```text
Movement receipt: none -> Augsburg, quantity 10, supplier commitment = COM-...

supplier fulfilled = 10
supplier open = 12
physical = 18
active reserved = 8
available = 10
```

The receipt does not automatically choose a customer. Allocation is explicit. Acme may
reserve the ten for Huber. The final twelve arrive later in a second Receipt Movement,
fulfilling the supplier Commitment and allowing the remainder to be reserved.

The model also permits a supplier Commitment without a Document when a real promise
precedes formal Evidence, or a receipt without a Commitment when goods genuinely
arrive unexpectedly. The Inspector reports the absent evidence or promise honestly.

### 19. Partial and final customer shipment

Acme ships 18 to Huber, then 12. Each is a separate Movement against the same outgoing
Commitment.

```text
after first:  promised 30, fulfilled 18, open 12, state open
after second: promised 30, fulfilled 30, open 0, state fulfilled
```

Both physical dates remain visible instead of being collapsed into one delivery flag.

### 20. Cancellation, return and adjustment

Velo Store orders ten helmets and six are reserved. The customer cancels before
shipment. Cancelling the Commitment records its cancellation time and releases active
Reservations. It creates no Movement because nothing moved. Physical stock is
unchanged; available stock rises by six.

Müller later returns two shipped lights. A `return` Movement into the Returns Area
increases stock there. It does not erase the historical shipment or reopen the
fulfilled delivery promise. A commercial credit is a separate financial event.

A count then finds one missing light. An outbound `adjustment` from Augsburg with a
reason records the difference. It does not edit a stock balance.

### 21. Correcting a wrong warehouse entry

Suppose the receipt of ten should have been seven. The original is not edited. One
correction operation appends:

1. an exact inverse `correction` Movement with quantity ten;
2. a normal replacement Receipt Movement with quantity seven;
3. a MovementCorrection relation joining all three;
4. affected Commitment reconciliation;
5. a `movement.corrected` BusinessEvent.

Net stock and fulfilment become seven. The Inspector still shows what was first
recorded and why it changed. A compensation cannot itself be corrected; a wrong
replacement starts a new correction chain.

### 22. Invoice, partial payment and credit

Acme posts a EUR 1,470 sales invoice:

| Account | Side | Amount |
| --- | --- | ---: |
| Accounts receivable | Debit | EUR 1,470 |
| Sales revenue | Credit | EUR 1,470 |

This creates an open receivable but changes no delivery quantity.

A EUR 500 customer payment creates its own payment Document and balanced posting:

| Account | Side | Amount |
| --- | --- | ---: |
| Cash | Debit | EUR 500 |
| Accounts receivable | Credit | EUR 500 |

A SettlementAllocation connects the payment receivable entry to the invoice
receivable entry. The derived open amount becomes EUR 970. A payment can also be
recorded before allocation; it is then posted but not yet assigned to an invoice.

A EUR 100 sales credit debits revenue and credits receivables, reducing open amount to
EUR 870. It changes neither stock nor delivery fulfilment. A returned, credited item
therefore needs both a Return Movement and financial credit.

Ledger errors are reversed with a complete exact-inverse posting group. Existing
allocations remain historical but become inactive when a linked original posting is
reversed. The invoice reopens accordingly. A replacement payment is a new posting and
allocation.

## Part IV — Changes and lifecycle questions

### 23. When an external customer changes an order

Shopify order 4711 originally contains ten lights and later seven. Version 2 does not
overwrite version 1. It creates a new SourceRecord in the same SourceStream.

The current Shopify interpreter retains that update as `needs_review`; it does not
create replacement Evidence or Commitments. Previous Documents, Commitments,
Reservations and Movements remain unchanged, including already shipped quantities.
Even metadata-only changes require review until automatic amendment is supported.
Explicit retry does not bypass this guard. New JSON cannot undo a physical event.

Late or conflicting versions are classified instead of guessed. InterpretationOutcome
shows whether a version was interpreted, stale, conflicting or required review.

### 24. When a manually entered order changes

Manual Evidence has an audited full-snapshot correction operation. Presentation and
reference data may be corrected. Economic line fields—Item, quantity, unit, price,
amount, promised time, line type and price provenance—cannot be rewritten after the
Document or line has linked Reality.

That prevents changing “10” to “7” underneath a Commitment, Reservation or Movement
created for ten. Once Reality exists, use explicit lifecycle handling: cancel the open
promise, release allocation and create correctly evidenced replacement intent.
Completed physical or financial events require their own return, correction, credit or
reversal.

### 25. Holds and deactivation

A Commitment hold blocks reservation and fulfilment until released. A Party delivery
hold blocks customer shipments for that Party. Holds are separate records with reason,
note, creator and release time; they do not erase the promise.

Deactivating master data prevents new use according to service rules but does not
invalidate history. An invoice keeps its agreed PaymentTerm and an order line keeps its
agreed price and optional PriceListEntry provenance. Later price changes never rewrite
Evidence.

## Part V — Reading the operational picture

### 26. Inventory formulas

```text
physical  = quantities into a Location - quantities out of it
reserved  = active Reservation quantities
available = physical - reserved
incoming  = open supplier Commitment quantities
projected = available + incoming
```

- **Physical** asks what is recorded at the Location now.
- **Reserved** asks how much is allocated to outgoing promises.
- **Available** asks what can still be allocated without double-promising.
- **Incoming** asks what suppliers still promise.
- **Projected** asks what could be available when incoming promises arrive.

### 27. What is open?

| Dimension | Open when | Closes when |
| --- | --- | --- |
| Customer Commitment | promise exceeds qualifying shipments | shipments fulfil it, or it is cancelled |
| Supplier Commitment | promise exceeds qualifying receipts | receipts fulfil it, or it is cancelled |
| Reservation | status is `active` | shipment consumes it or release frees it |
| Customer invoice | active receivable remains | derived amount reaches zero |
| Supplier invoice | active payable remains | derived amount reaches zero |

There is no universal “Document open” rule. An invoice can remain financially open
after full delivery. A sales order can have no open delivery quantity while its invoice
is unpaid. A cancelled promise can still have an unresolved credit or return.

### 28. Risk, projections and registers

Risk is computed, not copied onto a Document. It compares an outgoing Commitment's
open quantity with stock and relevant supply, while priority, due time and holds provide
context. The explanation can say “30 promised, 18 fulfilled, 12 open, seven reserved,
five short” instead of showing an unexplained red status.

Registers expose Commitments, Reservations, Movements, settlements, aging, journals,
handling units, lots and serial units. Materialized Projections support fast worklists.

```text
Reality records -> BusinessEvents -> Projection rows -> operational screen
```

If a Projection checkpoint trails the latest event, the view is stale and rebuildable.
Commands never trust it to permit excess shipment or over-allocation.

### 29. Inspector, explain and timeline

`explain commitment` returns the promise, parties, Item, Location, due date, state,
Reservations, Movements, fulfilled/open quantity, risk and the DocumentLine ->
Document -> SourceRecord chain with raw payload when present. It traverses opaque IDs,
not coincidentally matching numbers. Missing evidence is reported honestly.

The timeline interleaves SourceRecords, Commitments, Reservations, Movements and
LedgerEntries:

```text
09-02  SOURCE       Shopify order 4711 v1 received
09-02  COMMITMENT   deliver 12 BIKE-LIGHT
09-02  RESERVATION  allocate 12 BIKE-LIGHT
09-03  MOVEMENT     shipment 5 BIKE-LIGHT
09-04  MOVEMENT     shipment 7 BIKE-LIGHT
09-22  LEDGER       receivable debit EUR 1,470
09-25  LEDGER       receivable credit EUR 500
```

The cockpit stays simple because the Inspector preserves the deeper explanation.

## Part VI — Choosing the right record

### 30. Decision guide

Use a **Document** for a commercial statement. Use a **Commitment** for a genuine
directional promise that operations plans or measures. Do not create a Commitment just
because an upstream payload contains `status`, and do not require a Document when a
real promise exists without one.

Use a **Reservation** only to bind current stock to outgoing demand. “We owe 20” is a
Commitment. “Twelve are assigned” is a Reservation. “The supplier promises 20” is an
incoming Commitment. “Eight arrived” is a Movement.

Use a **Movement** for a physical quantity crossing a Location boundary. Use a **Fact**
only for an immutable, source-supported observation with a reviewed predicate that is
not already owned by another domain record.

Use an **adjustment** when today's physical count differs and the difference itself is
the observed event. Use a **correction** when a particular historical Movement was
entered incorrectly. Both may produce the same stock number, but tell different
stories.

Cancellation, return and credit act on separate axes:

| Event | Promise | Physical stock | Receivable |
| --- | ---: | ---: | ---: |
| Cancel open Commitment | changes | unchanged | unchanged |
| Release Reservation | allocation changes | unchanged | unchanged |
| Return Movement | unchanged | changes | unchanged |
| Sales credit | unchanged | unchanged | changes |

Posting a payment says money moved. Allocating it says which invoice it settles. This
is why a valid payment can be unallocated.

## Part VII — Guardrails and mental model

### 31. One application core

Web, CLI, API, MCP and Chat call the same application services and tools. They do not
write directly through the ORM or reimplement business formulas. “Ship five” therefore
has identical validation and effects through every interface.

Read-only agent queries need no confirmation. Mutating Chat actions first prepare a
ChangeProposal and server-derived preview; explicit human confirmation executes them.
An agent does not calculate its own inverse posting or available stock.

Every linked record is checked inside the tenant boundary. PostgreSQL is the only
supported database. Quantities and money use Decimal; timestamps are UTC internally.

### 32. The six questions

For any business case, ask:

1. **What arrived?** Preserve it losslessly as Source.
2. **What statement was recorded?** Represent stable commercial Evidence.
3. **What was promised?** Create a directional Commitment when one truly exists.
4. **What was allocated?** Reserve only current physical stock for outgoing demand.
5. **What happened?** Append physical Movements and financial LedgerEntries.
6. **What is the answer now?** Derive stock, fulfilment, risk and open balances.

At month end, every material number reconciles to these records. Stock reconciles to
Movements; availability to active Reservations; open delivery to Commitments and
fulfilment Movements; receivables to balanced postings and SettlementAllocations;
corrections to original, inverse and replacement records. Documents remain essential
Evidence, but Reality—not the Document—is the operational authority.

## Appendix A — Table map by responsibility

The exact current inventory is maintained in [Data Model](DATA_MODEL.md).

| Responsibility | Principal tables |
| --- | --- |
| Company access | `tenant`, `tenant_membership`, `company_invitation`, `invitation_delivery`, `security_audit_event` |
| Master data | `party`, `party_role`, `party_hold`, `item`, `location`, `payment_term` |
| Pricing | `price_list`, `price_list_entry`, `party_price_list`, `party_group`, `party_group_member`, `party_group_price_list` |
| Integration | `source_system`, `source_capability` |
| Source intake | `source_stream`, `source_record`, `source_artifact`, `import_job`, `interpretation_outcome`, `interpretation_record_reference` |
| Evidence | `document`, `document_line` |
| Promise and execution | `commitment`, `commitment_hold`, `reservation`, `movement`, `movement_correction` |
| Warehouse identity | `handling_unit`, `lot`, `serial_unit` |
| Finance | `ledger_entry`, `ledger_reversal`, `settlement_allocation` |
| Observation and audit | `fact`, `action`, `business_event` |
| Read optimization | `projection_row`, `projection_checkpoint` |
| Conversation | `chat_session`, `chat_message` |

## Appendix B — Common misconceptions

**“The sales order is fulfilled, so the invoice must be paid.”** No. Delivery and
payment are independent Reality axes.

**“Reserved stock has left the warehouse.”** No. Only a Movement changes physical
stock.

**“Incoming supply is available stock.”** No. It contributes to projected availability
but cannot be shipped before receipt.

**“A new source version edits the old order.”** No. It preserves a new SourceRecord.
Shopify updates currently require review and leave prior Evidence and Reality intact.

**“A correction deletes the mistake.”** No. It appends an inverse and optional
replacement, preserving the explanation.

**“A payment belongs directly to an invoice.”** The payment has its own Evidence and
posting. SettlementAllocation expresses how much applies to an invoice.

**“A projection is another source of truth.”** No. It is a rebuildable read model.

**“Every upstream field needs a column.”** No. SourceRecord preserves the payload. A
field becomes typed only when repeated core behavior proves the need.
