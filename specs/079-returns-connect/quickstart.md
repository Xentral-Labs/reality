# Quickstart: A Return May Say What It Reverses

**Language**: English

Four independent acceptance stories, run against PostgreSQL as part of
`tests/test_returns.py` and `tests/operational_exceptions/test_derivation.py`.

## Story 1 — Record a return against what it reverses

Ship ten against a customer delivery, then record a return of four against the same
commitment. It is accepted, and the queue no longer reports an unexplained movement. A return
against a supplier delivery is refused. A return larger than what went out is refused; a
return of exactly what went out is accepted. The commitment's fulfilled and open quantities
are unchanged, and no delivery class appears.

**Result**: passes. Voiding the return through the existing movement correction makes it stop
counting, with no new correction path.

## Story 2 — Stop billing goods that came back

An order line shipped in full and unbilled reports ten unbilled. Four come back and it reports
six. The remaining six come back and the entry disappears entirely.

**Result**: passes. This is a correction to a class that shipped in #115, not new behaviour.

## Story 3 — Goods back with no credit

Ship ten, bill ten, take six back: one entry with six returned, none credited, six
outstanding. Credit four and it reports two; credit the last two and it clears. Two credit
notes crediting the same line both count.

Take goods back that were never billed and nothing is reported at all — the company never
charged for them. Bill the line and the same return is owed a credit immediately.

**Result**: passes.

## Story 4 — Money back without goods back

Credit six against a line where nothing has come back and nothing is reported: telling a
customer to keep an item is a decision. Two units then arrive and one entry appears with six
credited, two returned, four outstanding. The remaining four arrive and it clears.

**Result**: passes. No order line is ever in both return classes at once.

## The demo month is left as it is

Its return on day 18 names no commitment, so it is still reported as an unexplained movement
and `test_the_month_ends_with_exactly_these_exceptions` is unchanged.

That is deliberate. Before this feature a return *could not* name what it reverses, so the
demo's orphaned return demonstrated a gap in the model. After it, the same record demonstrates
something more useful: somebody recorded goods coming back without saying what they came back
from, and Reality says so. Updating the demo to use the new link would trade one true story
for another and is a decision about the demo, not about this feature.

## What the stories taught

**The model refused the connection, and everything downstream inherited the refusal.** The
missing piece was not a table or a column. `record_movement` accepted a return, accepted a
commitment, and refused both together — one line of a guard — and from that followed two wrong
signals per return, a class that over-reported, and a whole business process that could not be
answered. The same shape as Spec 074's findings, in reverse: there the write path prevented a
condition from existing, here it prevented one from being recorded.

**Not netting was the decision that mattered.** Subtracting returns from fulfilment is the
obvious change and would have been wrong: a kept promise would reopen as overdue and a fully
returned order would look undelivered. Two figures answer two questions — did the company keep
its word, and how much did the customer keep — and only the second moves when goods come back.
That reason now sits next to `fulfilled_quantity`, because a reader who finds a returned order
still counting as delivered will otherwise read it as a bug.

**Two helpers counting one thing had already drifted.** The service layer excluded movements a
correction had voided; the exception queue did not. A shipment recorded in error and voided was
still reported as delivered and unbilled — a live defect nobody had noticed, found only because
returns forced a look at both. They now share one correction-aware helper, which is what the
requirement to reuse the existing path meant all along.

**A credit note is a quantity document here.** The money already had a path:
`post_sales_credit` reduces a receivable and is untouched. What was missing was how much of
which line came back, which is a quantity question — and answering it needed no ledger work at
all.
