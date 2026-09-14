# Quickstart: The Invoice Nobody Booked

**Language**: English

Three acceptance stories, run against PostgreSQL as part of
`tests/operational_exceptions/test_derivation.py`.

## Story one — the sales invoice nobody booked

Give a tenant four booked sales invoices and leave one unbooked since June: **nothing is
reported**, because four is not a rhythm. Add two more booked ones and the forgotten invoice is
reported at once, judged against a fortnight floor.

One recorded yesterday says nothing — it is inside the norm. Booking the forgotten one clears the
entry with no manual step.

**Result**: passes.

## Story two — the supplier invoice nobody booked

The same on the buying side, with its own rhythm.

**Result**: passes.

## Story three — each document type learns its own rhythm

A tenant that books its sales invoices promptly and has never booked a supplier invoice: the
sales side has a norm, the supplier side has **none**, and the unbooked supplier invoice is not
reported. Give the supplier side its own history and it reports immediately.

This is spec 080's rule and spec 089's correction applied a third time: share the rule, never the
history. A company that books sales daily and supplier invoices at month end has two honest
rhythms, and one judging the other would accuse it of both.

**Result**: passes.

## The four sides stay apart

An unbooked sales invoice, supplier invoice, credit note and supplier credit note on one tenant
with four rhythms: each is reported by exactly one class, and by its own. Asserted rather than
assumed.

## Two silences, each with its positive control

- **A reversed posting is not an unbooked one.** The reversing entries carry
  `document_id=None`, so the original still reads as booked. That is also the right answer:
  unbooking something on purpose is not the same as never getting round to it. A genuinely
  unbooked invoice on the same tenant reports, so the silence is the rule speaking.
- **A document with no readable date says nothing**, because nothing can be said about how long
  it has stood. The same amount with a real date reports.

## What the story taught

**Ordering was not politeness.** This class could not have been built before spec 091. Until an
invoice could be booked from a surface, no tenant could have a booking rhythm — so a class that
learns a norm from behaviour nobody could perform would have been silent everywhere, or on the
demo wrong everywhere. Splitting the two specifications was the difference between a class that
works and one that lies.

**Writing four things down together showed one of them was already wrong.** Listing the document
types with the account that means "booked" made it obvious that `supplier_credit_unposted` had
been asking `inventory` since spec 089 while its own operation guards on `accounts_payable`.
Equivalent in practice — one posting touches both — so nothing was broken and nothing changed.
But a class and its operation disagreeing is true only until somebody changes one posting, and it
cost one line to remove. There is now a test asserting all four agree with their operations.

**The body needed no work at all.** Spec 089 had already generalised it to take the document type
and the account, for the buying side. Adding invoices was two constants and two four-line
derivators. The helpers were renamed — they had been called `_credit_notes`,
`_credit_is_posted`, `_credit_posting_threshold` — because a name that describes the only caller
a function once had becomes a small lie the moment it has four.

**These will be the first learned classes live on almost every tenant.** The credit-note siblings
are usually silent for want of history; invoices are not. If the unmeasured constants behind the
learned rule are wrong, this is where it shows first. That is an argument for shipping and
watching the first real tenant, not for waiting.
