# Orders, Stock and Deliveries

[Back to the guide overview](../business-reality-guide)

## Follow Huber's order through warehouse and purchasing {#orders-and-inventory}

Huber orders 30 lamps. Eight are in Augsburg; Acme buys the missing 22 from LightWorks. We follow
which actions create records and which figures are derived from them. Invoice and payment come in
the next chapter.

The base case has one item, one location and no other orders, movements or holds. Here, “stock”
means physical stock calculated from recorded goods movements. “Available” is the part not already
allocated to a delivery promise.

### 1. Record the starting point

**In the business:** Eight lamps are in the warehouse. **In Reality:** Acme records that opening
stock as a goods movement into the location. This creates a **Movement** of type `opening_stock`.

**The result:** Eight physically present, zero reserved, eight available. These are calculated
balances, not a second independently entered authority.

### 2. Entering a sales order

**In the business:** Huber orders 30 lamps. **In Reality:** The supported manual order operation
preserves the input as a **SourceRecord**, records order `SO-1001` as a **Document** with its
**DocumentLine**, and explicitly creates a **delivery promise (Commitment)** from Acme to Huber for
30 units.

**The result:** Thirty remain to deliver. Warehouse stock remains eight. The order alone does not
reserve goods. An arbitrary document does not create a promise either; that belongs to the supported
order operation or importer.

### 3. Allocate existing stock

**In the business:** Acme wants to set aside available lamps for Huber. **In Reality:** An explicit
reservation action requests 30 against the promise. The service checks open demand and available
stock, then creates a **Reservation** for the eight available units.

**The result:** Eight are allocated to Huber, 22 remain unreserved, and none are free. All 30 still
remain to deliver. Allocating stock does not fulfil a promise.

The shortfall is a calculated answer. If nothing is available, no Reservation is created. The
shortfall does not automatically create a purchase order.

### 4. Order the missing lamps

**In the business:** Acme orders 22 lamps from LightWorks. **In Reality:** The supported purchase
order operation creates `PO-2001`, its line and a supplier promise for 22. This is also a
**Commitment**, this time from LightWorks to Acme.

**The result:** We expect 22 lamps. Eight remain in the warehouse, all reserved for Huber. Promised
supply is planning information. It is not existing stock and cannot be shipped as such.

### 5. A partial goods receipt: ten lamps

**In the business:** LightWorks delivers ten. **In Reality:** Acme records the actual receipt as a
**Movement** of type `receipt`, linked to the supplier promise.

**The result:** Eighteen are in stock; eight are reserved and ten are free. LightWorks still owes
twelve. Receipt does not automatically assign the new stock to Huber.

Acme therefore reserves the ten newly available lamps for Huber with a separate action. This creates
an additional Reservation. Eighteen are now allocated and none are free.

### 6. Receive and reserve the remaining twelve

The second receipt creates another Movement for twelve. LightWorks has now delivered all 22. Thirty
lamps are in the warehouse; 18 are already allocated to Huber. Another explicit reservation action
allocates the remaining twelve.

All 30 are now present and reserved. None has yet shipped to Huber.

### 7. Ship in two parts

**In the business:** Acme first ships 18 lamps to Huber. **In Reality:** Acme records that shipment
as a **Movement** of type `shipment` against Huber's Commitment. The operation consumes the matching
active reservations automatically; no separate release of their allocation is needed.

**The result:** Eighteen delivered, twelve still to deliver. Twelve remain in the warehouse and stay
reserved. The second shipment of twelve creates another Movement and completes the delivery promise.
Stock and active reservations are then zero.

Recording a Movement does not move goods. It records the actual warehouse event. Ensuring that the
goods were physically issued and the record is correct remains an operational responsibility.

### The quantities together

Every value refers to the same item and location. “Open” means Huber's outstanding delivery.

| After this step          | Physical | Reserved for Huber | Available | Shipped to Huber | Open |
| ------------------------ | -------: | -----------------: | --------: | ---------------: | ---: |
| Opening stock            |        8 |                  0 |         8 |                0 |    0 |
| Order for 30             |        8 |                  0 |         8 |                0 |   30 |
| First reservation        |        8 |                  8 |         0 |                0 |   30 |
| Receipt of ten           |       18 |                  8 |        10 |                0 |   30 |
| Another ten reserved     |       18 |                 18 |         0 |                0 |   30 |
| Receipt of twelve        |       30 |                 18 |        12 |                0 |   30 |
| Another twelve reserved  |       30 |                 30 |         0 |                0 |   30 |
| Shipment of 18           |       12 |                 12 |         0 |               18 |   12 |
| Final shipment of twelve |        0 |                  0 |         0 |               30 |    0 |

