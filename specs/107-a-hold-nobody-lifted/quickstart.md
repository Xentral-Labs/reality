# Quickstart: The Hold Nobody Lifted

**Language**: English

Seven tests in the derivation suite. No migration, no new operation.

## Story one — the credit check nobody finished

A promise held for a credit check sixty days ago, with five lifted holds behind it so the rule has
a rhythm. The queue reports it: the reason code, the note, who raised it, how long it has stood,
and **ten pieces still open on the promise it holds** — because a hold on nothing is a formality
somebody forgot and a hold on a real backlog is money standing still.

Whatever the queue said about that promise before it was held, it still says. A hold suppresses
nothing; it means somebody is dealing with it, not that it is fine. Lifting it ends the entry with
nothing stored.

A hold on a cancelled promise is not reported — it holds nothing back, so nobody could clear it by
doing anything useful. The test cancels the promise, asserts the hold is *still unreleased*, and
asserts the queue stays quiet.

**Result**: passes.

## Story two — the customer nobody can ship to

A delivery hold on a customer with two open orders, standing forty-five days. Reported as **high**,
naming the hold type, the reason and **two blocked deliveries** — a count, never a summed quantity,
because quantities across different items do not add up. The test then tries to ship against one of
those orders and watches it refused, which is what the count is about.

A hold blocking nothing is still reported, because it will refuse the next order too. Both are
read in one pass and their counts asserted together: `{blocking-two: 2, blocking-nothing: 0}`.

**Result**: passes.

## Story three — the rule, and whose history it reads

Four lifted holds is not a lenient threshold, it is a rule that cannot speak: a hold standing three
hundred days reports nothing. One more lifted hold and the same hold is judged — so the silence was
the minimum speaking and not the class being absent. A hold three days old says nothing, because
the floor is a week.

Two populations, never one: five lifted promise holds teach the promise rule and say nothing about
the party rule. Another company's history is its own. **Share the rule, never the history.**

**Result**: passes.

## What the story taught

**The check came before the design.** Spec 091 found five shipped classes whose clearing path
nothing reached, so the first thing done here was confirming a person can actually lift these holds
— `release_commitment_hold` and `release_party_delivery_hold` are declared on CLI, Web, API, MCP
and Chat. A class whose fix nothing reaches is worse than no class.

**The gap was found by asking what the queue reads, not what it reports.**
`exceptions.py` touched `CommitmentHold` and `PartyHold` **zero times**. That is a cheap question
with a blunt answer, and it is a different question from the two surveys that came before it.

**A forgotten hold is permanent, not untidy.** That is the whole argument for the feature.
`close_stale_promises` skips held promises on purpose and the protection never expires, so the one
operation that could close an abandoned promise is silently disabled for it, for ever.

**One class immediately failed the gate shipped a day earlier.** #142's reference-integrity gate
caught the new derivation reading `Commitment.document_line_id` — for the unit, in the entry —
before the declaration said so. Declared `traces_only` for both classes, since neither concludes
from it. A gate earning its keep on the next feature is the best evidence it was worth building.

**An assumption in a test was wrong and the test said so.** The first draft asserted the held
promise was still reported as `order_stalled`; it was `outgoing_commitment_at_risk`, because its
requested delivery is in the future. The fix is better than the guess: capture what the queue said
before the hold and assert it still says it, without naming a class.

## What this deliberately does not do

**Nothing is released automatically.** A hold is a person's statement that they are dealing with
something. Lifting it because time passed would remove the protection that makes holds worth
having, and it would be Reality deciding something nobody asked it to.

**Holds on cancelled promises stay where they are.** Cancelling a promise does not release its
holds. Reporting them would be a wall nobody can clear; releasing them on cancel is a behaviour
change to a shipped operation and belongs in its own specification.

**The threshold is a fifth unmeasured constant.** The Spec 080 helper now serves eight classes and
none of its numbers has been checked against a real business. This adds to that risk rather than
reducing it. A learned rhythm is still better evidence than a configured number, and the
alternative here was no visibility at all.
