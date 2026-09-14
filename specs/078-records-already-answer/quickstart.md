# Quickstart: Two Answers the Records Already Hold

**Language**: English

Two independent acceptance stories, each run against PostgreSQL as part of
`tests/operational_exceptions/test_derivation.py`.

## Story 1 — A customer past the limit agreed with them

Record a customer with a limit of 1000, invoice them 1200, and read the queue. One entry on
the Party: limit 1000, outstanding 1200, excess 200. Take a payment of 600 and the entry
clears on the next read.

Invoice a customer with a limit of 1000 exactly 1000 and nothing appears; add a single cent
and it does. Record a customer with no limit at all and nothing appears whatever they owe;
record a limit and the same customer is reported immediately.

**Result**: passes, including the boundary and both directions of the zero convention.

## Story 2 — The same supplier invoice twice

Record `ER-4711` from one supplier, then again. One entry on the second document naming the
first. A third produces two entries, both naming the first. The same number from a different
supplier produces nothing; the same number from the same supplier does. ` er-4711 ` matches
`ER-4711`. Two invoices with no number at all match nothing.

Reverse the first invoice's posting and the entry disappears — a withdrawn invoice cannot be
paid twice, and a supplier reissuing a corrected invoice under its original number is
ordinary.

**Result**: passes.

## The demo measurement, and the gate that was missing

The plan asked for a first-read volume on the demo tenant. Neither new class fires there:
the demo records no party with a credit limit, and its one supplier invoice has no twin.
Both classes are correctly silent, and the measurement says nothing about volume.

The first draft of this section went further and was wrong. It claimed the demo could not
exercise these classes because it holds no shipments and no supplier invoices, and concluded
that five of the last five classes were unreachable there. That came from measuring
`ensure_demo` — a small seed with one order — instead of `run_normal_month`, which is what
the demo runs. The real scenario ships goods three times, records a supplier invoice, takes a
return and ends with `shipped_not_billed` twice and `unexplained_movement` once. Spec 076's
quickstart carried the same wrong claim and is corrected in this branch.

What the mistake exposed is real and worth more than the claim was: **nothing asserted what
the demo's exception queue contains.** Spec 076 changed it — the two `shipped_not_billed`
entries are new since that merge — and no gate noticed, which is also why a wrong statement
about it survived a review. This branch adds
`tests/scenarios/test_normal_month.py::test_the_month_ends_with_exactly_these_exceptions`,
which pins every entry with the act that produces it, so the next class that changes the
demo has to say whether that is an improvement or a regression.

## What the stories taught

**Reading beats adding.** Both conditions were answerable from records the product has held
all along. `credit_limit` shipped with the master-data baseline, is validated on write and
appears in the audit trail; nothing had ever read it. The first thing to ask about a missing
exception is not what to store but what is already stored and never asked.

**A convention has to be stated where an operator reads it.** Zero meaning "no limit
recorded" is a defensible reading and an indefensible silence: a company that deliberately
puts a customer on cash-only terms records zero and gets nothing. The convention is written
into the class's own guidance rather than left in a specification, because the person who
needs it is looking at the queue.

**Judging is not the same as refusing.** A duplicate supplier invoice could be refused at
write time, and that would be the wrong instinct here: the same invoice legitimately arrives
from two connectors, and refusing the second destroys the evidence that both arrived. What
was missing was the judgement, not the constraint. The class carries both source records for
exactly that reason — whether the second was typed in or came from a system is what decides
what an operator does about it.

**Reading Documents rather than open items was the deliberate choice.** Everything else in
this family consumes the settlement derivation. The duplicate class does not, because an
invoice nobody has posted yet does not appear there — and the duplicate worth catching is the
one caught before it is paid.
