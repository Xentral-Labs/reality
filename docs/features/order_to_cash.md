# Feature: Order to Cash

## V0 story

1. Ingest a lossless Shopify order SourceRecord.
2. Interpret only stable fields into sales Document and DocumentLine evidence.
3. Create an outgoing customer-delivery Commitment from the line.
4. Reserve available inventory and expose shortage.
5. Record one or more shipment Movements; derive fulfillment.
6. Record invoice evidence and balanced receivable/revenue LedgerEntries.
7. Record partial/full customer payments and optional credits.

## Trace

`SourceRecord → Document → DocumentLine → Commitment → Reservation/Movement`

Financial evidence links through the invoice Document to its LedgerEntries. Delivery
status and financial status are independently derived.

## Prepayment fulfillment policy

`PaymentTerm.requires_prepayment` is the explicit commercial policy. Codes, names and zero due
days never imply prepayment. For a customer-delivery Commitment, fulfillment readiness follows
the shortest evidence path from its sales-order line to billed invoice lines, the invoice's
receivable LedgerEntry and active SettlementAllocations. It reports the order's stated gross as
required, qualifying allocated payment as received, and their non-negative remainder.

Missing invoice evidence, ambiguous cross-order invoice attribution, or an unpaid remainder are
dispatch blockers. Tenant, customer and currency must agree. Reversed posting groups do not
qualify. Ordinary net-term orders are not blocked merely because they are unpaid.

## Done when

A deterministic test proves full and partial fulfillment, partial payment, credit,
tenant isolation, source traceability, and balanced postings without direct ORM writes
from CLI, Web, or Chat.

## Recording and Booking

A sales invoice is recorded as evidence and booked into the ledger by two separate operations,
both reachable from every surface that reaches a credit note. Nothing on the receivable side —
the aging register, `overdue_receivable`, `credit_limit_exceeded`, netting a credit note, taking
a payment — sees an invoice until it is booked. See [the ledger](./ledger.md) for why the two
acts stay apart.

## Payment matching

Step 7 records payments on explicit command or through a source. Source-delivered payments pass
the shared intake core in [payment_matching.md](./payment_matching.md): recorded always, allocated
only when the source states an unambiguous reference, otherwise offered as read-time candidates.
[Feature 168](../../specs/168-demo-order-to-cash/spec.md) delivered it through the synthetic Demo
Data source.
