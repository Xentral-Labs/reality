# Quickstart: Goods Going Back the Other Way

**Language**: English

Four acceptance stories, run against PostgreSQL as part of `tests/test_returns.py` and
`tests/operational_exceptions/test_derivation.py`.

## Story one — send the faulty ones back

Receive a hundred against a purchase order and send ten back. Stock falls to ninety. The
supplier's promise is still fulfilled, because it was kept when the goods arrived — the same
answer the selling side gives for the same reason.

Refused: against a customer delivery, against a commitment for another item, and with no location
to take the goods from. Each with a positive control on the next line.

**Result**: passes.

## Story two — send a customer's return on to the supplier

A customer sends a faulty item back. A supplier return takes those goods out of the location they
came back to, naming the customer return, and the customer's return is settled.

Spec 082 had already written this down — its own description listed "a shipment to the supplier"
among the things that settle a return. The movement simply did not exist. Nothing new was needed:
the same rules apply, so the goods must leave the location the return came back to, and nothing
may settle more than came back.

**Result**: passes.

## Story three — see what the supplier owes for it

`supplier_return_not_credited` reports goods that went back and were never credited. It says
nothing while no supplier invoice has billed them: the company was never charged, so nothing is
owed back. Once the invoice arrives, four back and nothing credited reports four; a credit for
three reports one; a credit for four clears it.

`supplier_credit_not_returned` reports a supplier crediting more than went back — and stays
silent while nothing has gone back at all. That silence is the whole design: a rebate, an
allowance or a price correction is an ordinary supplier credit with no goods behind it, and
reporting one would flag every quarter-end agreement a company makes.

One order line never produces both.

**Result**: passes.

## Story four — stop accruing for goods that went back

`receipt_unbilled` counted everything that once arrived. Now it counts what the company still
holds: ten received with four back accrues for six, and a receipt entirely sent back accrues for
nothing.

`billed_not_received` was deliberately left alone, and this is the part worth arguing about. The
goods arrived. Netting returns off there would report a supplier as having failed to deliver
something it delivered — a false accusation about the delivery instead of a true statement about
the money. What the supplier owes for returned goods is the credit class's business.

The two look inconsistent until you write down the question each one asks. Both are requirements
rather than implementation details for exactly that reason.

**Result**: passes.

## The bound is what moved, not what is open

A supplier delivery is usually received in full, so its open quantity is zero exactly when a
company most wants to send something back. The bound is therefore what actually arrived less what
has already gone back — the identical reasoning the customer side uses, now written on both
sides.

The test proves it the awkward way: it asserts the open quantity is zero and then returns
anyway.

## The demo month

Unchanged. It records no supplier return, so neither class can fire and `receipt_unbilled` sees
the same figures it always did.

## What the story taught

**The best part of the design was already written down.** Spec 082 named "a shipment to the
supplier" as a resolution and could not record one. Closing that needed one movement kind and no
new concept — no reference, no schema, no rule. Reading what the product already says about
itself is cheaper than designing.

**Two neighbouring classes can disagree correctly.** `receipt_unbilled` must net returns off and
`billed_not_received` must not. That looks like an inconsistency and is not: one asks what the
company still holds, the other asks whether the supplier delivered. Writing both questions down
turned an argument into two requirements.

**A test helper collided with an existing one, again.** Appending a `send_back` helper to a
four-thousand-line test file silently shadowed the customer-return helper of the same name and
broke thirteen shipped tests at once. Nothing was wrong with the feature; the fix was a rename.
The lesson is not "be careful" — it is that a name check belongs in the append, and that a suite
run before the classes are written is what turns this into a two-minute fix instead of a
debugging session.

**The taxonomy table had `return_unresolved` twice.** A duplicate row that predates this feature,
found while inserting two new rows in class order. Collapsed here rather than left for somebody
else to notice.
