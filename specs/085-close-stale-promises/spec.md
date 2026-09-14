# Feature Specification: Close What Is Never Coming

**Feature Branch**: `085-close-stale-promises`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "Every volume measurement ends with an imported ledger filling the queue with stale open records, and nothing closes them in bulk from inside."

## Context and Intent

### Problem

Every volume measurement this product has run has ended the same way: an imported history fills
the operational queue with promises nobody is going to keep, and there is no way to close them
from inside Reality.

The arithmetic is not subtle. A company arriving with two years of orders brings thousands of
commitments whose due dates passed long ago and which were fulfilled — or abandoned — in
whatever system it used before. Reality has no record of that, so every one of them is an open
promise past its date, and `overdue_outgoing_customer_commitment` reports every one. The queue
that is supposed to show what needs attention shows a wall.

`cancel_commitment` closes exactly one promise and records no reason. Closing four thousand
means four thousand calls, and afterwards nothing says why any of them were closed.

This is the last thing standing between a real company and a usable first day, and it is not an
exception class — it is an operation the product does not have.

### Scope

- Preview which promises a closure would affect, with the count, what it would release, and a
  bounded sample.
- Close them in one act, recording who did it, why, and how many.
- Refuse the act if the number changed between the preview and the confirmation.
- Select by criteria a person can state and check: the side of the business, a date the promise
  was due before, and whether anything has moved against it.
- Leave every promise that has seen movement alone.

### Non-Goals

- Deciding which promises are dead. Reality does not know, and guessing would close orders a
  company is still working. The operator states the criteria and confirms a number they have
  seen.
- Closing anything other than promises. Documents, invoices and postings are untouched: a
  cancelled commitment stops an obligation, it does not rewrite what a source said.
- Reopening. A cancelled promise stays cancelled; if goods move afterwards the movement records
  itself and says what happened.
- An exception class for stale promises. The overdue class already reports them; what was
  missing is the way out, not another way in.
- Automatic closure on import, or a scheduled sweep. Both would make Reality the author of a
  judgement about somebody else's business.
- Bulk anything else. This operation exists for one condition and is not a general facility.

### Existing Contracts

