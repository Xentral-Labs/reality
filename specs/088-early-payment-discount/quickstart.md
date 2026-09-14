# Quickstart: The Discount Nobody Is Watching

**Language**: English

Two acceptance stories, run against PostgreSQL as part of
`tests/operational_exceptions/test_derivation.py` and `tests/test_payment_terms.py`.

## Story one — take the discount while it is there

Record a payment term granting two per cent within ten days, net thirty. Post a supplier invoice
for 1,000 dated six days ago. The queue names the rate, the day it expires and the 1,000 the
ledger holds open, and says four days are left. The same invoice under a term granting no
discount says nothing at all.

Pay it and the entry is gone. Post another one dated a month ago and it never appears, because
there is nothing left to take.

**Result**: passes.

## Story two — stop chasing a customer who paid what was agreed

A 1,000 invoice under the same term, paid 980 on the fourth day. Before this feature the twenty
that was left reported as an overdue receivable from the due date onward, for ever, next to
genuine debts.

Now the same entry appears — twenty really is open — carrying the reason
`early_payment_discount_taken`. The outstanding amount, the severity and the days overdue are
exactly what they were. What changed is that an operator can tell this invoice from one nobody
has paid.

Three neighbours, each proving the reason is a rule rather than a label:

- Paid 900 on the fourth day: no reason. A hundred is more than the agreed rate allows.
- Paid 980 on the twentieth day: no reason. The window had closed.
- Never paid: no reason. It is simply overdue.

**Result**: passes, on both sides of the business — a customer taking a discount and the company
taking one from a supplier are the same condition with the words reversed.

## No money is ever authored

An invoice of 1,000.13 under a two per cent term is the test for this. Two per cent of it is
20.0026 — a figure nobody agreed and one that has to be rounded before it can be said. It is
never said. The entry carries exactly two Decimal values: the rate the company stated and the
amount the ledger holds open.

The same discipline runs through the cause. Working out what the rate allows and comparing
against it would divide; both sides are multiplied out instead:

```
remainder x 100  <=  rate x gross
```

A test walks the syntax tree of the three functions involved and fails on any division node, so
this is a rule that can be reviewed rather than a convention that erodes.

## The demo month

Unchanged. It records no payment term granting a discount, so neither the class nor the cause
can fire there in either direction. Recorded here rather than presented as evidence.

## What the story taught

**The note was right this time, and checking was still worth it.** Spec 086 was blocked for
months by a note saying it needed a cost model, and that note was wrong. This one said it needed
schema, and it did — `PaymentTerm` carries `due_days` and nothing else, and a rate and a window
are not derivable from anything the model holds. The answer went in the Complexity Tracking
table rather than being assumed either way.

**A shipped class was producing a false positive per invoice.** Not a gap, a defect: on any
business granting an early-payment discount, `overdue_receivable` reported every invoice a
customer had settled correctly. It shipped that way and nobody noticed, because the residue is
small and the entry looks reasonable. A class that is wrong once per invoice is not partially
useful; it is one an operator learns to scroll past.

**Not suppressing it was the harder and better call.** Hiding the entry would have made the
queue look right and made a real open balance invisible, which is a worse lie than the one being
fixed. The remainder is genuinely open; what was missing was a way to say why.

**The drift gates earned their keep again.** Adding two columns broke thirty tests in four
files — the capability guidance gate refusing an undocumented service input. That is the gate
doing exactly what it exists for, and it was caught by running the whole suite before writing a
single derivation, rather than at the end.
