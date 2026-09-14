# Quickstart: The Parcel That Has Not Left Yet

**Language**: English

Eleven tests in `tests/test_return_announcements.py` and five in the derivation suite. One
migration.

## Story one — the customer says they are sending it back

Five shipped against a customer delivery. The customer announces two with a reference, a reason
and the day they say it will go, and all four are recorded exactly as stated — nothing normalised
and nothing generated. The delivery is untouched: it still promised five, and nothing has come
back.

A customer who names no day is not a customer promising *soon*. The absence is the statement.

Two announced leaves three announceable, so a further four is refused; three is accepted. The
same rule bounds the returning movement, and a test asserts nothing else computes it. A
withdrawal keeps what was announced and returns the delivery to its full five.

**Result**: passes.

## Story two — the parcel arrives

The movement names the announcement it fulfils **and** still names the delivery it reverses. One
of two arriving leaves the announcement open for one; the second finishes it at that moment,
without waiting for a later event that may never come.

Three arriving against an announcement of two is accepted — both statements are true and the
third item physically exists — and the delivery's own bound still holds. A return naming another
delivery's announcement, an announcement that is not open, or no delivery at all is refused. A
return naming no announcement behaves exactly as it did before this shipped.

**Result**: passes.

## Story three — nothing arrived

An announcement whose stated day has passed is reported and says the day the customer stated,
claiming no learned norm. An announcement with no stated day, standing longer than this company's
own rhythm, is reported and says the norm it was judged against. A company with four arrivals and
no stated day is not judged at all — and one more finished case makes the same announcement
appear, so the silence was the minimum speaking rather than the class being absent.

The goods arriving ends the entry with nothing stored. A withdrawn announcement is never reported.

**Result**: passes.

## What the story taught

**The obvious model was rejected on a measurement.** An announced return is a directional promise
and `Commitment` is the product's word for one, so a third `Commitment.type` is what a reader of
the Constitution would expect. Counting first changed the answer: `customer_delivery` is read in
**32 places across 8 modules, 17 of them a two-way branch** whose `else` silently means *supplier
delivery*. A third value makes all seventeen wrong, and most would keep passing their tests
because no test asks what a branch does with a type that does not exist yet. That is the shape of
bug this work has already been bitten by twice — a rule correct while one case existed and quietly
wrong the moment a second one did. The honest cost of the table is one more entity, and the plan
records that this is the first thing to fold in if the commitment vocabulary is ever widened
deliberately.

**Writing the learned threshold the obvious way measured the wrong thing.** The first version
learned from `announced_at` to `closed_at`, and `closed_at` is the instant somebody wrote the
arrival down. A backdated parcel would have taught a lag of weeks, so five one-day arrivals
produced a threshold of two hundred days and the derivation test failed for a reason that looked
like a threshold bug. It reads the movement's own `occurred_at` now, which is what
`return_unresolved` already does — the rule was there to copy and the first draft did not.

**A refusal that could not fire.** The guard for an unreadable expected day was written before
checking what `utc_datetime` does with garbage: it raises, so the guard was unreachable and its
test would have passed for the wrong reason. It now guards the case it can actually see — an empty
day, which the promise revision refuses the same way — and a second assertion pins the ISO error
for garbage.

**Better errors came from moving one check.** Naming an announcement on a shipment first produced
*"Movement exceeds the commitment's open quantity"*, because the commitment was judged before the
announcement was looked at. Resolving the announcement first costs nothing and tells the caller
what is actually wrong.

## What this deliberately does not do

**An announced return is not supply.** Nothing touches availability, replenishment or the
fulfilment queue. A company therefore cannot plan around announced returns, which is the point:
goods a customer has promised to send are not goods anybody can sell, and treating them as supply
is how a warehouse commits stock that never arrives.

The money half is untouched — a credit note still follows the goods, as Spec 079 decided. The
mirror case, telling a supplier that goods are coming back, is left out deliberately rather than
half-built. And Reality tells the customer nothing; it records that somebody said something.
