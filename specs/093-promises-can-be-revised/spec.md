# Feature Specification: When the Other Side Says a New Date

**Feature Branch**: `093-promises-can-be-revised`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "A Commitment carries one `due_at`, set when it is created, and nothing anywhere updates it. A supplier saying 'not the tenth, the twenty-fourth' cannot be recorded at all."

## Context and Intent

### Problem

A `Commitment` is a promise with a date. That date is written once, at creation, from what the
order asked for — and **nothing in the product ever changes it**. There is no operation, no
endpoint and no tool that can.

So the ordinary event in every trading relationship is unrecordable. A supplier acknowledges an
order and names a different date. A customer asks for a delay and the company agrees. Neither is
expressible, and the consequences run in both directions:

- **The queue reports a date nobody is working to.** `overdue_incoming_supplier_commitment`
  measures against a date the supplier revised weeks ago. The entry is true about the original
  promise and useless about today, and an operator who knows the supplier moved it learns to
  scroll past the class.
- **The revision itself is lost.** That a supplier moved this order — once, or three times — is
  one of the more useful things a company can know about a supplier, and Reality holds nothing
  about it.

The only way to record a new date today would be to overwrite the old one, which the product
does not offer and should not: **a date the supplier stated is a received value, and a second
statement must not erase the first.**

### Scope

- Record that a counterparty has stated a new date for a promise, without destroying the date it
  replaces.
- Judge the promise against the date that is now in force.
- Say, on an entry that is still overdue, that the promise had already been moved — so a
  revision cannot buy silence.

### Non-Goals

- **Deciding whether a revision is acceptable.** Reality records that the supplier said the
  twenty-fourth. Whether that is tolerable is a commercial judgement with a person behind it.
- **A class for a promise moved too often.** "Too often" is a number nobody has measured, and
  this queue already carries more unmeasured constants than it should. What a revised promise
  does get is a named reason on the entry it produces when it is late again, which needs no
  threshold at all.
- **Changing what a promise means.** Fulfilment, reservations and every quantity class are
  untouched. Only the date in force moves.
- **Correcting a mistake.** A correction says the record was wrong; a revision says the record
  was right and the world changed. The product has correction machinery for movements and ledger
  entries, and this is deliberately not it.
- **Revising anything but the date.** A quantity change is a different promise, not the same one
  later.
- **Rewriting the order line.** What the order asked for stays what the order asked for; the
  promise is what moves.

### Existing Contracts