- [`docs/features/commitments.md`](../../docs/features/commitments.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/008-commitments-holds/spec.md`](../008-commitments-holds/spec.md)
- [`specs/023-movement-corrections/spec.md`](../023-movement-corrections/spec.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-06

- Q: Who decides which promises are dead? → A: The operator, always. Reality can show what
  matches a stated rule and can refuse to act on a stale number, and it must not decide that an
  order nobody has shipped is abandoned rather than late. A company still chasing a six-month
  backlog would lose it.
- Q: Why a preview and a confirmed count rather than one call? → A: Because a bulk mutation
  nobody has looked at is the opposite of what this product is for, and because the set can
  change between looking and acting. The document correction path already refuses a stale
  revision; this refuses a stale count for the same reason.
- Q: Should promises with partial movement be closable? → A: No. Something has happened against
  them, so they are live records of an unfinished job rather than residue of an import.
  Excluding them is the difference between clearing noise and destroying work.
- Q: Should the reason be optional? → A: No. This is the one operation that changes thousands
  of records at once, and in a year the only thing that will explain it is the sentence
  somebody wrote when they did it.
- Q: Should this also close the documents behind the promises? → A: No. A promise is an
  obligation Reality owns; a document is what a source said. Cancelling the first is a
  judgement about the future, rewriting the second would be a claim about the past.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See What Would Close (Priority: P1)

An operator states the criteria and sees how many promises match, what would be released, and
enough of them to recognise what they are looking at.

**Why this priority**: Nobody should close four thousand records they have not seen, and
nothing else in this feature is safe without it.

**Independent Test**: Record promises across several dates and states, preview a closure, and
verify the count, the released reservations and the sample match what the criteria describe.

**Acceptance Scenarios**:

1. **Given** open promises due before a date and others due after it, **When** a closure is
   previewed for that date, **Then** only the earlier ones are counted.
2. **Given** a promise with quantity already shipped against it, **When** the closure is
   previewed, **Then** it is not counted, whatever its date.
3. **Given** matching promises with active reservations, **When** the closure is previewed,
   **Then** the quantity that would be released is stated.
4. **Given** more matching promises than the sample size, **When** the closure is previewed,
   **Then** the full count is stated and the sample is bounded.
5. **Given** criteria matching nothing, **When** the closure is previewed, **Then** it reports
   nothing rather than failing.

### User Story 2 - Close Them in One Act (Priority: P1)

An operator confirms the number they saw and a reason, and the promises close together.

**Why this priority**: It is the whole point; a first day is not usable until the wall is gone.

**Independent Test**: Preview, confirm the count with a reason, and verify every matching
promise is cancelled, its reservations released, and the overdue class silent for them.

**Acceptance Scenarios**:

1. **Given** a previewed closure, **When** it is confirmed with the count and a reason, **Then**
   every matching promise is cancelled and its active reservations released.
2. **Given** the same closure, **When** the queue is listed, **Then** none of those promises is
   reported as overdue.
3. **Given** a confirmation whose count no longer matches what the criteria select, **When** it
   is submitted, **Then** it is refused and nothing is closed.
4. **Given** a confirmation with no reason, **When** it is submitted, **Then** it is refused.
5. **Given** a closure that has run, **When** the record of it is read, **Then** it names who
   ran it, why, how many promises closed, and the criteria used.
6. **Given** a promise that has since seen movement, **When** the closure runs, **Then** that
   promise is left open even though it matched at preview time.

### Edge Cases

- A promise already cancelled when the closure runs.
- A promise held, or belonging to a party under a delivery hold, which never matches.
- Criteria matching promises of both directions when only one was asked for.
- A closure run twice with the same criteria, where the second run matches nothing.
- Promises of another tenant that match the same criteria.
- A due date in the future.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preview a closure, returning the number of promises that match,
  the quantity that would be released from active reservations, and a bounded sample of the
  promises themselves.
- **FR-002**: Criteria MUST be limited to the side of the business and a date the promise was
  due before, both stated by the caller.
- **FR-003**: A promise with any quantity moved against it MUST never match, whatever its date.
- **FR-004**: A promise that is not open MUST never match.
- **FR-004a**: A promise under a hold MUST never match, and neither MUST one whose party is
  under a delivery hold. A hold is a person saying they are dealing with this; closing it in
  bulk would overrule a decision somebody made deliberately, which is the opposite of what this
  operation is for.
- **FR-005**: A promise with no due date MUST never match, because a date is what makes
  "before" meaningful and a dateless promise is judged by a different class entirely.
- **FR-006**: Closing MUST require the count the caller saw, and MUST be refused where the
  criteria no longer select exactly that number.
- **FR-007**: Closing MUST require a reason, and MUST be refused without one.
- **FR-008**: Closing MUST cancel every matching promise and release its active reservations,
  through the existing single-promise cancellation so that nothing about cancelling diverges.
- **FR-009**: The act MUST be recorded once with the criteria, the reason, the count and the
  actor, in addition to whatever each cancellation records.
- **FR-010**: Both operations MUST be reachable through the JSON API and the agent tool
  catalog, and the closing one MUST require explicit human confirmation.
- **FR-011**: Neither operation MUST touch Documents, LedgerEntries or Movements.
- **FR-012**: A closure MUST be atomic: either every matching promise closes or none does.
- **FR-013**: A closure whose criteria match nothing and whose confirmed count is zero MUST
  succeed and change nothing, so running the same closure twice is safe rather than an error.

### Domain and Traceability Requirements

- **DR-001**: No schema changes. Cancellation, reservations and the business event record all
  exist.
- **DR-002**: Every read, preview, refusal and closure MUST be tenant-scoped, and promises of
  another tenant MUST never match.
- **DR-003**: The preview MUST NOT write anything.
- **DR-004**: Cancelling in bulk MUST use the same operation a single cancellation uses, so the
  two can never disagree about what cancelling means.
- **DR-005**: The recorded act MUST reach its records by opaque identity and MUST NOT restate
  business fields beyond the criteria a person typed.
- **DR-006**: No operational exception class is added; the overdue class keeps reporting what
  is open, and this operation is how it is answered.

### Key Entities *(when data is involved)*

- **Commitment**: The promises closed, selected by side, due date and the absence of movement.
- **Reservation**: What the closure releases, through the existing cancellation.
- **BusinessEvent**: The one record of the act, carrying the criteria, the reason and the count.

## Success Criteria *(mandatory)*

- **SC-001**: A company arriving with an imported history can clear the promises it is not
  going to keep, from inside the product, in one act.
- **SC-002**: Nothing closes that anybody has moved goods against.
- **SC-003**: Nobody closes a number they have not seen.
- **SC-004**: A year later, the record says who closed what and why.
- **SC-005**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- The queue's wall on a first day is made of overdue promises, which the volume measurements of
  Specs 068 and 069 both observed. If a later import produces a different kind of residue, this
  operation does not address it.
- A due date is the only ordering a stale promise reliably carries. Promises without one are
  Spec 080's business, and closing them in bulk would need a different rule.
- The operator is a person with a reason, not a scheduled job. Nothing here runs by itself.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1, 3, 4 | preview shape test |
| FR-002 | US1 scenario 1 | criteria test |
| FR-003 | US1 scenario 2; US2 scenario 6 | moved-against exclusion test |
| FR-004 | Edge cases | non-open exclusion test |
| FR-004a | Edge cases | held promise exclusion test |
| FR-005 | Edge cases | dateless exclusion test |
| FR-006 | US2 scenario 3 | stale count refusal test |
| FR-007 | US2 scenario 4 | missing reason refusal test |
| FR-008 | US2 scenarios 1, 2 | closure test |
| FR-009 | US2 scenario 5 | recorded act test |
| FR-010 | US2 scenario 1 | API and tool contract test |
| FR-011 | US2 scenario 1 | untouched records test |
| FR-012 | US2 scenario 3 | atomicity test |
| FR-013 | Edge cases | empty closure test |
| DR-001 | — | no migration added |
| DR-002 | Edge cases | tenant isolation test |
| DR-003 | US1 scenario 1 | preview writes nothing test |
| DR-004 | US2 scenario 1 | shared cancellation test |
| DR-005 | US2 scenario 5 | recorded act test |
| DR-006 | US2 scenario 2 | catalog class count unchanged |
