# Quickstart: A Closed Promise Holds Nothing

**Language**: English

Twelve tests in `tests/test_commitment_holds.py`, seven of them new. No migration, no new
operation.

## Story one — the cancelled order

A promise held for a credit check, then cancelled. The hold is released with it, and **nothing
anybody said is erased**: the reason code, the note, who raised it and the instant it was raised
all survive the release, which is what makes doing this automatically safe.

The concrete harm, in its own test: a promise partly shipped, held, then cancelled. Before this,
`require_not_held` refused the goods coming back — with a message about the credit check. Now the
return records.

A promise with no hold is cancelled exactly as it was. The release is emitted by the operation that
releases holds, and the cancellation event names the holds it released, so a reader of the timeline
sees the two facts together.

**Result**: passes.

## Story two — the promise revised to nothing

A held promise revised down to what already shipped is fulfilled, and its hold goes with it. A
revision that leaves the promise open leaves the hold alone, because there is still a delivery to
stop.

**Result**: passes.

## Story three — the invariant

**A promise that is not open never carries an active hold.** Proven from every direction a promise
can stop being open: cancelled directly, settled by a revision, and shipped to completion after its
hold was lifted. The test then queries every closed promise and every active hold and asserts the
two sets do not intersect, with an open promise's hold as the positive control.

Both legs that make the fulfilled case the *only* interesting one are pinned rather than trusted:
you cannot hold a closed promise, and you cannot ship a held one.

**Result**: passes.

## What the story taught

**This is not the automatic release Spec 107 refused, and the difference is worth a sentence.**
That specification refused lifting a hold *because time passed* — a hold is a person's statement
and the clock does not answer it. This lifts a hold because its *subject is gone*. The test that
separates the two cases: **is anything still being blocked?** Time passing does not change the
answer; a promise closing does.

**A test caught a claim in the plan, not a bug in the code.** The first draft said the
stale-promise closure was where the transaction mattered — forty promises, forty sets of holds.
It cannot be: `_stale_promises` skips a promise with an active hold on purpose, so a closure never
cancels a held one. The first version of that test therefore asserted `active_commitment_hold(...)
is None` on promises that had never been held — passing for the wrong reason, which is exactly the
vacuous-negative trap. Replaced with two honest tests: one rolls a cancellation back and asserts
neither release survived, the other pins that a closure skips a held promise at all. The plan says
what happened.

**Spec 107's own test pinned the bug.** It asserted that a hold survives a cancellation —
documenting the behaviour this specification changes — so it went red on the first full run, which
is exactly what a test written a day earlier should do. Its assertion is inverted, and a second
leg was added: the *legacy* state is reconstructed by hand and the class is asserted still to skip
it, so the skip keeps a test rather than becoming dead code nobody would notice removing.

**The sequence that reaches a held-and-fulfilled promise is not obvious.** A held promise cannot be
shipped, so it cannot become fulfilled that way. But Spec 093 deliberately allows a held promise to
be **revised**, and Spec 097 settles one as fulfilled the moment a stated quantity falls to what
has already moved. So a counterparty saying *"only send what you already sent"* finishes a held
promise — and every return against it would then be refused for a reason that has nothing to do
with returns.

## What this deliberately does not do

**Holds already sitting on promises closed before this shipped stay where they are.** No migration
should edit a tenant's operational records to tidy them, and no rule can tell a hold left
deliberately from one forgotten. `release_commitment_hold` reaches them from every surface. Spec
107's class goes on skipping them, and its guidance now says that is a legacy situation rather than
an ordinary one — because the reason it used to give has stopped being the reason.

**The invariant is proven per path, not enforced by a constraint.** The condition spans two tables
and a status, so a database constraint cannot express it. A future operation that closes a promise
a third way has to add a leg to the invariant test, and this says so.

**Party holds are untouched.** They are not tied to a promise, so nothing about a promise closing
says anything about them. Spec 107 reports a forgotten one.
