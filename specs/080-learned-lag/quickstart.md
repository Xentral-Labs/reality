# Quickstart: Long by This Company's Own Standard

**Language**: English

Two independent acceptance stories, run against PostgreSQL as part of
`tests/operational_exceptions/test_derivation.py`.

## Story 1 — The order that quietly stopped

Give a tenant six orders it shipped in about a day, then leave one undated promise standing
for sixty. One entry appears on that promise, with sixty days standing against a threshold of
seven. Ship it and the entry is gone on the next read.

The same promise with a due date produces nothing from this class and is reported by
`overdue_outgoing_customer_commitment` instead — never both. A cancelled promise produces
nothing and teaches the norm nothing. A tenant with only four finished orders is not judged at
all; the fifth makes a norm and the same standing promise reports immediately. A tenant that
ships in an hour does not report a three-day-old order, because three times an hour is not a
threshold anybody would act on — and once past the seven-day floor the same order does report.

**Result**: passes, including both directions of every silence.

## Story 2 — The receipt no supplier invoiced

Give a tenant six receipts its suppliers invoiced within three days, then receive goods and
leave them unbilled for sixty. One entry with ten received, none billed, sixty days standing
against a fortnight. A receipt two days old says nothing. Billing it clears the entry.

A pair recorded in different units is left alone; the same figures in the order line's own
unit report at once. A receipt voided by a movement correction stops counting entirely,
because it never arrived.

**Result**: passes.

## The norm is not the same statistic as Spec 072's

Spec 072 judges a silent source against **the longest pause that source has shown**. This
feature judges an order against **the median of the most recent twenty finished cases**, and
the difference is not a preference.

A source's pauses are bounded — nights, weekends, a maintenance window — so the longest is a
safe anchor that cannot run away. A fulfilment lag has no such bound. One order that took
eight months would set the bar at eight months and silence the class forever, and the tenant
would never learn why nothing was ever reported. The median cannot be captured by a single
case, which is exactly the property needed here and not there.

The tests hold that line directly: one order that took a year leaves the threshold where it
was, and shifting the whole business does move it.

## The demo month cannot exercise either class

Measured on `run_normal_month`: the queue is unchanged at `shipped_not_billed` twice and
`unexplained_movement` once, and **both norms come back as `None`** — the month has fewer than
five finished promises and fewer than five invoiced receipts, so no expectation is claimed and
neither class can fire in either direction.

That is the correct behaviour and a weak test of it. Unlike the wrong claim Spec 078 first
made about the demo, this one is measured on the scenario the demo actually runs, and it is
reported as what it is: the pinned demo queue is unchanged, and it proves nothing about volume.

## What the stories taught

**The blind spot was bigger than the class.** Every delivery class Reality had was anchored to
`due_at`. A consumer order — the most common order there is — carries no date, so a reserved,
unpicked, months-old webshop order was reportable by nothing at any age. That was not a missing
class so much as a missing question: everything asked "did it miss its date", and nothing asked
"is this unusual here".

**Returning nothing is not the same as returning a large number.** The threshold helper gives
back `None` below the minimum history rather than something lenient. A tenant without history
is not a tenant with a generous bar, it is one the rule cannot speak about, and collapsing the
two would have hidden a young tenant behind an arithmetic.

**Disjointness by construction beats disjointness by rule.** `order_stalled` takes only undated
promises, so it cannot overlap the overdue class. The alternative — report both and have one
supersede the other — is what Spec 068 had to build for the at-risk and overdue pair, and it
needs a precedence rule that stays true. Not being able to overlap is cheaper than agreeing not
to.

**Eight constants, none of them measured.** The multiple of three and both floors are
judgements made without a real tenant to check them against. They are recorded beside the code
with their reasoning, which is honest, and they remain the weakest part of this feature. The
first business that uses it will be a better source than any of the arguments here.
