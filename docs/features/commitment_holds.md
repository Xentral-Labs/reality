# Feature: Commitment execution holds

## Goal

Temporarily block execution without cancelling promises or turning Documents into
operational state.

## Model

CommitmentHold links only to Commitment and records `reason_code`, optional note,
creator, creation time, and release time. It is active while `released_at` is
empty. Holds are retained after release for auditability.

Allowed reasons are `credit_check`, `customer_request`,
`address_clarification`, `compliance`, `manual_review`, and `other`.

## Behavior

- An active hold blocks reservation and physical Movement for the Commitment.
- It does not change Commitment status, delete reservations, or modify Documents.
- Holding a Document is a convenience operation that holds each open Commitment
  linked to that Document.
- Releasing Document holds releases active holds on its linked Commitments.
- All lookups and mutations are tenant-scoped.
- Web mutations require confirmation; CLI and API call the same services.

## A Hold Nobody Lifted

`commitment_hold_unreleased` reports a hold standing longer than this company's own rhythm for
lifting promise holds — the middle of the most recent twenty lifted ones, three times over, never
sooner than a week, and silent below five. It matters because `close_stale_promises` skips held
promises on purpose and that protection has no expiry, so a forgotten hold shields its promise from
the only sweep that could close it. The entry names the reason, the note, who raised it and the
quantity still open on the promise. A hold on a promise that is no longer open is not reported,
because it holds nothing back. See [operational exceptions](./operational_exceptions.md).

## A Hold Never Outlives Its Promise

Cancelling a promise releases its holds, the way it has always released its reservations. Both hold
something for a promise, and letting one go while keeping the other was inconsistent on its face.

The concrete harm was a **refused return**. `require_not_held` refuses every movement naming a held
commitment, so a promise partly shipped, held for a credit check and then cancelled went on
refusing the goods coming back — with an error message about the credit check.

**This is not automatic release because time passed**, which spec 107 refused and still refuses: a
hold is a person's statement and the clock does not answer it. This releases a hold because its
*subject* is gone. The test that separates the two is worth keeping: **is anything still being
blocked?** Time passing does not change the answer; a promise closing does.

Nothing anybody said is erased. A release sets one timestamp; the reason code, the note, who raised
it and when all stay, which is what makes doing it automatically safe.

A promise settled as fulfilled by a **revision** releases its holds too, and that is the only other
path. A held promise cannot be shipped, so it cannot become fulfilled by shipping — but spec 093
deliberately allows a held promise to be revised, and spec 097 settles one as fulfilled the moment
a stated quantity falls to what has already moved. So a counterparty saying *"only send what you
already sent"* finishes a held promise, and without the release every return against it would then
be refused for a reason that has nothing to do with returns. Both of the other legs — you cannot
hold a closed promise, you cannot ship a held one — are pinned by tests rather than trusted.

The invariant, stated once: **a promise that is not open never carries an active hold.** It is
proven per path rather than enforced by a constraint, because the condition spans two tables and a
status; a future operation that closes a promise a third way has to add a leg to the invariant test.

**What this does not do:** holds already sitting on promises closed before this shipped stay where
they are. No migration should edit a tenant's operational records to tidy them, and no rule can
tell a hold left deliberately from one forgotten. `release_commitment_hold` reaches them from CLI,
Web, API, MCP and Chat. Party holds are unaffected — they are not tied to a promise, and spec 107
reports a forgotten one.

