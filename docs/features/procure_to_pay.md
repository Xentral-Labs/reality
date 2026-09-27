# Feature: Procure to Pay

## V0 story

1. Create an incoming supplier-delivery Commitment, optionally backed by a purchase
   order Document.
2. Record partial/full receipt Movements and derive fulfillment.
3. Make received stock available for customer reservations.
4. Record supplier-invoice evidence and balanced expense/inventory/payable entries.
5. Record partial/full supplier payments.

## Trace

`Purchase Document/Line → Supplier Commitment → Receipt Movement`

`Supplier Invoice Document → LedgerEntries`

## Done when

A deterministic test proves partial receipt, final receipt, supplier invoice, partial
payment, open payable, tenant isolation, and traceability. Purchase-document status is
not used as a proxy for receipt or payment.

## Supplier Credits

A supplier credit note is recorded, booked as the reverse of the supplier invoice, and then
either netted against what the company still owes that supplier or refunded in money. Two
operational exception classes watch it: one for a credit nobody booked, which makes the payable
too high and a payment run pay too much, and one for a booked credit nobody has claimed, which
is the company's own working capital sitting with a supplier.

## Supplier Returns

The goods half, added by spec 090. `supplier_return` takes goods out against the delivery they
arrived on, bounded by what actually arrived, and it can settle a customer return — so a faulty
item a customer sent back can be shipped on to the supplier and the customer's return stops being
reported as unresolved.

Two classes close the chain: `supplier_return_not_credited` reports goods that went back and were
never credited, counting only what a supplier invoice actually billed; and
`supplier_credit_not_returned` reports a supplier crediting more than went back, silent while
nothing has gone back so that a rebate is never mistaken for a discrepancy.

`receipt_unbilled` now counts what the company still holds, so it stops accruing an invoice for
goods that went back. `billed_not_received` still counts the raw receipt, because the goods did
arrive and a return does not unmake that.

## Recording and Booking

A supplier invoice is recorded and booked by two separate operations, both reachable from every
surface. Until it is booked, `overdue_payable`, `purchase_discount_available` and the
early-payment discount reason cannot see it, and no supplier credit can be netted against it.
See [the ledger](./ledger.md).

One supplier invoice may bill received positions of several purchase orders of one supplier in
one currency (spec 283). The guided entry collects them from `invoice_billable_positions`: what the
company still holds (received less sent back) and is not yet billed, grouped by purchase order.
Each invoice line links to its own order line, so `billed_not_received` stays per line.

## Supplier Acknowledgements

A supplier that acknowledges an order with a different date is the ordinary event in every
buying relationship, and it is recorded as a statement rather than by overwriting the promise.
A supplier confirming a smaller quantity is the same statement: *"eighty pieces, two weeks
later"* is recorded once, and everything downstream measures against eighty and against that day.
`overdue_incoming_supplier_commitment` says the promise was moved once the stated day passes
too. See
[commitments](./commitments.md) for the record and
[operational exceptions](./operational_exceptions.md) for what the queue does with it.

## The Payment Run

A company pays its suppliers on a day, not one at a time. `preview_payment_run` says what is
worth paying and writes nothing; `execute_payment_run` pays what somebody confirmed, in one
transaction.

The preview proposes two kinds of invoice: one due on or before the day the run is being made
for, and one whose early-payment window has not closed yet — because an invoice nobody has to
pay for weeks can still be the one worth paying this afternoon. It reports what each supplier is
owed and totals **per currency**, never across them, since a run pays in one currency and a sum
of two is not a total. It orders by the day the money is needed — an open discount deadline where
there is one, the due date otherwise — and then by identity, so two identical reads return an
identical answer.

**It computes nothing.** This is the whole shape of the feature. An ERP payment run is
mechanically a discount calculator: it walks the open payables and pays gross minus a rate. That
multiplication is the largest source of money nobody agreed to in an ERP — 2% of 1,234.56 is
24.6912, somebody rounds it, and the rounded figure becomes what a supplier is told they were
paid. So the preview names the rate the company negotiated and the day it expires, and a person
states the amount. Paying 980 of 1,000 leaves 20 open, which is reported as an overdue payable
with the early-payment-discount reason exactly as it is after a single payment. Spec 088 decided
that and this does not revisit it.

One rule decides what is payable, and the preview and the run both ask it: a supplier invoice,
not reversed, with something open, and not already reported as a duplicate. The duplicate is the
one exclusion that **refuses** rather than warns — paying it is money that does not come back,
and the class has a clearing path, so refusing traps nobody. A sales invoice is absent from the
answer rather than withheld; it was never a candidate. The duplicate grouping itself lives in the
service layer with the exception class as its second consumer, because two answers to "is this a
duplicate" is how a proposal and the operation that executes it start disagreeing about money.

The run refuses everything before it writes anything: an empty list, a missing reason, an invoice
named twice, an invoice that is not payable, an amount above what is open, a currency that does
not match, and a set of amounts that does not sum to the confirmed total. The confirmation figure
is a **total** rather than a count — Spec 085 confirmed a count because a count was what the
person had looked at, and here a person approves an amount of money while the list is usually
assembled by a client from the proposal, where every line can be right and the sum still wrong.

Then it posts every payment through the same operation a single payment uses, so a payment made
in a run is the same posting as one made alone, and commits once. A failure anywhere rolls the
whole thing back. That is the reason the operation exists: the alternative is a Friday where
nineteen payments went out and twenty-one did not and somebody has to work out which. One
`payments.run` event records the reason, the total, the currency and every invoice with what was
paid against it — a run is a decision about payments, not a payment, so it is an event and not a
document.

**What it does not do:** there is no durable way to say "do not pay this one". Holding an invoice
back means leaving it out of the run, and it reappears in the next preview. That is strictly
correct — it is unpaid, and this queue reports what is unresolved until somebody resolves it —
and it is mildly annoying every week for an invoice under dispute. Reality also does not move
money; a run records that the company paid.
