# Feature Specification: The Hold Nobody Lifted

**Feature Branch**: `107-a-hold-nobody-lifted`
**Created**: 2026-09-08
**Status**: Draft
**Language**: English
**Input**: "A hold is somebody saying they are dealing with this. Nothing watches it, and the stale-promise closure deliberately skips held promises — so a forgotten hold protects a promise from the only sweep that could close it, permanently and silently."

## Context and Intent

### Problem

A hold is the product's way of recording *somebody is dealing with this*. `hold_commitment` stops
one promise from being executed; `hold_party_delivery` stops every shipment to a customer. Both
carry a reason code, a note, who raised it, and when. Neither changes or deletes what it holds —
that is the point of them.

**Nothing in the queue watches them.** `exceptions.py` touches `CommitmentHold` and `PartyHold`
**zero times**. There is a `hold_register` a person can go and read, and nothing that ever tells
anybody to.

Two consequences, and the second is worse than it first sounds:

**A held promise is invisible twice over.** A hold suppresses nothing else in the queue, so the
promise it holds still appears where it appeared before. But the *hold itself* — the reason
somebody gave, and the fact that they gave it three months ago — is nowhere.

**A forgotten hold is permanent.** `close_stale_promises` is the one operation that closes many
promises at once, and it deliberately skips anything with an active commitment hold or whose party
has an active delivery hold: a hold is somebody saying they are dealing with it, so a sweep must
not close it out from under them. That protection has no expiry. A hold raised for a credit check
somebody finished a year ago goes on shielding its promise from the only sweep that could close
it, and nothing reports either fact.

And a customer delivery hold does more than shield: while it stands, **every** shipment to that
customer is refused at write time — including orders taken after the hold was raised, by people
who never knew about it.

### Scope

- Report a hold nobody has lifted, judged against how long this company normally takes to lift
  one.
- Say what the hold is holding back, so an operator can tell a forgotten formality from a block
  on a real backlog.
- Nothing else. No schema, no new operation, no change to any existing class.

### Non-Goals

- **Releasing a hold automatically.** A hold is a person's statement that they are dealing with
  something. Lifting it because time passed would be the product deciding it knows better, and it
  would remove the protection that makes holds worth having.
- **Suppressing anything while a hold stands.** A held promise appears in the queue exactly as it
  does today. A hold says somebody is dealing with it, not that it is fine.
- **Releasing holds when a promise is cancelled.** `cancel_commitment` leaves holds standing
  today, which is how a hold on a closed promise exists at all. Changing that is a behaviour
  change to a shipped operation and belongs in its own specification; this one leaves those holds
  alone and says why they are not reported.
- **A payment hold, or any second party hold type.** Spec 098 considered one and did not build it.
  This class will report whatever hold types exist, which means a future type must arrive with its
  own release path — stated here so that is a requirement rather than a surprise.
- **Reporting how long a hold *should* take by reason code.** A credit check and an address
  clarification take different times, and nobody has measured either. One learned rhythm per hold
  kind is what the evidence supports; splitting by reason would be six thresholds nobody has
  looked at.

### Existing Contracts

- [`specs/085-close-stale-promises/spec.md`](../085-close-stale-promises/spec.md) — the sweep that
  skips held promises
- [`specs/080-learned-lag/spec.md`](../080-learned-lag/spec.md) — the threshold rule this reuses
- [`docs/features/commitment_holds.md`](../../docs/features/commitment_holds.md)
- [`docs/features/party_delivery_holds.md`](../../docs/features/party_delivery_holds.md)
- [Constitution](../../.specify/memory/constitution.md), principles II, V and VIII

## Clarifications

### Session 2026-09-08

- Q: Can a person actually lift these holds from a surface? → A: Yes, checked before designing
  anything. `release_commitment_hold` and `release_party_delivery_hold` are declared commands on
  CLI, Web, API, MCP and Chat. A class whose clearing path nothing reaches is the Spec 091 mistake,
  and this is the check that would have caught it.
- Q: One class or two? → A: Two, and only because a class carries one `record_type` and these are
  two records. One derivation body serves both, parameterised, the way the return and open-item
  classes already are. They are the same condition with the same clearing path.
- Q: Two learned rhythms or one? → A: Two. A promise hold and a customer delivery hold are
  different processes with different people behind them, and Spec 089 settled that populations
  belonging to different processes each learn their own statistic. Share the rule, never the
  history.
- Q: What severity? → A: The promise hold is normal and the party hold is high, because their blast
  radii genuinely differ. A forgotten promise hold blocks one promise. A forgotten customer
  delivery hold refuses every shipment to that customer, including orders taken by people who
  never knew about it.
- Q: What does the entry say a hold is holding back? → A: For a promise hold, the open quantity on
  that promise, in that promise's own unit. For a party hold, the **number** of open customer
  deliveries — never a summed quantity, because quantities across different items do not add up.
  Spec 076 settled that and this does not make an exception for a count that would look tidier.
- Q: Is a hold on a closed promise reported? → A: No. It holds nothing back, so there is nothing
  for anybody to clear, and a queue full of holds on cancelled promises is the wall Spec 088
  refused. That such holds exist at all is named as a limit rather than fixed here.
- Q: What floor? → A: A week, the same as the stalled-order floor. A hold is an active statement
  that somebody is on it, so a few days is ordinary and a week is the shortest span in which
  "forgotten" means anything.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The Credit Check Nobody Finished (Priority: P1)

A promise was held for a credit check months ago. The check was done, nobody lifted the hold, and
the promise has been quietly exempt from every sweep since.

**Why this priority**: It is the case that makes a forgotten hold permanent rather than merely
untidy.

**Independent Test**: Hold an open promise, let this company's own rhythm pass, and read the queue.

