# Feature Specification: A Return Is Not Finished When It Arrives

**Feature Branch**: `082-return-resolved`
**Created**: 2026-09-05
**Status**: Draft
**Language**: English
**Input**: "Goods come back and nobody says what happened to them."

## Context and Intent

### Problem

Spec 079 let a return say what it reverses, so Reality can now answer how much came back and
whether it was credited. It cannot answer the question an operator actually asks next: **what
happened to the goods?**

Returned stock arrives somewhere and then either goes back on the shelf, is scrapped, or goes
back to the supplier. Each of those is a movement Reality already records. None of them says
which return it settles, so nothing connects the arrival to its outcome — and a pallet of
returns can sit in a corner for a year while every figure in the system stays correct.

The obvious cheap answer does not work. Reality could look at what is still standing in the
location returns arrive at, but stock is fungible: five units come back into the returns area
and five units later leave it, and nothing says whether those were the same five. That
produces a condition that is sometimes right, which this line of work has repeatedly refused
— an exception that is sometimes wrong is worse than none.

What is missing is the same thing that was missing for invoicing and for crediting: an edge.
An invoice line names the order line it bills; a credit note line names the order line it
credits; a movement should be able to name the return it resolves.

### Scope

- Let a movement say which return it resolves.
- Validate that link the way the others are validated: same tenant, a real return, the same
  item, out of the place the goods came back to, and never more than came back.
- Report a return with quantity still unresolved, judged against how long this company
  normally takes to resolve one.
- Give the class the identity, severity, impact, causal values, trace, explanation, ordering,
  tenant isolation and operator guidance every existing class carries.

### Non-Goals

- A returns workflow. Reality records what happened and derives what is outstanding; it does
  not model inspection steps, disposition rules or approval.
- Naming the outcome as a separate field. What happened to the goods is already what the
  resolving movement is: a transfer back to stock is a restock, an outward adjustment is a
  scrap, a shipment to the supplier is a return to them. Adding a label would be a second
  authority for something the movement already states.
- Two-step resolutions through an inspection area. A resolution must move the goods out of
  where they came back to, so a business that shuttles returns between locations first will
  see the first move counted as the resolution. That is a real limit and it is named here
  rather than solved.
- Value. What a returned item is worth, and whether scrapping it should post anything, is a
  ledger question this feature does not touch.
