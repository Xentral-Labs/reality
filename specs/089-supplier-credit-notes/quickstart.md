# Quickstart: The Credit That Comes the Other Way

**Language**: English

Three acceptance stories, run against PostgreSQL as part of `tests/test_credit_notes.py` and
`tests/operational_exceptions/test_derivation.py`.

## Story one — take the credit off what is owed

Post a supplier invoice for 1,000 and a supplier credit for 150. The credit posts as the exact
reverse of the invoice: `accounts_payable` debit, `inventory` credit, its own gross amount and
nothing else. Netting it against the invoice leaves 850 owed.

Net a 250 credit against a 100 invoice and the invoice is settled while 150 stays claimable.
Then net that 150 against a second invoice and neither document owes anything it did not.

A credit belonging to another supplier is refused. So is a credit that was never booked, because
there is no control entry to settle with. A supplier invoice that was overdue stops being
reported the moment a credit settles the last of it — and nothing downstream had to be told a
credit was involved rather than a payment.

**Result**: passes.

## Story two — get the money back when nothing is open

Pay a supplier invoice in full, then receive a credit for 60. There is nothing to net it
against; the company's money is with the supplier. A refund brings it back: cash debit,
`accounts_payable` credit, and the credit note settled. A refund of 61 is refused, because that
is more than the credit still claims.

**Result**: passes.

## Story three — see the credits nobody has acted on

`supplier_credit_unposted` reports a credit a supplier sent that nobody booked. Booking it clears
the entry with no manual step.

`supplier_credit_unclaimed` reports a booked credit nobody has netted or asked for. Net part of
it and the entry reports only the remainder; have the supplier refund the rest and it goes.

The two sides stay apart. With a history on both sides, a credit the company wrote is reported
by `credit_note_unposted` and never by `supplier_credit_unposted`, and the other way round. That
is asserted rather than assumed.

**Result**: passes.

## Each side learns its own rhythm

This is the part of the design that changed during the work. The first draft of the plan said the
new class should reuse the threshold the selling side already learns. That was wrong.

The existing threshold is learned from credit notes the company wrote itself and booked to
`sales_revenue` — how long accounts receivable takes over its own paperwork. Booking a credit a
supplier sent is a different process with a different owner. Sharing the number would let one
side's rhythm accuse or silence the other, and a company issuing no sales credits at all could
never judge its supplier credits.

So the *rule* is shared and the *history* is not, which is exactly what spec 080 did when it gave
the learned-expectation rule two more users. `test_each_side_learns_its_own_rhythm` proves it: a
prompt history of the company's own credit notes leaves the supplier side claiming no norm and
reporting nothing, and a history of supplier credits makes the same forgotten credit report at
once.

## The demo month

Unchanged, and it proves nothing: the demo records no supplier credit, so neither class can fire
there in either direction.

## What the story taught

**The recorded note overstated the blocker, again.** It said "no `supplier_credit_note` type
exists". `create_document` takes the type as a free string, so such a document could always be
created — what could not happen was posting it, settling it or seeing it. That is the second
feature in a row where a recorded blocker turned out narrower than it sounded, and the habit of
checking before believing has now paid twice.

**Two rows in one table did most of the work.** `SETTLEMENT_CONTROL` records which account
settles a document and which side the entry sits on, and `open_invoice_amount` flips the sign
from that. A supplier credit on the debit side of `accounts_payable` therefore reads as a claim
on the supplier with no special handling anywhere — and the aging register, `overdue_payable` and
`purchase_discount_available` all behaved correctly without being touched.

**It is deliberately half a feature.** A return to a supplier cannot be recorded at all, so a
credit for returned goods is money with no evidence of the goods behind it. For a price
correction, an allowance or a rebate nothing is missing, and those are the common cases. The
missing half is written into the class's own guidance, the procure-to-pay feature document and
the coverage matrix, so the next person to look does not have to rediscover it.

**Mirrors drift, and comments do not prevent that.** The two sides now share one settlement
service, one parameterised learned rule and one body per class pair, and a test asserts that
neither side reads the other's documents. That is what will still be true after the next change
to one side only.
