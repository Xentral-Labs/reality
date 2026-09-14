# Feature: Commitments

## Purpose

A commitment is a directional promise. Customer delivery and supplier delivery use
the same primitive with opposite directions. A commitment may be supported by a
document line, but documents are never its lifecycle authority.

## V0 behavior

- Create customer and supplier delivery commitments with opaque IDs.
- Require tenant-owned parties, items and locations.
- Fulfilled quantity is the sum of linked fulfillment movements.
- Open quantity is `promised - fulfilled`; it never becomes negative.
- `open`, `fulfilled`, and `cancelled` are commitment states.
- Partial movements leave a commitment open; complete movements fulfill it.
- Cancellation preserves the commitment and releases active reservations.
- Many promises may be closed at once, by a side of the business and a date they were due
  before, and only after somebody has previewed the set and confirmed the count they saw. A
  closure is refused if that count no longer matches, refused without a reason, and applied as
  one transaction. It never matches a promise with movement against it, one under a hold, one
  whose party is under a delivery hold, one that is not open, or one with no due date — and it
  touches no Document, LedgerEntry or Movement. The act is recorded once with the criteria, the
  reason and the number.
- A commitment may link to a Document and DocumentLine, or exist without either.

## Invariants

- Every read and write is tenant-scoped.
- A document status never represents delivery or fulfillment.
- Human document numbers are not used for joins or identity.
- Historical movements are append-only; corrections use compensating movements.

## Acceptance stories

1. Shipping 10 and then 20 against a promise of 30 yields 10, then 30 fulfilled.
2. A supplier receipt fulfills an incoming commitment using the same calculation.
3. Cancelling an open commitment retains it and releases active reservations.
4. Records from another tenant cannot be linked, read, or mutated.

## When the Other Side Says a New Date

A promise is created with a date and that date never changes. What changes is which date is in
force, and that is recorded rather than overwritten.

`revise_commitment` appends a `CommitmentRevision`: the day now stated, the quantity now stated,
or both, with when it was stated, an optional note and the source record it came from. A
statement must restate at least one of the two; one that restates neither is refused.

Both figures live in one record because *"eighty pieces, two weeks later"* is one sentence. Two
tables would give it two timestamps that can disagree about when the supplier said it. The promise's own `due_at` stays the
day the promise was made with, which is what makes "originally due" answerable at all.

**A table rather than a column, for one reason.** A `confirmed_due_at` column would have been
smaller and would have let a supplier's second statement erase its first. A date somebody stated
is a received value, and this product does not overwrite those.

`commitment_due_at` and `commitment_quantity` answer what is in force: **the latest revision that
stated that figure**, which is not necessarily the latest revision. A statement about the
quantity alone leaves an earlier date standing, and the other way round, because nobody restated
it. Where nothing has been stated, the promise's own figure stands. Revisions are ordered by when
they were stated and then by identity, so two statements in the same instant resolve the same way
on every read.

Everything that judges a promise asks those two rules: what is open, what the queue reports as
remaining, whether an order counts as complete, and the learned norm for how long fulfilment
takes.

A promise revised down to what has already arrived is **settled at that moment** rather than at
the next movement, because there may not be a next movement. That is the one stored thing a
revision writes, and it is the same field the movement path sets for the same reason.

A quantity below what has already moved is accepted: the supplier said eighty and ninety came,
both are true, and refusing would lose the statement. What is open becomes nothing.

**What this does not do:** stock reserved for the original quantity stays reserved when a promise
shrinks. Nothing releases it and no class reports it, because over-reserving has never been a
condition this queue reports. Releasing somebody's stock as a side effect of recording a sentence
would be the product deciding something it was not asked to.

A revision is not a correction. A correction says the record was wrong; a revision says the
record was right and the world moved. A promise on hold may still be revised — a hold stops
execution, and recording what the other side said is not execution — and a date already past is
accepted, because a supplier admitting it will be three days late is a real statement.

Only an open promise can be revised, and only its date: a different quantity is a different
promise, not the same one later.
