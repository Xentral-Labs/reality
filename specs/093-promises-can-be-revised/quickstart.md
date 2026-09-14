# Quickstart: When the Other Side Says a New Date

**Language**: English

Three acceptance stories, run against PostgreSQL as part of
`tests/test_commitment_revisions.py` and `tests/operational_exceptions/test_derivation.py`.

## Story one — the supplier names a new date

A supplier delivery due twenty days ago is reported as overdue. The supplier acknowledges a day
five days out; it stops being reported, because it is not late until that day. Read the queue ten
days later and it is overdue again — the revision moved the judgement rather than removing it.

**Result**: passes.

## Story two — a revision cannot buy silence

Same promise, revised to a day that has *also* passed. The entry comes back carrying the
`promise_was_revised` reason, the day it was originally due, and the number of times it has
moved.

Nothing else about the entry changed: same severity, same record, same remaining quantity, same
trace. A promise late against a date its own counterparty chose is exactly as overdue as any
other, and now it says so.

**Result**: passes.

## Story three — no statement is ever lost

Two revisions on one promise: both are kept, in the order they were stated, and the promise's own
date is untouched. That is what makes "originally due" answerable at all.

Refused where it makes no sense — a cancelled promise, a fulfilled one, an unknown one, an
unreadable date — each with a positive control. Accepted where it might look wrong: a promise on
hold (a hold stops execution, and this records a statement), and a date already past (a supplier
admitting it will be three days late is the most useful kind).

**Result**: passes.

## And an undated order stops being undated

Stating a date for an order nobody dated moves it out of `order_stalled`. That is the one
existing class this feature changes, and it changes correctly.

## What the story taught

**The schema change exists to prevent an overwrite, not to record something new.** A
`confirmed_due_at` column would have been one column instead of a table — and would have
destroyed a supplier's first statement the moment it made a second. A date somebody stated is a
received value. So the table is the *smallest* design that obeys the Constitution, not the larger
of two options, and that is worth saying because it looks like the opposite at first glance.

**Judging against a revised date is a loosening, and naming it as one mattered.** An order three
weeks late stops being late because somebody typed a new date. That is right — the queue should
measure against the date people are working to — and it is still a loosening. What limits it is
the reason on the entry and the original date being kept, not a threshold nobody has measured.

**The blind spot is written down.** A supplier that moves the date repeatedly and always beats
the revised one is never reported. Arguably correct, since it meets the promises it actually
made; a company that agreed to the first date may disagree, and Reality is silent on the
difference. In the assumptions and in the class's own guidance rather than left to be found.

**The date in force is the third derived figure this line of work has had to keep
single-sourced** — unit comparability in 087 and the learned thresholds in 089 were the others.
It was written as one rule from the start, with a test asserting exactly one function asks for
it, rather than discovered as three copies later.

**The drift gates did most of the review.** Adding three services and one event broke forty tests
across five files until the isolation catalog, the command catalog, the business event catalog
and their counts agreed. None of that was subtle work; all of it would have been easy to forget.
