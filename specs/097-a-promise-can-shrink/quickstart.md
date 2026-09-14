# Quickstart: Eighty of the Hundred

**Language**: English

Ten tests in `tests/test_commitment_revisions.py` and two in the derivation suite.

## Story one — the supplier confirms eighty

A promise for a hundred. One statement says *"eighty pieces, two weeks later"* and both figures
are in force from one record: what is open becomes eighty, the date becomes the stated one, and
the promise still carries the hundred and the day it was made with.

An overdue promise for a hundred with eighty received reports twenty missing. Revised to eighty,
the entry goes — not because time passed, but because the promise did. Revised to ninety instead,
it reports ten and says `committed_quantity` is ninety.

**Result**: passes.

## Story two — a promise that shrinks to what arrived is finished

Ninety received against a hundred, revised to ninety: the promise is fulfilled **at that moment**,
without waiting for another movement, because there may not be one.

Revised to eighty with ninety already received: accepted. The supplier said eighty and ninety
came, both are true, the ninety is untouched, and nothing is open.

**Result**: passes.

## Story three — nothing is lost, and nothing empty is accepted

Three statements, all kept in the order they were made. A statement restating neither figure is
refused; so are zero and a negative quantity, and a promise that is closed.

**Result**: passes.

## Writing the second rule exposed a bug in the first

`commitment_quantity` returns the latest revision **that stated a quantity** — not simply the
latest revision, because a later statement about the date alone leaves an earlier quantity
standing.

`commitment_due_at`, written in Spec 093, did **not** have that shape. It took the last revision
unconditionally and returned its `due_at`. Once a statement could carry a quantity and no date,
that returned `None` — and every class that judges a promise by its date went silent.

The derivation test caught it before the feature shipped: an overdue promise with a quantity-only
revision produced **no entries at all**. The fix is one loop, the date rule now matches the
quantity rule, and a regression assertion holds both directions.

Worth naming because it is the ordinary shape of this kind of bug: a rule that was correct while
one field existed, and quietly wrong the moment a second one did.

## What this deliberately does not do

Stock reserved for the original hundred stays reserved when the promise shrinks to eighty.
Nothing releases it and no class reports it. Releasing somebody's stock as a side effect of
recording a sentence would be the product deciding something nobody asked it to — so it is a
stated limit rather than a quiet behaviour.

## What the story taught

**Reversing an earlier non-goal is worth doing openly.** Spec 093 wrote *"a different quantity is
a different promise"* and it was right for a specification about dates. It kept that one honest
and shippable. Saying why it is wrong as a permanent answer is more useful than pretending the
scope was always this.

**The rename landed alone.** `revise_commitment_due_date` would have been a lie the moment it
revised a quantity. Renaming it first, with the whole suite proving the operation still worked,
kept the two changes separable — and it turned up that the docs still used the old name, which a
code-only rename would have left behind.

**Four derived figures now have to stay single-sourced** — unit comparability, the learned
thresholds, the date in force and now the quantity in force. Each was written as one rule with a
test asserting nothing else computes it, and this time the pattern paid for itself immediately by
making the 093 bug a one-line fix rather than a hunt.
