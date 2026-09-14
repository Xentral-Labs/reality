# Quickstart: A Fee Is a Charge, Not a Smaller Credit

**Language**: English

One test, in `tests/operational_exceptions/test_derivation.py`, carrying both recordings.

## The measurement that produced the specification

Run before anything was written, because the item was on the list as a suspected false positive:

| How the fee is recorded | `returned_not_credited` |
|---|---|
| Credit note line for **8** naming the order line | `uncredited_quantity 2.0000`, for ever |
| Credit note line for **10** naming the order line, plus a **charge line** for the fee | no entry, credit note total `72.00` |

So the model already expresses a restocking fee, and the entry appears only when a company
records it as a smaller credit — which is a true statement about its own document.

**Nothing was built.** No derivation, no service, no schema.

## Both recordings, pinned in one test

Ten shipped, ten invoiced, ten back. Credit ten and charge for the fee: the class clears and the
customer receives 72. On a second order line, credit eight: two are reported as uncredited.

They live in one test so neither can be changed without the other being read.

**The second assertion is the one that matters.** It is correct, and it looks exactly like a bug
report titled *"false entry on restocking fees"*. Somebody acting on that report would remove it.
This is what stops them.

## The guidance

`returned_not_credited` now says how a fee, a damage deduction or a write-off is recorded — one
shape, credit the goods and charge for what is kept — and what recording a smaller credit
quantity means instead. A test reads the guidance rather than checking it exists, the same shape
as Spec 088's asymmetry test.

## What the story taught

**Measuring first turned a feature into a paragraph.** The item was described as a false
positive of the same kind Spec 088 removed from `overdue_receivable`. It is not: 088 had a real
defect where a customer doing the agreed thing looked like a debtor. Here the customer's document
says eight were credited, and the queue agrees with the document.

**The remedy for a recording trap is guidance, and saying so is not a cop-out.** Reality cannot
know that a credit note for eight was meant as ten credited and two charged. A rule that guessed
would be inventing intent — which is the one thing this product refuses everywhere else.

**A test can exist to stop a fix.** That is an unusual reason to write one and it is the strongest
one here: the behaviour most at risk is the behaviour that is right.
