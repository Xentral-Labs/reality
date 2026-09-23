# One Order End to End

[Back to the guide overview](../business-reality-guide)

## 1. Your understanding check: is Northstar's order complete?

All 30 lamps are recorded as shipped from Acme to Northstar. Invoice `INV-1001` states EUR 1,470,
with EUR 500 payment allocated and EUR 100 credit applied. There are no further movements,
reservations or financial entries in this base sequence.

Before reading on, answer “Is order `SO-1001` complete?” Which statements can you support, and what
information is missing?

<details>
<summary>Show answer</summary>

The delivery promise is fulfilled: 30 were promised and 30 are recorded as shipped. Nothing remains
reserved for this order. Financially, EUR 870 remains open. Without the due date and assessment
date, overdue status is not established. Shipment movements alone do not prove arrival at the
customer either.

“Complete” therefore needs a business meaning. Delivery and financial settlement have different
bases.

</details>

## 2. How the records fit together

This short **Reality-Timeline** is an explanation, not a live agent response or a promise that a
current product view presents this exact table. It connects the warehouse sequence in
[chapter 2](./02-orders-stock-and-deliveries) with the invoice in
[chapter 3](./03-invoices-and-payments).

The original order information is preserved as a **SourceRecord**. **Document** and **DocumentLine**
record `SO-1001`. Acme's **Commitment** to Northstar holds the delivery promise; each
**Reservation** allocates stock to it and each fulfilling **Movement** records a shipment.

| Business event                               | Authoritative records                                  | Result in the base sequence                                 |
| -------------------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------- |
| Eight lamps at the start                     | Opening-stock Movement                                 | Eight present                                               |
| Northstar orders 30                          | Order, line and customer Commitment                    | Thirty to deliver                                           |
| Allocate the existing eight                  | Reservation                                            | Eight reserved, 22 unreserved                               |
| Order 22 from Alpine Components              | PO-2001 and supplier Commitment                        | Twenty-two expected                                         |
| Receive ten and twelve; reserve each receipt | Two receipt Movements and additional Reservations      | Thirty present and allocated                                |
| Ship 18 and twelve to Northstar              | Two shipment Movements against the customer Commitment | Thirty fulfilled, zero open; matching Reservations consumed |

The warehouse ends with zero lamps from this base sequence, zero active reservations and zero
available stock. The invoice is linked to the order line it bills; that relationship does not need
to be guessed afterwards from equal amounts.

## 3. Money remains a separate axis

| Operation on INV-1001          | Records and relationship                                          | Open amount |
| ------------------------------ | ----------------------------------------------------------------- | ----------: |
| Post invoice stating EUR 1,470 | Invoice document and balanced LedgerEntry records                 |   EUR 1,470 |
| Allocate EUR 500 payment       | Separate payment posting and SettlementAllocation to this invoice |     EUR 970 |
| Apply EUR 100 credit           | Separate credit posting and settlement of this invoice            |     EUR 870 |

The invoice amount is received authority. The open amount comes from postings and applied
settlements. No additional “paid” Fact is created to hold those answers.

## 4. How an agent might answer

> Delivery for Northstar's order SO-1001 is fully recorded as shipped: 18 and twelve lamps against
> the promise of 30. No active reservation remains for this order. The linked invoice INV-1001 has
> EUR 870 outstanding: EUR 1,470 invoiced less EUR 500 allocated payment and EUR 100 applied credit.
> I cannot establish whether that remainder is overdue without checking the due date. Next I would
> check the due date and further incoming payments. I have not changed any records.

In a real answer, delivery and reservation claims must lead to Northstar's Commitment and its
records. The open amount must lead to the invoice posting, payment, SettlementAllocation and credit.
Where available, provenance can be followed to the original input. Readable example numbers do not
replace those technical relationships.

The agent reads current state and states its limits. A proposed next step is not an executed action.
A Reality change does not automatically update an external ERP or send money through a provider.

## 5. What you can transfer to other cases

Returns, warehouse corrections and cancellations in chapter 2's variants are **not part of this base
sequence**. If one actually occurs, its own records change the answer. Historical deliveries or
sources are not simply deleted.

For another order, ask the same questions: what was recorded, promised, allocated, moved and posted?
What answer follows now? A work list or Projection helps you read but does not replace the records
that explain it.

One question remains: what happens to additional customer information such as “Please deliver to the
side entrance”? Continue to [Facts and Open Questions](./06-facts-and-open-questions).