- Supplier returns as a promise. Sending goods back to a supplier resolves a customer return
  here; whether the supplier then credits it is the mirror of Spec 079 and is not this.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/features/movements.md`](../../docs/features/movements.md)
- [`specs/079-returns-connect/spec.md`](../079-returns-connect/spec.md)
- [`specs/080-learned-lag/spec.md`](../080-learned-lag/spec.md)
- [`specs/009-inventory-execution/spec.md`](../009-inventory-execution/spec.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-05

- Q: Why not derive this from what is left in the returns location? → A: Because stock is
  fungible and the answer would be a guess. Five back and five out later says nothing about
  whether those were the same five. The proxy is cheaper and sometimes wrong, and sometimes
  wrong is the one thing this catalog does not ship.
- Q: A column or a relation table, as movement correction uses? → A: A column. A correction
  relates three movements and carries its own reason and fingerprint, so it earned a table. A
  resolution relates two and carries nothing of its own: what happened is what the resolving
  movement already is.
- Q: How is a partial resolution handled? → A: Naturally. Five come back, three go on the
  shelf and two are scrapped, which is two movements resolving one return. The class reports
  what is still unresolved, so it shrinks and then clears.
- Q: How long is too long? → A: Learned, as Spec 080 learns its two norms, from how long this
  company's own resolved returns took. A company that inspects weekly and one that inspects
  quarterly should not share a number, and neither should have to configure one.
- Q: Must the resolution leave the place the goods arrived at? → A: Yes. It is the one
  physical check available and it makes the link mean something; without it any outward
  movement could claim to settle any return. The cost is that a business moving returns
  through an inspection area first has its first move counted as the resolution, which is
  recorded as a limit.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Say What Happened to the Goods (Priority: P1)

Somebody records the goods going back on the shelf, or being scrapped, and says which return
that settles.

**Why this priority**: Nothing can be reported about unresolved returns until a resolution
can be recorded at all.

**Independent Test**: Record a return, resolve part of it with a transfer, and verify the
link is stored and the outstanding quantity falls.

**Acceptance Scenarios**:

1. **Given** a recorded return, **When** a movement out of the returns location names it,
   **Then** the link is accepted and stored.
2. **Given** the same return, **When** a second movement resolves the remainder, **Then**
   both count and nothing is outstanding.
3. **Given** a movement naming something that is not a return, **When** it is recorded,
   **Then** it is refused.
4. **Given** a movement naming a return of another tenant, **When** it is recorded, **Then**
   it is refused.
5. **Given** a movement naming a return of a different item, or one that does not leave the
   location the goods came back to, **When** it is recorded, **Then** it is refused.
6. **Given** resolutions that would together exceed what came back, **When** the last is
   recorded, **Then** it is refused.

### User Story 2 - See the Returns Nobody Dealt With (Priority: P1)

An operator sees returns with goods still unresolved far longer than this company normally
takes, with how much is outstanding and what normal is.

**Why this priority**: It is stock the company owns, cannot sell, and has stopped counting as
a problem, and it grows quietly because every individual record is correct.

**Acceptance Scenarios**:

1. **Given** a history of returns resolved within days and one standing for months, **When**
   the queue is listed, **Then** one entry appears with the outstanding quantity, its age and
   the norm.
2. **Given** the same return, **When** the goods are restocked or scrapped, **Then** the entry
   disappears without any manual step.
3. **Given** a return resolved in part, **When** the queue is listed, **Then** the entry
   reports only what is still outstanding.
4. **Given** a company with too few resolved returns to claim a norm, **When** the queue is
   listed, **Then** no entry appears, however long anything has stood.
5. **Given** a return two days old on a company that takes a week, **When** the queue is
   listed, **Then** no entry appears.

### Edge Cases

- A return that a movement correction has voided, and a resolution that has been voided.
- A resolving movement recorded as occurring before the return it resolves, which is accepted
  and teaches the norm nothing.
- A return whose goods are transferred to another location and resolved from there.
- A return resolved by a shipment back to the supplier.
- A return of a serial-tracked item, where quantity is always one.
- A returns location that also holds ordinary stock.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A movement MUST be able to name the return it resolves, and that reference MUST
  be optional.
- **FR-002**: The reference MUST be refused unless it names a `return` movement of the same
  tenant.
- **FR-003**: The reference MUST be refused unless the resolving movement concerns the same
  item and takes goods out of the location the return brought them into.
- **FR-004**: The reference MUST be refused where the resolutions of one return would
  together exceed the quantity returned.
- **FR-004a**: A resolution recorded as having occurred before the return it settles MUST be
  accepted and MUST contribute a lag of zero to the norm. Movement instants are supplied by
  the caller everywhere in the product and nothing else polices their order; refusing here
  would make this one link stricter than the records around it, and a backdated entry is a
  recording matter rather than a business one.
- **FR-005**: A return MUST be resolvable by more than one movement, so restocking part and
  scrapping the rest needs no special handling.
- **FR-006**: An absent reference MUST mean the movement settles no return, and MUST NOT be
  treated as unknown.
- **FR-007**: The system MUST report one entry for every return with quantity still
  unresolved whose age exceeds the learned resolution threshold.
- **FR-008**: The resolution norm MUST be learned from this tenant's own resolved returns,
  using the same shape Spec 080 established: the median of the most recent completed cases, a
  product multiple, an absolute floor, and a minimum history below which nothing is claimed
  and nothing reported.
- **FR-009**: Quantities MUST exclude movements a correction has voided, on both sides of the
  comparison.
- **FR-010**: Each entry MUST state the returned quantity, the resolved quantity, what is
  outstanding, its age and the threshold.
- **FR-011**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace, in
  the same shape as every existing class.
- **FR-012**: Each entry MUST disappear as soon as its condition ends, without acknowledgement
  or any other manual step.
- **FR-013**: The explanation of an entry MUST re-derive the current condition, and a
  malformed, unknown, cleared or foreign identity MUST produce the same not-found response
  the queue already returns.
- **FR-014**: The class MUST be declared in the closed catalog with an authority reference,
  named executable evidence, and the description, owner and clearing path every class carries.
- **FR-015**: Every surface that consumes the queue MUST receive the class through the
  existing shared list and explanation contract.
- **FR-016**: The queue MUST remain deterministically ordered for identical data, with the
  longest-standing return first.

### Domain and Traceability Requirements

- **DR-001**: The reference is Reality about Reality: which movement settled which. It adds
  no status to any movement and no workflow state anywhere.
- **DR-002**: The class MUST be derived at read time from Movements the tenant already owns.
- **DR-003**: Quantities MUST come from the existing correction-aware movement path, never a
  second count.
- **DR-004**: Traces MUST reach their records by opaque identity and MUST NOT restate business
  fields.
- **DR-005**: Every read, derivation, validation and explanation MUST be tenant-scoped,
  including the norm.
- **DR-006**: No cause is introduced; the closed cause vocabulary is untouched.
- **DR-007**: The outcome of a return MUST NOT be stored as a label. What happened is what the
  resolving movement is, and a second authority for it would be a field that can disagree.

### Key Entities *(when data is involved)*

- **Movement (`return`)**: Goods coming back, whose resolution is now answerable.
- **Movement (resolving)**: The transfer, adjustment or shipment that settles it, and whose
  own type says what happened.

## Success Criteria *(mandatory)*

- **SC-001**: An operator can see, for any return, how much of it is still sitting unresolved.
- **SC-002**: Returns nobody dealt with become visible without any return becoming visible.
- **SC-003**: What happened to returned goods is answerable without any new vocabulary.
- **SC-004**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-005**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- Spec 079 is in place, so a return can name what it reverses; this feature is the other end
  of the same record's life.
- Spec 080's learned-threshold helper is in place and is the right shape for a third use.
- Absence of a resolution means the goods are still sitting. That rests on the same contract
  as Spec 076 and 079: every resolving movement sets the reference.
- A company that routes returns through an inspection area will have its first move counted
  as the resolution. That is a limit of the physical check, not of the model, and the rule to
  revisit is FR-003.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | resolution link test |
| FR-002 | US1 scenarios 3, 4 | reference validation test |
| FR-003 | US1 scenario 5 | item and location validation test |
| FR-004 | US1 scenario 6 | over-resolution refusal test |
| FR-004a | Edge cases | backdated resolution test |
| FR-005 | US1 scenario 2 | partial resolution test |
| FR-006 | US2 scenario 1 | absent-reference meaning test |
| FR-007 | US2 scenarios 1, 3 | unresolved return derivation test |
| FR-008 | US2 scenarios 4, 5 | learned norm test |
| FR-009 | Edge cases | voided movement test |
| FR-010 | US2 scenario 1 | causal values test |
| FR-011 | US2 scenario 1 | entry shape and trace test |
| FR-012 | US2 scenario 2 | clearing test |
| FR-013 | Edge cases | explanation not-found parity test |
| FR-014 | US2 scenario 1 | catalog coverage and guidance gate test |
| FR-015 | US2 scenario 1 | shared list and explanation contract test |
| FR-016 | US2 scenario 1 | deterministic ordering test |
| DR-001 | US2 scenario 2 | no-operational-state test |
| DR-002 | US2 scenario 2 | read-time derivation test |
| DR-003 | Edge cases | shared movement path test |
| DR-004 | US2 scenario 1 | opaque trace test |
| DR-005 | Edge cases | tenant isolation test, including the norm |
| DR-006 | US2 scenario 1 | existing cause-vocabulary drift gate |
| DR-007 | — | no outcome field is added |