The order remains the document for what was ordered. “Partially delivered” or “fully delivered”
comes from the Commitment and linked shipment movements. No delivery status is held on the Document.

### Check your understanding

The supplier's first ten lamps have arrived but have not yet been reserved. How much is physically
present, how much is allocated to Huber, and how much remains to deliver to Huber?

<details>
<summary>Show answer</summary>

Eighteen physically present, eight reserved for Huber, and 30 still to deliver. Receipt, allocation
and customer shipment answer three different questions.

</details>

<details>
<summary>Technical detail: records and partial reservations</summary>

The reservations in this base case are three records against the same customer Commitment:

```text
Reservation: commitment = HUBER-..., quantity = 8, status = active
Reservation: commitment = HUBER-..., quantity = 10, status = active
Reservation: commitment = HUBER-..., quantity = 12, status = active
```

A partial shipment within one Reservation consumes the original record (`consumed`) and creates a
new active record for the remainder. The original quantity is not overwritten. Once a promise is
fully fulfilled, the service sets it to `fulfilled`.

A real supplier promise can precede its document. An actual receipt can also be recorded without a
known promise. Missing relationships remain visible.

</details>

To try it: <ProductLink>Open Reality</ProductLink>. Use a separate learning company and check it
before each confirmation. These actions really change records there.

## Variants outside the base sequence

The following cases do not change the table above. They show what to do when the business case
changes. On a first reading, skip this detail and continue to
[Huber's invoice and payment](./03-invoices-and-payments).

<details>
<summary>Cancellation, returns, recording errors and changed orders</summary>

## Changes, Returns and Corrections {#changes-and-corrections}

### Cancellation, return and adjustment

Velo Store orders ten helmets and six are reserved. The customer cancels before shipment. Cancelling
the Commitment records its cancellation time and releases active Reservations. It creates no
Movement because nothing moved. Physical stock is unchanged; available stock rises by six.

In a separate variant, Huber later returns two shipped lamps. A `return` Movement into the Returns
Area increases stock there. It does not erase the historical shipment or reopen the fulfilled
delivery promise. A commercial credit is a separate financial event.

A count then finds one missing light. An outbound `adjustment` from Augsburg with a reason records
the difference. It does not edit a stock balance.

### Correcting a wrong warehouse entry

Suppose the receipt of ten should have been seven. The original is not edited. One correction
operation appends:

1. an exact inverse `correction` Movement with quantity ten;
2. a normal replacement Receipt Movement with quantity seven;
3. a MovementCorrection relation joining all three;
4. affected Commitment reconciliation;
5. a `movement.corrected` BusinessEvent.

Net stock and fulfilment become seven. The Inspector still shows what was first recorded and why it
changed. A compensation cannot itself be corrected; a wrong replacement starts a new correction
chain.

## Customer Changes, Holds and Lifecycle {#lifecycle}

### When an external customer changes an order

In this integration variant, an order arrives from the Shopify shop system. Its order 4711
originally contains ten lamps and later seven. The structured data received is called the payload;
JSON is its exchange format. Version 2 does not overwrite version 1. It creates a new SourceRecord
in the same SourceStream.

The current Shopify interpreter retains that update as `needs_review`. Previous Documents,
Commitments, Reservations and Movements remain unchanged, including shipped quantities. Even
metadata-only changes require review until automatic amendment is supported. Explicit retry does not
bypass this guard. New JSON cannot undo a physical event.

Late or conflicting versions are classified instead of guessed. InterpretationOutcome shows whether
a version was interpreted, stale, conflicting or required review.

### When a manually entered order changes

Manual Evidence has an audited full-snapshot correction operation. Presentation and reference data
may be corrected. Economic line fields—Item, quantity, unit, price, amount, promised time, line type
and price provenance—cannot be rewritten after the Document or line has linked Reality.

That prevents changing “10” to “7” underneath a Commitment, Reservation or Movement created for ten.
Once Reality exists, use explicit lifecycle handling: cancel the open promise, release allocation
and create correctly evidenced replacement intent. Completed physical or financial events require
their own return, correction, credit or reversal.

### Holds and deactivation

A Commitment hold blocks reservation and fulfilment until released. A Party delivery hold blocks
customer shipments for that Party. Holds are separate records with reason, note, creator and release
time; they do not erase the promise.

Deactivating master data prevents new use according to service rules but does not invalidate
history. An invoice keeps its agreed PaymentTerm and an order line keeps its agreed price and
optional PriceListEntry provenance. Later price changes never rewrite Evidence.

</details>

Next: [Invoices and Payments](./03-invoices-and-payments).
