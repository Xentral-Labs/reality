# Quickstart: Close What Is Never Coming

**Language**: English

Two independent acceptance stories, run against PostgreSQL as part of
`tests/test_stale_promises.py`.

## Story 1 — See what would close

Record three promises due before a date and one due after it, reserve stock against one of
them, and preview a closure. Three match, the reserved quantity is stated, and the sample is
bounded and drawn only from the matching set. Criteria matching nothing report zero rather than
failing. The preview changes no status, no reservation and emits no event, which is asserted
rather than assumed.

Nothing matches that has movement against it — and voiding that movement through the existing
correction makes the promise match again, because then nothing ever moved. Nothing matches that
is already cancelled, has no due date, is under a hold, or belongs to a party under a delivery
hold.

**Result**: passes.

## Story 2 — Close them in one act

Confirm the count with a reason and the promises close together: cancelled, reservations
released, and the overdue class silent for them. No Document and no Movement changed.

Confirm a count that no longer matches and it is refused with nothing closed. Confirm without a
reason and it is refused. Run the same closure twice and the second succeeds having closed
nothing, because a repeat should be safe rather than an error. Another tenant's promises
matching the same criteria stay open.

The act leaves one event carrying the criteria, the reason, the number and the identities.

**Result**: passes.

## What the stories taught

**The dangerous part was not the deletion.** It was deciding what to delete. Every safety in
this feature exists because Reality must not decide that an unshipped order is abandoned rather
than late: the criteria are stated by a person, the count is confirmed by a person, the reason
is written by a person. Reality's only contributions are showing what matches and refusing to
act on a stale number.

**Reusing the single cancellation forced a small change and prevented a large one.**
`cancel_commitment` committed internally, so calling it in a loop would have left a half-closed
wall on any failure. It gained the deferral flag the rest of the module already uses. Writing
status directly instead would have been easier and would have created a second definition of
what cancelling means, which drifts within a release.

**"Nothing moved" is the whole safety rule, and it is not airtight.** A company that records
movements outside Reality — the exact company most likely to arrive with an imported history —
has promises that look untouched and are not. The preview and the sample exist for that reason
and nothing else.

**One deliberate foot-gun remains.** A due date in the future is allowed, so "due before
tomorrow" would sweep today's orders. Refusing it would be Reality deciding what a person may
mean, which this feature declines to do everywhere else. The count is what stands between an
operator and that mistake.
