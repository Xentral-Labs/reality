# Quickstart: Invoice Lines Know What They Bill

**Language**: English

Three independent acceptance stories, each run against PostgreSQL as part of
`tests/operational_exceptions/test_derivation.py`.

## Story 1 — Shipped and never billed

Record a sales order for ten pieces, ship six against its commitment, and read the queue.
One entry appears on the order line: six delivered, none billed, six outstanding. Bill four
on an invoice line that names the order line and the entry reports two. Bill the remaining
two on a second invoice and the entry is gone on the next read, with nothing acknowledged
and nothing stored.

**Result**: passes. Ship first, and the entry follows the goods rather than the paperwork.

## Story 2 — Billed and never received

Record a purchase order, bill six of it on a supplier invoice line naming the order line,
and read the queue before anything arrives. One entry: six billed, none received, six
outstanding. Record the receipt of six against the commitment and the entry clears.

Record the same purchase order and receive all ten without any invoice, and nothing is
reported at all — a supplier invoice still in the post is the usual sequence, not a finding.

**Result**: passes, in both directions.

## Story 3 — A price that was not the one agreed

Bill an order line agreed at 9.00 at a unit price of 11.00. One entry on the invoice line
names both figures and the difference of 2.00. Bill at exactly 9.00 and nothing appears.
Bill freight on a line that names no order line and nothing appears, because nothing was
agreed for it to differ from.

**Result**: passes.

## The demo measurement — corrected on 2026-09-05

**This section originally recorded a wrong measurement and a wrong conclusion drawn from
it.** It reported that the demo stays quiet and that the demo records no shipments, so the
three classes could not be exercised there. Both statements came from measuring
`ensure_demo`, a small seed that creates one order, instead of `run_normal_month`, the
scenario the demo actually runs.

The real measurement: a full ERP month ends with `shipped_not_billed` twice and
`unexplained_movement` once. Both Shopify orders ship in full against their commitments and
the month's only sales invoice is a header with no lines, so no invoice line bills either
order line — the class fires, correctly, on the demo's own story.

The assumption that a missing reference means "not billed" is therefore exercised by the
demo after all, and it holds. What was genuinely missing was a gate: nothing asserted what
the demo's queue contains, which is why a wrong claim about it survived a review. Spec 078
adds `test_the_month_ends_with_exactly_these_exceptions` to close that.

## What the stories taught

**The edge is what was missing, not the numbers.** Reality already held every figure these
three classes report — the quantity promised, the quantity moved, the price agreed, the
price billed. None of the three could be derived, and no amount of cleverness over Parties,
Items and dates would have fixed that: the missing thing was a single reference saying which
agreed line a billed line settles.

**Absence only means something under a contract.** `shipped_not_billed` concludes from a
missing reference, which is sound only while every order-billing line sets one. That is a
property of the write paths, not of the derivation, and it is the one assumption in this
feature that a later feature could quietly break.

**Starting the walk at the Commitment did the exclusion for free.** The first sketch walked
order lines and then asked whether each had promised a delivery. Starting from the promise
instead makes a freight or service line unreachable rather than filtered, which is both
smaller and harder to get wrong later.

**Two of the four cells are not conditions.** Shipped-not-billed and billed-not-received
are the same comparison on opposite sides of the business. The other two — an invoice ahead
of the goods on the sales side, goods ahead of the invoice on the purchase side — are
ordinary trade, and reporting them would have produced a queue nobody reads.

**A skipped comparison is invisible.** A pair recorded in different units is left alone
rather than converted, which is the safer failure and still a failure: an operator cannot
tell a line nobody needs to look at from one the rule declined to judge. That is recorded
as a review risk rather than solved, because solving it means unit conversion, which is a
feature of its own.
