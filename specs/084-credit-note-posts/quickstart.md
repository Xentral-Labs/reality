# Quickstart: A Credit Note Gives the Money Back

**Language**: English

Four independent acceptance stories, run against PostgreSQL as part of
`tests/test_credit_notes.py` and `tests/operational_exceptions/test_derivation.py`.

## Story 1 — Owe the money

Record a credit note for 30 and post it. The ledger carries the exact reverse of a sales
invoice: revenue debited, receivable credited. Post it against a customer whose invoice is
**already paid in full** and it is accepted — the receivable goes negative, which is the
statement that the company owes them. That is the ordinary consumer return, and it could not
be expressed at all before.

A sales invoice is refused, a second posting is refused, a zero total is refused. A credit
note whose lines say 30 and whose header says 25 posts 25, because the header is what somebody
stated.

**Result**: passes.

## Story 2 — Settle it, one way or the other

Net a posted credit against an invoice the customer still owes and the invoice falls exactly as
a payment makes it fall. Or refund it: cash leaves and the credit is settled. Settling more
than the credit note still owes is refused in both directions.

**Result**: passes.

## Story 3 — See the credit nobody booked

Give a company six credit notes it booked within two days, then record one and leave it. One
entry with its total, its age and the norm. Post it and the entry is gone. A company with four
booked credit notes is not judged at all.

**Result**: passes.

## Story 4 — See the money still owed

Post a credit note for 60 and settle nothing: one entry saying 60 is owed. Net 20 against an
open invoice and it reports 40. Refund the rest and it clears.

**Result**: passes.

## The demo month

Unchanged: `shipped_not_billed` twice and `unexplained_movement` once. The demo now records,
posts and nets a real credit note where it previously called an operation nobody could reach,
so it exercises the whole credit path correctly and neither new class fires. The pinned queue
needed no change.

## What the stories taught

**The question was better than the answer I first gave.** Asked whether returns were finished,
the honest check found a hole in the middle rather than a missing feature at the edge: a class
said "credited" and meant "noted as credited", because the credit note recorded a quantity and
never touched the money. Four specifications had shipped without anybody asking whether the
chain joined up.

**The first design would have shipped something that fails the common case.** The obvious shape
— a credit reduces an open receivable — is what the old operation did, and it cannot credit an
invoice the customer has already paid. In consumer trade that is *most* returns. The finding
came out of writing the edge cases down, not out of building; the case "an invoice fully
settled by payments, then credited" had no requirement resolving it, and following that thread
changed the feature.

**Widening one concept did the work.** `_invoice_control_entry` refused anything that was not an
invoice, and everything downstream inherited that refusal. Teaching it that a settleable
document is not always an invoice made the credit note, the refund, the netting and both new
classes fall out. The four-row table it became is now the single place where a wrong side would
be wrong — which is why the final review reads it specifically.

**One allocation rule was subtly narrow.** `open_invoice_amount` subtracted only allocations
where the document is the settled side, which is complete for an invoice and wrong for a credit
note: a credit settles an invoice on one side and is settled by a refund on the other. Counting
both sides is correct in general and was invisible until a document could be both.
