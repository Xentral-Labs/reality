# Feature Specification: The Invoice Nobody Booked

**Feature Branch**: `092-invoice-unposted`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "A credit note recorded and never booked has been reported since Spec 084, with its own description saying recording and booking are two acts 'exactly as they are for an invoice'. The invoice case was argued and never built."

## Context and Intent

### Problem

`credit_note_unposted` reports a credit promised on paper and never booked. Its description in
the catalog says, in as many words, that recording and booking are two acts **"exactly as they
are for an invoice"**. The mirror was argued in 084, again in 089 for the supplier side, and has
never existed for the document both process chains actually hang on.

An invoice recorded and never booked is worth more than its credit-note sibling, in both
directions:

- **A sales invoice nobody booked** means the company has billed a customer and its own accounts
  know nothing about it. Nothing is owed as far as Reality is concerned, so no reminder, no
  aging, no credit-limit arithmetic includes it. The money is invisible until somebody books it.
- **A supplier invoice nobody booked** means the company owes money its books do not show. It
  will not appear in a payment run, no early-payment discount is offered for it, and nothing
  accrues.

Neither is reportable today, and until Spec 091 neither could even happen on a real tenant,
because nothing outside the demo could book an invoice at all. That is why this is a separate
specification rather than part of that one: **a class reporting invoices nobody booked, on a
product where nobody could book one, would have reported every invoice in the tenant.**

### Scope

- Report a sales invoice recorded and never booked, judged against the rhythm this company has
  shown for booking its own sales invoices.
- Report a supplier invoice recorded and never booked, judged against its own separate rhythm.
- Reuse the body, the rule and the guards that already serve the two credit-note classes.

### Non-Goals

- **Booking anything automatically.** The whole point of the class is that a gap between two acts
  is a real business fact. A product that closed the gap itself would have nothing to report and
  would post figures nobody asked to post.
- **One class for both directions.** The owner differs — billing on one side, accounts payable on
  the other — and so does whose money is wrong. One row for two jobs is a worklist nobody owns,
  which is the same argument Spec 089 made for splitting the credit classes.
- **Sharing a learned rhythm with anything.** How long a company takes to book its own sales
  invoices, its supplier invoices, its own credit notes and its suppliers' credit notes are four
  different processes with different owners. The rule is shared; no history is.
- **A configured threshold.** As everywhere else in this queue, the norm is learned from what
  this tenant has actually done.
- **Reporting a document whose posting was reversed.** Reversing is a deliberate act, not a
  forgotten one.

### Existing Contracts

