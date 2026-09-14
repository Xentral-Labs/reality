# Feature Specification: Eighty of the Hundred

**Feature Branch**: `097-a-promise-can-shrink`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "Spec 093 let a counterparty state a new date and deliberately left quantities alone — 'a different quantity is a different promise'. That was right for that specification and it leaves the ordinary case unrecordable: a supplier confirming eighty of the hundred."

## Context and Intent

### Problem

`Commitment.quantity` is written when the promise is created and **nothing anywhere assigns to
it**. `create_commitment` is reachable from no surface either — only from recording an order. So
a supplier that acknowledges an order with a smaller quantity leaves a company two bad options:
cancel the promise and raise a whole new order, or record nothing and let the queue keep
measuring against a hundred nobody is sending.

Spec 093 built the same thing for dates and said, in its own non-goals, that a different quantity
is a different promise. That was the right call for a specification about dates: it kept the
scope honest. It is not right as a permanent answer, because in trade the two arrive in the same
sentence — *"eighty pieces, two weeks later"* — and forcing them apart makes one conversation
into two records or none.

### Scope

- Let the same statement that revises a date also revise the quantity, or revise either alone.
- Judge every promise by the quantity now in force, as it is already judged by the date in force.
- Keep every earlier statement, because a quantity a counterparty stated is a received value.

### Non-Goals

- **Reopening a promise that is closed.** Only an open promise can be revised, which Spec 093
  already established. Raising the quantity on a fulfilled promise would reopen it, and a promise
  somebody has already finished is not the same promise.
- **Changing anything but the date and the quantity.** A different item, party or location is a
  different promise in a way a quantity is not.
- **Deciding whether a smaller quantity is acceptable.** Reality records that the supplier said
  eighty. Whether to accept, cancel or chase is a commercial judgement.
- **Releasing reservations when a promise shrinks.** Stock held for a hundred stays held; nothing
  reports it, because over-reserving is not a condition this queue has ever reported. It is named
  as a limit rather than solved, because releasing somebody's stock as a side effect of recording
  a sentence would be the product deciding something it was not asked to.
- **A class for a promise repeatedly shrunk.** The same argument Spec 093 made about dates: the
  threshold would be a number nobody has measured. The overdue entry already says the promise was
  revised.

### Existing Contracts