- [`docs/features/commitments.md`](../../docs/features/commitments.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/features/procure_to_pay.md`](../../docs/features/procure_to_pay.md)
- [`specs/080-learned-lag/spec.md`](../080-learned-lag/spec.md)
- [Constitution](../../.specify/memory/constitution.md), principles I and VIII

## Clarifications

### Session 2026-09-06

- Q: A new column on the commitment, or a record per revision? → A: A record per revision. A
  column would hold only the latest date, so a supplier's second statement would overwrite its
  first — and a date somebody stated is a received value. Append-only is also how this product
  already treats movements, ledger entries and source records.
- Q: Does judging against the revised date let a supplier hide by moving it? → A: It would, and
  that is why the entry says so. Once the revised date has passed too, the overdue entry carries
  a named reason that this promise had already been moved, and the causal values name the date it
  was originally due. No threshold, no silence bought.
- Q: Should a revision be refused for a promise on hold? → A: No. A hold stops execution;
  recording what the other side said is not execution, and refusing it would lose a statement
  because of an unrelated block.
- Q: Can a revision name a date already past? → A: Yes. A supplier admitting it will be three
  days late is a real statement and the most useful kind.
- Q: Both directions? → A: Yes. A supplier moving a delivery and a company agreeing a later date
  with a customer are the same act with different parties, and the same record serves both.
- Q: What about a promise nobody dated at all? → A: Stating a date makes it dated, so it stops
  being an undated order and the class that reports those stops reporting it. That is correct and
  it is one of the few existing classes this feature touches.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The Supplier Names a New Date (Priority: P1)

An operator records that the supplier now says the twenty-fourth, and the queue stops reporting
the order against the tenth.

**Why this priority**: Until it exists, the class judging supplier lateness measures against a
date nobody is working to.

**Independent Test**: Create a supplier delivery due on a past date, record a revision to a
future one, and read the queue.

**Acceptance Scenarios**:

1. **Given** an overdue supplier delivery, **When** the supplier's new and future date is
   recorded, **Then** it is no longer reported as overdue.
2. **Given** the same promise, **When** the revised date also passes, **Then** it is reported as
   overdue again, carrying the reason that the promise had already been moved and the date it was
   originally due.
3. **Given** two revisions, **When** the queue is read, **Then** the promise is judged against
   the later statement.
4. **Given** the revision recorded, **When** the promise is read, **Then** the date it was
   originally due is still there.
5. **Given** a revision naming a date already past, **When** it is recorded, **Then** it is
   accepted, because a supplier admitting lateness is a statement worth keeping.

### User Story 2 - The Company Agrees a Later Date with a Customer (Priority: P1)

The same act in the other direction.

**Acceptance Scenarios**:

1. **Given** an overdue customer delivery, **When** a later date is agreed and recorded, **Then**
   it is no longer reported as overdue.
2. **Given** the revised date passing, **When** the queue is read, **Then** it is reported again
   with the same reason.

### User Story 3 - A Revision Cannot Be Lost (Priority: P1)

Every date a counterparty stated stays readable.

**Acceptance Scenarios**:

1. **Given** three revisions on one promise, **When** they are read, **Then** all three and the
   original date are there, in the order they were stated.
2. **Given** a revision, **When** it is recorded, **Then** nothing about the promise's own record
   has been overwritten.

### Edge Cases

- A revision on a promise that is already fulfilled or cancelled.
- A revision on a promise nobody dated.
- A revision naming the same date the promise already has.
- Two revisions stated at the same instant.
- A revision on another tenant's promise.
- A revision on a promise with an active hold.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A counterparty's newly stated date for a promise MUST be recordable, and MUST NOT
  overwrite the date it replaces or any earlier statement.
- **FR-002**: Every recorded statement MUST carry when it was stated and MAY carry a note and the
  source record it came from.
- **FR-003**: The date in force for a promise MUST be the most recently stated one, or the
  promise's own date where none has been stated.
- **FR-004**: Every class that judges a promise by its date MUST judge it by the date in force.
- **FR-005**: A promise that had no date and now has a stated one MUST stop being reported as an
  undated order.
- **FR-006**: An overdue entry for a promise whose date has been revised MUST carry a named
  reason saying so, and MUST name the date it was originally due and how many times it has been
  moved.
- **FR-007**: That reason MUST NOT suppress or otherwise alter the entry; a revised promise past
  its revised date is as overdue as any other.
- **FR-008**: Recording a revision MUST be refused for a promise that is not open, for a promise
  belonging to another tenant, for an unknown promise, and without a readable date.
- **FR-009**: Recording a revision MUST be allowed for a promise with an active hold, because a
  hold stops execution and this records a statement.
- **FR-010**: A revision MUST be recordable for both directions of promise.
- **FR-011**: The operation MUST be declared in the command catalog, the tenant isolation catalog
  and the capability guidance, and MUST be reachable from the API and the agent tools.
- **FR-012**: The queue MUST remain deterministically ordered for identical data.
- **FR-013**: Every existing class MUST behave exactly as it does today for a promise nobody has
  revised.

### Domain and Traceability Requirements

- **DR-001**: One new table, appended to and never updated. No column on the promise itself
  changes, because that would overwrite a received value.
- **DR-002**: The date in force MUST be derived at read time and MUST NOT be stored on the
  promise.
- **DR-003**: One shared rule MUST answer what date is in force, used by every class that asks,
  so no two can disagree.
- **DR-004**: Every read, derivation and write MUST be tenant-scoped.
- **DR-005**: Traces MUST reach their records by opaque identity.
- **DR-006**: One cause is added to the closed vocabulary, with the authority and evidence a
  cause requires.
- **DR-007**: No figure and no date may be derived, inferred or adjusted; every date recorded is
  one somebody stated.

### Key Entities *(when data is involved)*

- **Commitment**: The promise, whose own date stays the date it was made with.
- **CommitmentRevision**: One statement by a counterparty that the date is now something else.

## Success Criteria *(mandatory)*

- **SC-001**: The ordinary event of a supplier acknowledging a different date can be recorded.
- **SC-002**: The queue judges a promise by the date that is actually in force.
- **SC-003**: No statement about a date is ever destroyed by a later one.
- **SC-004**: A revision cannot buy silence: a promise late against its own revised date says
  that it was moved.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically ordered
  queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- A revision is a statement somebody recorded, from an acknowledgement, an email or a call.
  Reality does not fetch it and does not judge whether it was reasonable.
- Reporting a moved promise as a reason rather than as its own class means a supplier that moves
  dates repeatedly and always beats the revised one is never reported. That is deliberate — it is
  meeting its stated promises — and it is the limit of what this feature says.
- The date in force becomes a derived figure that several classes depend on, which is one more
  thing that must not drift. It is one shared rule for that reason.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US3 scenarios 1, 2 | append-only revision test |
| FR-002 | US3 scenario 1 | revision fields test |
| FR-003 | US1 scenarios 1, 3 | date in force test |
| FR-004 | US1 scenario 1; US2 scenario 1 | class judges the date in force test |
| FR-005 | Edge cases | undated promise becomes dated test |
| FR-006 | US1 scenario 2; US2 scenario 2 | revised reason test |
| FR-007 | US1 scenario 2 | entry otherwise unchanged test |
| FR-008 | Edge cases | refusal tests |
| FR-009 | Edge cases | held promise test |
| FR-010 | US2 scenario 1 | both directions test |
| FR-011 | US1 scenario 1 | catalog drift gates and surface tests |
| FR-012 | US1 scenario 3 | deterministic ordering test |
| FR-013 | — | the existing suites, unchanged |
| DR-001 | — | one migration adding one table |
| DR-002 | US1 scenario 4 | nothing stored on the promise test |
| DR-003 | US1 scenario 1 | one shared rule test |
| DR-004 | Edge cases | tenant isolation test |
| DR-005 | US1 scenario 2 | opaque trace test |
| DR-006 | US1 scenario 2 | cause vocabulary drift gate |
| DR-007 | US1 scenario 5 | recorded-dates-only test |
