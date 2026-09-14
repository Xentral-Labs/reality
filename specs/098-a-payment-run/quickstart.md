# Quickstart: One Friday, Forty Payments

**Language**: English

Fifteen tests in `tests/test_payment_runs.py`. No migration.

## Story one — what should go out on Friday

Three payable supplier invoices. One is due inside the day the run is being made for, one is due
a month later with no discount to lose, and one is not due for weeks but its early-payment window
closes in four days.

The preview proposes the first and the third, in that order — soonest money first, by an open
discount deadline where there is one and the due date otherwise. It says what each supplier is
owed, totals **per currency** and never across them, and names what it withheld: an invoice whose
posting was reversed, one recorded under a number its supplier already used, and one with nothing
open. Two identical reads of an unchanged tenant return an identical answer, and nothing was
written.

**Result**: passes.

## Story two — forty payments, one decision

A confirmed list of invoices and amounts with a matching total pays every one of them, settles
every invoice, and records one `payments.run` event with the reason, the total, the currency and
every invoice with what was paid against it.

If somebody settled one of them in between, the run is refused and **nothing at all** was posted.
Not a partial Friday.

A payment made in a run is the same posting as a payment made alone — the run goes through the
same operation. A run is a decision about payments, not a payment, so it is an event and not a
document.

**Result**: passes.

## Story three — the discount is named, never applied

An invoice of 1,000 with a 2% term still inside its window. The preview names 1,000 open, 2% and
the deadline. It states **no** discounted amount — one assertion checks that neither 980 nor 20
appears anywhere in the line.

The operator states 980. The run pays 980 and 20 stays open, which is reported as an overdue
payable with the early-payment-discount reason exactly as it is after a single payment.

**Result**: passes.

## What the story taught

**The most useful thing in this feature is the arithmetic it does not do.** An ERP payment run is
mechanically a discount calculator: walk the open payables, pay gross minus a rate. That single
multiplication is the largest source of money nobody agreed to in an ERP — 2% of 1,234.56 is
24.6912, somebody rounds it, and the rounded figure becomes what a supplier is told they were
paid. Principle VIII was written before this specification and this is the case it was written
for.

So what the run actually contributes is the three things that were genuinely missing: a read that
assembles what is worth paying, a transaction so a Friday cannot half-happen, and one record that
forty payments were one decision. Nothing else needed inventing.

**A guidance line named an operation that did not exist.** `purchase_discount_available` has said
"accounts payable, with whoever schedules the payment run" since Spec 088. That was a role the
product did not support, and it went unnoticed because nothing checks that a class's owner can do
what the class asks of them. It is the same kind of gap the capability audit found in Spec 091,
found the same way: by reading what the product tells people to do and asking whether they can.

**The duplicate rule moved down rather than sideways.** The run needs exactly the set the
exception class has grouped since Spec 078. Copying it would have given the product two answers
to "is this a duplicate", so the grouping moved into the service layer with the class as its
second consumer — `exceptions` already depends on `core` and not the other way round. That is
the fifth derived figure this line of work has had to single-source, after units, learned
thresholds, and the date and quantity in force.

**The confirmation figure is a total, not a count.** Spec 085 confirmed a count because a count
was what the person had looked at. Here a person approves an amount of money while the list is
usually assembled by a client from the proposal, where every line can be right and the sum still
wrong.

**One refusal is deliberately out of character.** The run refuses to pay an invoice reported as a
duplicate, and this queue reports rather than refuses almost everywhere else. Paying a duplicate
is money that does not come back, the class is the only payable condition marked high, and it has
a clearing path — so the refusal traps nobody. It is argued in the plan rather than assumed,
because it is the one thing a reviewer should be able to disagree with.

## What this deliberately does not do

There is no durable way to say "do not pay this one". Holding an invoice back means leaving it out
of the run, and it reappears in next week's preview. That is strictly correct — it is unpaid, and
this queue reports what is unresolved until somebody resolves it — and mildly annoying every week
for an invoice under dispute. A per-invoice block needs a schema change, a lifecycle and a release
path, which is a separable feature rather than a corner of this one.
