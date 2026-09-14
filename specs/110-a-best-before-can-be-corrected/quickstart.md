# Quickstart: A Best-Before Can Be Corrected

**Language**: English

Six tests in `tests/test_inventory_tracking_reservations.py` and one in the derivation suite. No
migration, no new record type.

## Story one — the misread label

Somebody read the fifteenth; the goods say the sixteenth. `correct_lot_expiry` takes the new date,
**the date the caller believes is stored**, and **a reason**. The lot carries the new date, and one
`lot.expiry_corrected` event carries the before, the after and the reason.

Every refusal is exercised with a positive control in the same test: an empty reason, a
confirmation that does not match what is stored, a confirmation claiming none is stated when one
is, a correction that would change nothing, and an unreadable date **in either position**. None of
them changes anything, and the same lot then corrects cleanly.

**Result**: passes.

## Story two — the wrong label entirely

A date read off a neighbouring pallet, on an item with no shelf life, is corrected to **nothing**
with a reason. The lot then has no best-before and asserts nothing about expiry.

Correcting a date back in has to name that none is stated — claiming the old date is refused. Then
it records.

**Result**: passes.

## Story three — the queue follows

Two lots, both wrong in opposite directions: one read a day early, reporting good stock as expired;
one read late, hiding expired stock. Correcting the first forward removes its entry; correcting the
second back makes it appear, with the corrected date and the days since it passed. Derived per
read, so nothing is stored and there is no manual step.

And the refusal that sent everybody here now says where to go: stating a different date names the
correction, in words.

**Result**: passes.

## What the story taught

**Settling what kind of change this is decided the whole shape.** Spec 093 built an append-only
record and said in its own docstring that it was *not* a correction — *"a correction says the
record was wrong; this says the record was right and the world moved."* A counterparty moving a
delivery date is the world moving. A best-before is printed on a box: it does not move, so a second
date means the first reading was wrong, and keeping both as equally valid statements would record a
contradiction as though it were history. Once that was settled, the shape was the one the product
already had for corrections — correct in place, audit in the event — and **no table was needed**.

**A correction costs a confirmation, not just a reason.** The caller names the date they believe is
stored. That is not novelty: three operations here already make a caller say what they are acting
on (the confirmed count of Spec 085, the confirmed total of Spec 098, the expected revision of a
document correction), for the same reason each time. It also makes the intent legible — *"I saw the
fifteenth, it is the sixteenth"* — which a reason alone does not convey.

**The sibling operation answers the source-record question the other way, and imitating it would
have been wrong.** `correct_manual_document_lines` refuses to correct a document that came from a
source record. Applying that here looked consistent until it was measured: **no import path
creates lots at all** — `create_lot` is reached only from the agent tool, the API and the command
line. So a lot's source record says where the *batch* came from, never where the *date* came from,
and refusing on it would have blocked a correction to a hand-typed date because the goods arrived
by import.

**A refusal without a way forward is a bug of its own.** Spec 109's refusal was right and left a
typo stuck for a whole specification. One sentence in the message fixes that, and there is a test
asserting the words are there.

## What this deliberately does not do

**Correcting to nothing is lossy in the record.** Afterwards a lot looks exactly like one nobody
ever dated; only the event history says otherwise. The alternative is a second column saying why
the field is empty, which is more schema than a misread label deserves.

**The confirmation confirms a value, not a revision number.** Two corrections in the same instant
could both pass their check and the second would win. A counter would close that; a lot's
best-before is not a field two people race on, and adding one would be schema for a hypothetical.

**Reality judges neither reading.** Nothing stops a second correction back again, and nothing
should — the product is not the arbiter of what is printed on a box. Which also means an entry can
be made to go away by hand; that is true of every corrected value here, the reason is recorded, and
the alternative is the uncorrectable field this specification exists to remove.

**A lot's number stays as it is.** Movements and reservations were recorded against it; changing it
would change which goods they concerned.
