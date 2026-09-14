# Feature Specification: A Closed Promise Holds Nothing

**Feature Branch**: `108-a-closed-promise-holds-nothing`
**Created**: 2026-09-08
**Status**: Draft
**Language**: English
**Input**: "Cancelling a promise does not release its holds. Spec 107 found it and deliberately left it: such holds are not reported and not cleaned up, so a tenant accumulates them quietly."

## Context and Intent

### Problem

`cancel_commitment` releases the promise's **reservations** — stock held for something that is no
longer going to happen has to go back. It leaves the promise's **holds** exactly where they are.

That is inconsistent on its face: a reservation and a hold are the same shape of thing, both
holding something for a promise, and one is let go while the other is not. It also has three
concrete costs.

**A hold that blocks nothing still blocks something.** `require_not_held` refuses every movement
naming a held commitment and every reservation against it. A cancelled delivery can still have
goods come back against it — a partial shipment, then the rest cancelled — and that return is now
refused with a message about a credit check somebody finished months ago.

**The record asserts something untrue.** An unreleased hold says *somebody is dealing with this
promise*. Nobody is; the promise is off. The hold register shows it as active for ever.

**Nothing reports it, by design.** Spec 107 skips holds on promises that are not open, on the
ground that they hold nothing back. That reasoning was half right — see below — and it means the
accumulation is silent.

### The sequence that makes a fulfilled promise carry a hold

Worth writing down, because it is the only one and it is not obvious.

`hold_commitment` refuses a promise that is not open, and `require_not_held` refuses every movement
naming a held one — so a held promise cannot be shipped, and therefore cannot become fulfilled by
shipping. But Spec 093 decided deliberately that **a held promise may still be revised**, and Spec
097 settles a promise as fulfilled the moment a stated quantity falls to what has already moved.

So: hold a promise for a credit check, the counterparty says *"only send what you already sent"*,
and the promise is fulfilled while still held. From then on every return against it is refused for
a reason that has nothing to do with returns.

### Scope

- Cancelling a promise releases its holds, the way it already releases its reservations.
- A promise settled as fulfilled by a revision releases its holds too, for the same reason.
- One invariant, stated once and proven from every direction: **a promise that is not open never
  carries an active hold.**

### Non-Goals

- **Erasing what somebody said.** Releasing a hold sets `released_at`. The reason code, the note,
  who raised it and when all stay exactly as recorded, which is what makes this safe to do
  automatically at all.
- **Releasing party holds.** A party hold is not tied to a promise, so nothing about a promise
  closing says anything about it. Spec 107 reports a forgotten one.
- **Cleaning up holds left on promises closed before this ships.** They are data, not schema, and
  no migration should touch a tenant's operational records to tidy them. `release_commitment_hold`
  reaches them from every surface, and this specification says so rather than pretending they are
  gone.
- **Letting a hold survive a cancellation on purpose.** A hold whose subject is gone is not a
  weaker hold, it is a statement about nothing. If somebody wants to stop dealing with a
  counterparty's goods, that is a party hold, and it exists.
- **Changing what a hold blocks.** `require_not_held` is untouched. This changes when a hold ends,
  not what it does while it stands.

### Existing Contracts

- [`specs/107-a-hold-nobody-lifted/spec.md`](../107-a-hold-nobody-lifted/spec.md) — which found
  this and left it
- [`specs/093-promises-can-be-revised/spec.md`](../093-promises-can-be-revised/spec.md) — a held
  promise may still be revised
- [`specs/097-a-promise-can-shrink/spec.md`](../097-a-promise-can-shrink/spec.md) — settling on a
  revision
- [`docs/features/commitment_holds.md`](../../docs/features/commitment_holds.md)
- [Constitution](../../.specify/memory/constitution.md), principles II and V

## Clarifications

### Session 2026-09-08

- Q: Why release rather than report? → A: Because a hold on a closed promise is a statement about
  nothing, and reporting it would be asking a person to tidy up after the product. Spec 107 chose
  to report *unreleased* holds and to skip these; this closes the hole that made skipping
  necessary.
- Q: Is releasing automatically not the thing Spec 107 refused? → A: Spec 107 refused releasing a
  hold **because time passed** — a hold is a person's statement and time does not answer it. This
  releases a hold because its *subject* is gone. Those are different, and the difference is whether
  anything is still being blocked.
- Q: Does anything get lost? → A: No. A release sets one timestamp. The reason, the note, who
  raised it and when are all still there, which is exactly why this can be automatic.
- Q: Is the release inlined or does it call the existing operation? → A: It calls the existing
  operation, which needs one new argument so it can take part in a transaction. One release path,
  one event, one place that knows how to release a hold.
- Q: What about a promise fulfilled by shipping? → A: Unreachable while held, and that is pinned by
  a test rather than assumed. `require_not_held` refuses the shipment.
- Q: What about holds already sitting on closed promises? → A: Left alone and named. A migration
  that edits a tenant's operational records to tidy them is not something this product should do,
  and the release operation reaches them from every surface.
- Q: Does Spec 107's class change? → A: Its behaviour does not. Its skip becomes true by
  construction for anything closed after this ships, and it correctly keeps ignoring older rows.
  The guidance is corrected to say that.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The Cancelled Order (Priority: P1)

An order is held for a credit check and then cancelled. The hold ends with it, and the goods that
already went out can still come back.

**Why this priority**: It is the case that was asked for and the one that blocks a real return.

**Independent Test**: Hold an open promise, cancel it, and read the hold and what can be recorded
against the promise.

**Acceptance Scenarios**:

1. **Given** an open promise with an active hold, **When** it is cancelled, **Then** the hold is
   released, and its reason, note, author and creation instant are unchanged.
2. **Given** the same cancellation, **When** the business events are read, **Then** the release is
   recorded by the operation that releases holds, and the cancellation names the holds it released.
3. **Given** a partly shipped promise that was held and then cancelled, **When** goods come back
   against it, **Then** the return is recorded, where before it was refused.
4. **Given** a promise with no hold, **When** it is cancelled, **Then** nothing about the
   cancellation changes.
5. **Given** two held promises cancelled inside one transaction that is then rolled back,
   **When** the holds are read, **Then** neither release survived, because neither cancellation
   did.
6. **Given** a stale-promise closure, **When** it runs, **Then** it never cancels a held promise at
   all, because it skips them — which is why the transaction is proven directly rather than
   through it.

### User Story 2 - The Promise Revised To Nothing (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a held promise revised down to what has already shipped, **When** the revision is
   recorded, **Then** the promise is fulfilled and its hold is released.
2. **Given** a held promise revised to a quantity above what has shipped, **When** the revision is
   recorded, **Then** the promise stays open and the hold stays active, because there is still a
   delivery to stop.
3. **Given** a held promise, **When** a shipment against it is attempted, **Then** it is refused —
   so being fulfilled by shipping cannot reach a held promise at all.

### User Story 3 - The Invariant (Priority: P1)

**Acceptance Scenarios**:

1. **Given** every way a promise can stop being open, **When** each is exercised, **Then** no
   promise that is not open carries an active hold.
2. **Given** a promise that is not open, **When** somebody tries to hold it, **Then** it is
   refused.

### Edge Cases

- Cancelling a promise that has several holds recorded over time, one active.
- Cancelling a promise whose hold was already released.
- A revision that states only a date on a held promise.
- A hold on a promise closed before this shipped.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Cancelling a promise MUST release every active hold on it, through the existing
  release operation, within the same transaction as the cancellation.
- **FR-002**: Settling a promise as fulfilled while recording a revision MUST release every active
  hold on it, in the same way.
- **FR-003**: A release MUST preserve the hold's reason code, note, author and creation instant,
  and MUST set only when it was released.
- **FR-004**: The cancellation event MUST name the holds it released, and the release itself MUST
  be recorded by the operation that releases holds rather than by a second emitter.
- **FR-005**: A promise with no active hold MUST behave exactly as it does today when cancelled or
  settled.
- **FR-006**: A revision that leaves a promise open MUST leave its hold active.
- **FR-007**: A promise that is not open MUST NOT be holdable, and that MUST be proven rather than
  assumed.
- **FR-008**: A held promise MUST NOT be shippable, and that MUST be proven rather than assumed.
- **FR-009**: After every way a promise can stop being open, no promise that is not open may carry
  an active hold.
- **FR-010**: What a hold blocks while it stands MUST NOT change.
- **FR-011**: Every existing class, operation, register and projection MUST behave exactly as it
  does today, apart from a hold ending sooner.

### Domain and Traceability Requirements

- **DR-001**: No migration, no new operation, no new operational exception class or cause.
- **DR-002**: One release path. The existing operation MUST gain the ability to take part in a
  caller's transaction rather than being reimplemented, and that MUST be proven by a rollback
  rather than through the stale-promise closure, which cannot cancel a held promise.
- **DR-003**: Holds on promises closed before this ships MUST be left untouched, and that MUST be
  stated as a limit rather than backfilled.
- **DR-004**: Spec 107's class MUST keep its behaviour, and its guidance MUST be corrected to say
  its skip is now true by construction going forward. Its test MUST have the inverted assertion
  and MUST keep proving the skip against a reconstructed legacy row, so the skip does not become
  untested code.
- **DR-005**: Every read and write MUST be tenant-scoped.

### Key Entities *(when data is involved)*

- **CommitmentHold**: unchanged. It gains no field; it stops being active sooner.
- **Commitment**: unchanged.

## Success Criteria *(mandatory)*

- **SC-001**: A hold never outlives the promise it was raised against.
- **SC-002**: Goods can come back against a cancelled delivery that was once held.
- **SC-003**: Nothing anybody said is erased.
- **SC-004**: The invariant holds from every direction, and each direction has a test.
- **SC-005**: Nothing else about holds changes.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- Holds already sitting on closed promises stay there. Nothing reports them and nothing tidies
  them; the release operation reaches them from every surface.
- A party hold is unaffected: it is not tied to a promise.
- This changes when a hold ends, never what it blocks while it stands.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1, 5 | cancellation releases the hold test |
| FR-002 | US2 scenario 1 | revision settles and releases test |
| FR-003 | US1 scenario 1 | nothing erased test |
| FR-004 | US1 scenario 2 | event test |
| FR-005 | US1 scenario 4 | unheld cancellation unchanged test |
| FR-006 | US2 scenario 2 | still-open revision test |
| FR-007 | US3 scenario 2 | holding a closed promise refused test |
| FR-008 | US2 scenario 3 | held promise cannot ship test |
| FR-009 | US3 scenario 1 | the invariant test |
| FR-010 | — | `require_not_held` untouched |
| FR-011 | — | the existing suites, unchanged |
| DR-001 | — | no migration, no command added |
| DR-002 | US1 scenarios 5, 6 | rollback test, and the closure skipping held promises |
| DR-003 | Edge cases | the limit stated, no backfill |
| DR-004 | — | the corrected catalog guidance and Spec 107's inverted test with its legacy leg |
| DR-005 | — | the existing isolation suites |