**Acceptance Scenarios**:

1. **Given** a promise held longer than this company's rhythm for lifting promise holds, **When**
   the queue is read, **Then** it is reported with the reason somebody gave, who gave it, how long
   it has stood, and what is still open on the promise.
2. **Given** a promise held for less than that, **When** the queue is read, **Then** nothing is
   reported.
3. **Given** the hold being lifted, **When** the queue is read, **Then** the entry is gone with
   nothing stored and no manual step.
4. **Given** a hold on a fulfilled or cancelled promise, **When** the queue is read, **Then**
   nothing is reported, because nothing is being held back.
5. **Given** a company with fewer than five lifted promise holds, **When** the queue is read,
   **Then** nothing is reported, because the rule cannot speak yet.

### User Story 2 - The Customer Nobody Can Ship To (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a customer delivery hold standing longer than this company's rhythm, **When** the
   queue is read, **Then** it is reported as high, naming the hold type, the reason, and **how
   many** open customer deliveries it is blocking.
2. **Given** such a hold blocking no open promises, **When** the queue is read, **Then** it is
   still reported, because it will refuse the next order too.
3. **Given** the two hold kinds, **When** the queue is read, **Then** each is judged against its
   own population of lifted holds, and one company's history is never read for another.

### User Story 3 - Nothing Else Moves (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a held promise, **When** the queue is read, **Then** every other class reports
   exactly what it reported before this shipped.
2. **Given** a company that holds nothing, **When** the queue is read, **Then** it is unchanged.

### Edge Cases

- A hold raised and lifted within the same instant.
- A hold whose promise has no open quantity left.
- Several holds on one party over time, one of them still open.
- A party hold of a type that has no release path.
- A hold created by an agent rather than a person.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: One operational exception class MUST report an unreleased commitment hold, and one
  MUST report an unreleased party hold, sharing one derivation body.
- **FR-002**: Each class MUST judge against its own population of lifted holds, using the Spec 080
  rule unchanged, and MUST report nothing where that population is too small.
- **FR-003**: The floor MUST be a week for both, and no entry may appear sooner.
- **FR-004**: A promise-hold entry MUST name the reason code, the note, who raised it, how long it
  has stood, the norm it was judged against, and the quantity still open on the promise it holds.
- **FR-005**: A party-hold entry MUST name the hold type, the reason code, the note, who raised it,
  how long it has stood, the norm, and the **count** of open customer deliveries it blocks. It MUST
  NOT sum quantities across items.
- **FR-006**: A hold on a promise that is not open MUST NOT be reported.
- **FR-007**: A party hold MUST be reported whatever its type, and the type MUST appear in the
  entry.
- **FR-008**: The party-hold class MUST be high severity and the promise-hold class normal, and the
  catalog MUST say why.
- **FR-009**: Both entries MUST clear when the hold is released, with nothing stored and no manual
  step.
- **FR-010**: Nothing may be released, suppressed or changed by these classes existing.
- **FR-011**: Every existing class, operation, register and projection MUST behave exactly as it
  does today.

### Domain and Traceability Requirements

- **DR-001**: No migration, no new operation, and no new operational exception cause.
- **DR-002**: Exactly two classes are added, and the closed registry MUST stay closed: catalog
  ids, class order and derivation registry agree.
- **DR-003**: The learned rule MUST be the shared one, and each class MUST learn from its own
  population. A rule is shared; a history never is.
- **DR-004**: Both durations MUST be derived at read time from the hold's own timestamps and MUST
  NOT be stored.
- **DR-005**: Every read and derivation MUST be tenant-scoped.
- **DR-006**: The clearing path of each class MUST already be reachable from every adapter it is
  declared on, and that MUST be verified rather than assumed.

### Key Entities *(when data is involved)*

- **CommitmentHold** and **PartyHold**: unchanged. Both already carry when they were raised, why,
  by whom, and when they were released.
- **Commitment**: unchanged, read to say what a hold is holding back.

## Success Criteria *(mandatory)*

- **SC-001**: A hold somebody forgot is visible, and stops being visible when it is lifted.
- **SC-002**: An operator can tell a forgotten formality from a block on a real backlog.
- **SC-003**: A promise no longer stays permanently exempt from the stale-promise sweep in silence.
- **SC-004**: Nothing is released, suppressed or decided by the product.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically ordered
  queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- Holds on closed promises exist because cancelling a promise does not release them. They are not
  reported and not cleaned up; that is a stated limit and a separate specification.
- A future party hold type will be reported by this class, so it must arrive with a release path.
- How long a hold *should* take differs by reason code and nobody has measured it. One rhythm per
  hold kind is what the evidence supports.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1; US2 scenario 1 | both derivation tests |
| FR-002 | US1 scenarios 2, 5; US2 scenario 3 | learned rhythm and minimum tests |
| FR-003 | US1 scenario 2 | floor test |
| FR-004 | US1 scenario 1 | promise-hold entry test |
| FR-005 | US2 scenarios 1, 2 | party-hold entry test, count not sum |
| FR-006 | US1 scenario 4 | closed promise test |
| FR-007 | Edge cases | hold type in the entry test |
| FR-008 | US2 scenario 1 | the catalog and its guidance |
| FR-009 | US1 scenario 3 | the entry clears test |
| FR-010 | US3 scenario 1 | nothing suppressed test |
| FR-011 | US3 scenario 2 | the existing suites, unchanged |
| DR-001 | — | no migration, no command added |
| DR-002 | — | the closed registry test |
| DR-003 | US2 scenario 3 | shared rule, separate histories test |
| DR-004 | US1 scenario 1 | nothing stored test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | — | the reachability check recorded in the plan |