- [`specs/084-credit-note-posts/spec.md`](../084-credit-note-posts/spec.md)
- [`specs/089-supplier-credit-notes/spec.md`](../089-supplier-credit-notes/spec.md)
- [`specs/091-invoices-can-be-booked/spec.md`](../091-invoices-can-be-booked/spec.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/features/ledger.md`](../../docs/features/ledger.md)
- [Constitution](../../.specify/memory/constitution.md), principle II

## Clarifications

### Session 2026-09-06

- Q: One class or two? → A: Two. A sales invoice nobody booked is billing's problem and hides
  money owed to the company; a supplier invoice nobody booked is accounts payable's and hides
  money the company owes. Same shape, different owner, opposite direction.
- Q: Should the two share the credit note's learned threshold? → A: No, and not each other's.
  Four populations, four rhythms, one rule. That is the precedent Spec 089 set after its first
  draft got it wrong.
- Q: Will this be learnable where the credit-note classes often are not? → A: Yes, and that is
  the interesting difference. Credit notes are rare, so a company issuing a handful a year never
  reaches the minimum history and is never judged. Invoices are the opposite: any trading company
  books enough of them for a rhythm to exist, so this class will actually speak.
- Q: Which account says a document is booked? → A: The one its own posting operation uses to
  refuse a second posting. Writing the four constants down together showed that
  `supplier_credit_unposted` had asked a different account from its operation since Spec 089 —
  equivalent in practice, and corrected here so the two cannot drift apart if a posting ever
  changes.
- Q: What about an invoice whose posting was reversed? → A: Not reported. The reversing entries
  carry no document reference, so the original still reads as booked — which is also the right
  answer: somebody booked it and then deliberately unbooked it, which is not the same as nobody
  having got round to it.
- Q: What stops this flooding a tenant that imported history? → A: The same minimum history every
  learned rule uses. A tenant that recorded thousands of invoices and booked none has no rhythm
  to be judged against and is told nothing. The class speaks for a company that books most of
  them and has forgotten some, which is exactly the condition.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The Sales Invoice Nobody Booked (Priority: P1)

An operator sees sales invoices that were recorded and never booked, so the money the company is
owed stops being invisible.

**Why this priority**: Every receivable rule in the product ignores an unbooked invoice, so the
gap is silent by construction.

**Independent Test**: Give a tenant a rhythm of booking sales invoices promptly, record one and
leave it, and read the queue.

**Acceptance Scenarios**:

1. **Given** a tenant that normally books a sales invoice within days and one recorded long
   before that norm allows, **When** the queue is read, **Then** it is reported.
2. **Given** the same invoice booked, **When** the queue is read, **Then** it is no longer
   reported.
3. **Given** an invoice recorded yesterday, **When** the queue is read, **Then** nothing is
   reported, because it is inside the norm.
4. **Given** a tenant with fewer than five booked sales invoices, **When** the queue is read,
   **Then** nothing is reported, because no rhythm can be claimed.

### User Story 2 - The Supplier Invoice Nobody Booked (Priority: P1)

The same on the buying side, so money the company owes stops being invisible.

**Acceptance Scenarios**:

1. **Given** a rhythm of booking supplier invoices and one left unbooked past it, **When** the
   queue is read, **Then** it is reported.
2. **Given** a tenant that books its sales invoices promptly and has never booked a supplier
   invoice, **When** the queue is read, **Then** no supplier invoice is reported, because one
   side's rhythm never judges the other.
3. **Given** the same tenant once it has a supplier-invoice rhythm, **When** the queue is read,
   **Then** the unbooked supplier invoice is reported.

### User Story 3 - The Four Sides Stay Apart (Priority: P2)

Each of the four unposted classes reports only its own document type.

**Acceptance Scenarios**:

1. **Given** an unbooked sales invoice, supplier invoice, credit note and supplier credit note,
   **When** the queue is read, **Then** each is reported by exactly one class.

### Edge Cases

- An invoice whose posting was reversed.
- An invoice with no readable document date.
- An invoice recorded and booked in the same moment.
- A tenant with a rhythm on one document type and none on the other three.
- An invoice for zero.
- A credit note reported by an invoice class, or the reverse.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST report a sales invoice recorded and never booked, judged against
  the rhythm this company has shown for booking its own sales invoices.
- **FR-002**: The system MUST report a supplier invoice on the same terms, judged against its own
  separate rhythm.
- **FR-003**: Each rhythm MUST be learned from that document type alone. No two of the four
  unposted classes may share a history.
- **FR-004**: Where fewer than the minimum number of that type have been booked, nothing MUST be
  reported for it.
- **FR-005**: A document whose posting was reversed MUST NOT be reported, because it was booked
  and then deliberately unbooked.
- **FR-006**: A document with no readable date MUST NOT be reported, because nothing can be said
  about how long it has stood.
- **FR-007**: Each of the four unposted classes MUST report only its own document type.
- **FR-008**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace, in the
  same shape as every existing class.
- **FR-009**: Each entry MUST disappear as soon as the document is booked, without
  acknowledgement or any other manual step.
- **FR-010**: The explanation of an entry MUST re-derive the current condition, and a malformed,
  unknown, cleared or foreign identity MUST produce the same not-found response the queue already
  returns.
- **FR-011**: Both classes MUST be declared in the closed catalog with an authority reference,
  named executable evidence, and the description, owner and clearing path every class carries,
  and each MUST name its credit-note counterpart and say what it hides while it stands.
- **FR-012**: Every surface that consumes the queue MUST receive both classes through the
  existing shared list and explanation contract.
- **FR-013**: The queue MUST remain deterministically ordered for identical data.
- **FR-014**: Every existing class MUST behave exactly as it does today.
- **FR-015**: Each class MUST judge a document booked by the same account its posting operation
  uses to refuse a second posting, so a class and its operation cannot disagree about what
  "booked" means.

### Domain and Traceability Requirements

- **DR-001**: No schema changes and no new service logic.
- **DR-002**: Both classes MUST be derived at read time and MUST store nothing.
- **DR-003**: All four unposted classes MUST share one body, so none can drift in what "booked"
  means.
- **DR-004**: Traces MUST reach their records by opaque identity and MUST NOT restate business
  fields already carried in causal values.
- **DR-005**: Every read and derivation MUST be tenant-scoped.
- **DR-006**: No cause is introduced; the closed cause vocabulary is untouched.

### Key Entities *(when data is involved)*

- **Document**: The sales or supplier invoice recorded and not booked.
- **LedgerEntry**: What its absence is judged by, and what ends the condition.

## Success Criteria *(mandatory)*

- **SC-001**: Money the company is owed, and money it owes, stop being invisible because nobody
  booked the paperwork.
- **SC-002**: Each of the four unposted conditions is judged against its own process rhythm.
- **SC-003**: A tenant with no rhythm for a document type is told nothing about it.
- **SC-004**: Two identical reads of an unchanged tenant return an identical, identically ordered
  queue.
- **SC-005**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- Depends on Spec 091: until an invoice could be booked from a surface, no tenant could have a
  booking rhythm and this class would have been silent everywhere or wrong everywhere.
- The learned rule's constants are the same unmeasured ones every other learned class uses. They
  have never been checked against a real business, and this class inherits that.
- A company that records invoices and books none is told nothing, which is the safe direction and
  also the case where an operator might most want telling.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1, 3 | sales invoice unposted derivation test |
| FR-002 | US2 scenario 1 | supplier invoice unposted derivation test |
| FR-003 | US2 scenarios 2, 3 | separate rhythm test |
| FR-004 | US1 scenario 4 | minimum history test |
| FR-005 | Edge cases | reversed posting test |
| FR-006 | Edge cases | unreadable date test |
| FR-007 | US3 scenario 1 | four sides stay apart test |
| FR-008 | US1 scenario 1 | entry shape and trace test |
| FR-009 | US1 scenario 2 | clearing test |
| FR-010 | Edge cases | explanation not-found parity test |
| FR-011 | US1 scenario 1 | catalog coverage and guidance gate test |
| FR-012 | US1 scenario 1 | shared list and explanation contract test |
| FR-013 | US3 scenario 1 | deterministic ordering test |
| FR-014 | — | the existing suites, unchanged |
| FR-015 | Edge cases | class and operation agree test |
| DR-001 | — | no migration and no service diff |
| DR-002 | US1 scenario 2 | read-time derivation test |
| DR-003 | US3 scenario 1 | one shared body test |
| DR-004 | US1 scenario 1 | opaque trace test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US1 scenario 1 | existing cause-vocabulary drift gate |