- [`specs/093-promises-can-be-revised/spec.md`](../093-promises-can-be-revised/spec.md)
- [`docs/features/commitments.md`](../../docs/features/commitments.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [Constitution](../../.specify/memory/constitution.md), principles I and VIII

## Clarifications

### Session 2026-09-06

- Q: A second table, or the one Spec 093 built? → A: The one that exists. A counterparty
  restating a promise is one act, and "eighty pieces, two weeks later" is one sentence. Two
  tables would make a company record it twice and let the two halves disagree about when it was
  said.
- Q: What if a revision states neither a date nor a quantity? → A: Refused. A statement that
  restates nothing is not a statement.
- Q: What if the new quantity is below what has already arrived? → A: Accepted. The supplier said
  eighty and ninety came; both are true, the over-delivery is already recorded, and refusing
  would lose the statement. What is open becomes nothing, which is what it is.
- Q: Does a promise become fulfilled when its quantity drops to what has arrived? → A: Yes, and
  it must be settled at that moment rather than at the next movement, because there may not be a
  next movement.
- Q: What happens to stock reserved for the original quantity? → A: It stays reserved. Releasing
  it would be Reality deciding something nobody asked for, and no class reports over-reservation.
  Stated as a limit.
- Q: Does the operation keep its name? → A: No. `revise_commitment_due_date` would be a lie the
  moment it revises a quantity, and a name describing what a function used to do is how the next
  reader learns to distrust the rest.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The Supplier Confirms Eighty (Priority: P1)

An operator records that the supplier will send eighty of the hundred, and everything downstream
measures against eighty.

**Why this priority**: It is the ordinary case and it is unrecordable today.

**Independent Test**: Create a supplier delivery for a hundred, revise it to eighty, receive
eighty, and read the promise and the queue.

**Acceptance Scenarios**:

1. **Given** a promise for a hundred revised to eighty, **When** what is open is read, **Then**
   it is eighty.
2. **Given** the same promise with eighty received, **When** the promise is read, **Then** it is
   fulfilled and nothing is reported.
3. **Given** the same promise overdue, **When** the queue is read, **Then** the quantity it
   reports as remaining is measured against eighty.
4. **Given** the revision, **When** the promise is read, **Then** the hundred it was made with is
   still there.
5. **Given** eighty and a later date stated together, **When** the promise is read, **Then** both
   are in force from one statement.

### User Story 2 - A Promise That Shrinks to What Arrived Is Finished (Priority: P1)

**Acceptance Scenarios**:

1. **Given** ninety received against a hundred, **When** the promise is revised to ninety,
   **Then** it is fulfilled without waiting for another movement.
2. **Given** ninety received, **When** the promise is revised to eighty, **Then** it is accepted,
   nothing is open, and the ninety that arrived is untouched.

### User Story 3 - Nothing Is Lost (Priority: P1)

**Acceptance Scenarios**:

1. **Given** three revisions, **When** they are read, **Then** all three are there in the order
   they were stated, each saying what it restated.
2. **Given** a revision stating neither a date nor a quantity, **When** it is attempted, **Then**
   it is refused.

### Edge Cases

- A revision to zero.
- A revision to a negative quantity.
- A revision on a fulfilled or cancelled promise.
- A revision stating only a date, on a promise whose quantity was revised earlier.
- A promise shrunk below what is reserved against it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: One statement MUST be able to restate a promise's date, its quantity, or both, and
  MUST NOT overwrite any earlier statement.
- **FR-002**: A statement restating neither MUST be refused.
- **FR-003**: A quantity of zero or less MUST be refused, because a promise for nothing is a
  cancellation and the product has one.
- **FR-004**: The quantity in force MUST be the most recently stated one, or the promise's own
  where none has been stated, resolved by one shared rule used by everything that asks.
- **FR-005**: What is open, what the queue reports as remaining, and whether a promise counts as
  complete MUST all be measured against the quantity in force.
- **FR-006**: A quantity below what has already moved MUST be accepted, and what is open MUST
  then be nothing.
- **FR-007**: A promise whose stated quantity falls to or below what has already moved MUST be
  settled as fulfilled at that moment.
- **FR-008**: Only an open promise MUST be revisable, and the promise's own quantity MUST stay
  the quantity it was made with.
- **FR-009**: The operation MUST be named for what it does, and every catalog, tool, schema and
  endpoint MUST follow.
- **FR-010**: Every existing class and operation MUST behave exactly as it does today for a
  promise nobody has revised.

### Domain and Traceability Requirements

- **DR-001**: One migration, adding a nullable quantity to the existing revision record and
  allowing its date to be absent. No new table.
- **DR-002**: The quantity in force MUST be derived at read time and MUST NOT be stored on the
  promise.
- **DR-003**: One shared rule MUST answer the quantity in force, beside the one that answers the
  date.
- **DR-004**: Every read, derivation and write MUST be tenant-scoped.
- **DR-005**: No operational exception class or cause is added.
- **DR-006**: Every quantity recorded MUST be one somebody stated; none may be derived or
  adjusted.

### Key Entities *(when data is involved)*

- **Commitment**: The promise, whose own date and quantity stay the ones it was made with.
- **CommitmentRevision**: One statement that the date, the quantity, or both are now something
  else.

## Success Criteria *(mandatory)*

- **SC-001**: "Eighty pieces, two weeks later" is one record.
- **SC-002**: Everything that judges a promise judges it by what is in force.
- **SC-003**: No statement about a promise is ever destroyed by a later one.
- **SC-004**: A promise that shrinks to what arrived is finished, not left open.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically ordered
  queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- Builds directly on Spec 093; without its record and its rule this would be a second way to say
  the same thing.
- Stock reserved for the original quantity stays reserved when a promise shrinks. Nothing reports
  it and nothing releases it, which is a real limit of this feature.
- Whether a company should accept a reduced promise is outside the product. Reality records the
  sentence; the decision has a person behind it.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 5; US3 scenario 1 | one statement, both figures test |
| FR-002 | US3 scenario 2 | empty revision refused test |
| FR-003 | Edge cases | zero and negative test |
| FR-004 | US1 scenario 1 | quantity in force test |
| FR-005 | US1 scenarios 1, 3 | open, remaining and complete test |
| FR-006 | US2 scenario 2 | below what moved test |
| FR-007 | US2 scenario 1 | settled at that moment test |
| FR-008 | US1 scenario 4; Edge cases | closed promise refused test |
| FR-009 | US1 scenario 1 | catalog drift gates and surface tests |
| FR-010 | — | the existing suites, unchanged |
| DR-001 | — | one migration, no new table |
| DR-002 | US1 scenario 4 | nothing stored on the promise test |
| DR-003 | US1 scenario 1 | one shared rule test |
| DR-004 | Edge cases | tenant isolation test |
| DR-005 | — | the closed registry expectation, unchanged |
| DR-006 | US1 scenario 1 | recorded-quantities-only test |
