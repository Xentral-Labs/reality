# Feature Specification: A Credit Note Gives the Money Back

**Feature Branch**: `084-credit-note-posts`
**Created**: 2026-09-05
**Status**: Draft
**Language**: English
**Input**: "Was returns finished? The credit note records a quantity and never touches the money."

## Context and Intent

### Problem

The return-to-resolution chain has a hole in the middle, and it is worse than a missing
feature because an existing class quietly says something it does not mean.

Spec 079 gave a credit note lines that name the order line they credit, so Reality can report
goods that came back and were never credited. That credit note **posts nothing**. It is a
quantity document and no more.

The money path is a different thing entirely. `post_sales_credit` takes an invoice and an
amount — not a credit note — and reduces the receivable. It is reachable from nowhere: not the
JSON API, not the agent tool catalog, not the web application. Its only caller in the whole
product is the demo script.

Two consequences follow. A company using Reality cannot record a credit at all through any
surface it has. And `returned_not_credited` disappears the moment somebody records a credit
note line, **whether or not any money was ever given back** — so a queue that says "credited"
means only "noted as credited", and the operator reading it cannot tell.

There is a third, and it is the one that decides the shape of this feature. Reducing an open
receivable only works while something is open. `allocate_settlement` refuses an allocation
larger than the invoice's open amount, so **a credit against an invoice the customer has
already paid cannot be expressed at all** — which is the ordinary consumer return: paid at
checkout, sent back a week later. The most common return in the business this product is for
is the one the existing credit path cannot handle.

The ledger itself has no such problem. An invoice debits the receivable, a payment credits it,
and a credit note credits it again — leaving the receivable negative, which is exactly the
statement "we owe this customer money". Nothing about that is unusual; the credit was simply
never given the shape an invoice already has.

### Scope

- Post a credit note as a document in its own right, using the total it states, as the exact
  reverse of the posting a sales invoice makes. It stands as an obligation to the customer and
  needs no invoice to exist.
- Settle a posted credit note the two ways a business settles one: allocate it against an open
  invoice, or refund the customer.
- Record a customer refund, as the mirror of the customer payment that already exists.
- Make both postings reachable through the JSON API and the agent tool.
- Report a credit note recorded and never posted.
- Report a posted credit note that has neither been allocated nor refunded.
- Say plainly, in the guidance of the class that measures quantities, that it measures
  quantities.
- Record, post and settle a credit note in the demo month the new way.

### Non-Goals

- Supplier credit notes. Goods going back to a supplier and the credit that follows are the
  mirror flow, with a different document and a different owner, and neither is expressed today.
- Changing what `returned_not_credited` measures. It answers a quantity question and answers it
  correctly; what was missing is the money question beside it.
- Allocating one credit note across several invoices, or one refund across several credit
  notes. A payment settles one invoice in this product and the credit path follows the same
  rule; spreading either is one feature for both, not half of one here.
- Deciding whether a credit should be netted or refunded. Both are recorded, neither is
  advised, and no rule prefers one.
- Automatic posting on recording. An invoice is recorded and posted as two acts, and a credit
  note is no different; the gap between them is exactly what one of the new classes measures.
- Tax on a credit. Reality records the total a source states and computes no tax anywhere.

### Existing Contracts

- [`docs/features/ledger.md`](../../docs/features/ledger.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/012-ledger-finance/spec.md`](../012-ledger-finance/spec.md)
- [`specs/079-returns-connect/spec.md`](../079-returns-connect/spec.md)
- [`specs/080-learned-lag/spec.md`](../080-learned-lag/spec.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-05

- Q: Should a credit note reduce an open invoice, or stand on its own? → A: Stand on its own.
  Reducing an open receivable cannot express a credit against an invoice already paid, which is
  the ordinary consumer return. A credit note that posts like a reversed invoice leaves the
  receivable negative — the company owes the customer — and that is a true statement whether or
  not anything is open.
- Q: Then what settles it? → A: Either an allocation against an open invoice, or a refund. Both
  go through the settlement relation payments already use, so a credit note is settled the same
  way an invoice is, from the other direction.
- Q: Which amount does it post? → A: The total the credit note states. Constitution principle
  VIII settles this: adding up the lines to produce a different figure would make Reality the
  author of a number somebody else stated.
- Q: Should recording a credit note post it automatically? → A: No. An invoice is recorded and
  posted as two acts and a credit note is the same. The distance between the two is a real
  business fact — the paperwork exists and the money has not moved — and collapsing it would
  hide exactly one of the conditions this feature exists to show.
- Q: Should `returned_not_credited` require a posted credit? → A: No. It measures whether the
  goods that came back have been credited on paper, which is a real question with a real
  answer. Making it also mean "and the money moved" would give one class two jobs. The money
  gets its own classes, and the quantity class says in its guidance what it does not cover.
- Q: Two new classes rather than one? → A: Yes, because two different people act. A credit note
  nobody posted is bookkeeping that has not happened; a posted credit nobody settled is money
  the company owes and has not moved. One class covering both would tell neither owner what to
  do.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Owe the Money (Priority: P1)

Somebody records a credit note for returned goods and posts it, and the company's books show
that it owes the customer.

**Why this priority**: A company using Reality cannot record a credit at all today through any
surface it has, and cannot express owing a customer anything.

**Independent Test**: Post a credit note against a fully paid invoice and verify the receivable
for that customer is negative by the credit note's stated total.

**Acceptance Scenarios**:

1. **Given** a recorded credit note, **When** it is posted, **Then** the ledger carries the
   exact reverse of a sales invoice posting for the credit note's stated total, and the entries
   balance.
2. **Given** an invoice the customer has already paid in full, **When** a credit note for that
   customer is posted, **Then** it is accepted and the customer's receivable becomes negative.
3. **Given** the same credit note, **When** it is posted a second time, **Then** it is refused.
4. **Given** a document that is not a credit note, **When** it is posted this way, **Then** it
   is refused.
5. **Given** a credit note whose stated total is zero, **When** it is posted, **Then** it is
   refused, because no money moves.

### User Story 2 - Settle It, One Way or the Other (Priority: P1)

Somebody either nets the credit against an invoice the customer still owes, or refunds it.

**Why this priority**: A credit that is never settled is an obligation the company carries
forever, and the two ways of settling it are how every trading business actually works.

**Acceptance Scenarios**:

1. **Given** a posted credit note and an open invoice for the same customer, **When** the
   credit is allocated against that invoice, **Then** the invoice's open amount falls by the
   allocated amount.
2. **Given** a posted credit note, **When** the customer is refunded, **Then** cash leaves, the
   receivable returns to zero and the credit note is settled.
3. **Given** a credit note settled in full, **When** more is allocated or refunded against it,
   **Then** it is refused.
4. **Given** a refund larger than the credit note it settles, **When** it is recorded, **Then**
   it is refused.

### User Story 3 - See the Credit Nobody Booked (Priority: P1)

An operator sees credit notes recorded and never posted for longer than this company normally
takes.

**Acceptance Scenarios**:

1. **Given** a company that normally posts credit notes within days and one recorded months ago
   and never posted, **When** the queue is listed, **Then** one entry appears with its total,
   its age and the norm.
2. **Given** the same credit note, **When** it is posted, **Then** the entry disappears without
   any manual step.
3. **Given** a credit note recorded yesterday, **When** the queue is listed, **Then** no entry
   appears.
4. **Given** a company with too few posted credit notes to claim a norm, **When** the queue is
   listed, **Then** no entry appears.

### User Story 4 - See the Money Still Owed (Priority: P1)

An operator sees posted credit notes that have neither been netted nor refunded, with what is
still outstanding.

**Why this priority**: It is money the company's own books say it owes a customer, and nothing
looks at it today — the existing unmatched-money class only considers postings that moved cash.

**Acceptance Scenarios**:

1. **Given** a posted credit note that has been neither allocated nor refunded, **When** the
   queue is listed, **Then** one entry appears with the amount still owed.
2. **Given** the same credit note allocated in part, **When** the queue is listed, **Then** the
   entry reports only the remainder.
3. **Given** the remainder refunded, **When** the queue is listed, **Then** the entry
   disappears without any manual step.

### Edge Cases

- A credit note in a currency other than the customer's other documents.
- A credit note for a party that is not a customer.
- A posted credit note whose posting group is later reversed.
- A refund recorded for a credit note of another tenant.
- A credit note allocated against an invoice of a different customer.
- A credit note recorded before the invoice it relates to.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST post a recorded credit note as the exact reverse of a sales
  invoice posting, for the total the credit note states, without requiring any invoice to
  exist.
- **FR-002**: The amount posted MUST be the total stated on the credit note and MUST NOT be
  derived from its lines.
- **FR-003**: Posting MUST be refused for a document that is not a credit note, for a credit
  note already posted, and for a stated total of zero or less.
- **FR-004**: A posted credit note MUST be settleable by allocation against an open invoice of
  the same customer and currency, through the settlement relation payments already use.
- **FR-005**: The system MUST record a customer refund as the mirror of the customer payment it
  already records, and MUST settle it against the credit note it repays.
- **FR-006**: Settling MUST be refused where it would exceed what the credit note still owes,
  where the currency differs, or where the party differs.
- **FR-007**: Both postings MUST be reachable through the JSON API and the agent tool catalog,
  as every other posting is.
- **FR-008**: The system MUST report one entry for every credit note recorded and not posted
  whose age exceeds a threshold learned from this company's own posted credit notes.
- **FR-009**: The system MUST report one entry for every posted credit note with an amount
  still neither allocated nor refunded.
- **FR-010**: Every learned threshold MUST use the established rule: the median of the most
  recent completed cases, a product multiple, an absolute floor, and a minimum history below
  which nothing is claimed and nothing reported.
- **FR-011**: Each entry MUST state the figures it compares — the total, what is settled, what
  remains, and for the unposted class the age and the threshold.
- **FR-012**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace, in
  the same shape as every existing class.
- **FR-013**: Each entry MUST disappear as soon as its condition ends, without acknowledgement
  or any other manual step.
- **FR-014**: The explanation of an entry MUST re-derive the current condition, and a
  malformed, unknown, cleared or foreign identity MUST produce the same not-found response the
  queue already returns.
- **FR-015**: Both classes MUST be declared in the closed catalog with an authority reference,
  named executable evidence, and the description, owner and clearing path every class carries.
- **FR-016**: Every surface that consumes the queue MUST receive both classes through the
  existing shared list and explanation contract.
- **FR-017**: The queue MUST remain deterministically ordered for identical data.
- **FR-018**: `returned_not_credited`'s guidance MUST say that it reports whether goods were
  credited on paper rather than whether money moved, and MUST name the classes that answer the
  second question.

### Domain and Traceability Requirements

- **DR-001**: No schema changes. A credit note is already a Document with lines, and the ledger
  entries, posting groups and settlement relation it needs already exist.
- **DR-002**: Both classes MUST be derived at read time from Documents, LedgerEntries and
  settlement allocations the tenant already owns, and MUST store nothing.
- **DR-003**: The posted amount MUST be the received total, never a sum over lines, which
  Constitution principle VIII requires.
- **DR-004**: What an invoice still owes MUST keep coming from the one settlement derivation,
  so an allocated credit reduces it the same way a payment does and no consumer can disagree.
- **DR-005**: A credit note MUST NOT gain a status. Whether it is posted, allocated or refunded
  is derived from whether those records exist.
- **DR-006**: Traces MUST reach their records by opaque identity and MUST NOT restate business
  fields.
- **DR-007**: Every read, derivation, validation and explanation MUST be tenant-scoped,
  including the norm.
- **DR-008**: No cause is introduced; the closed cause vocabulary is untouched.
- **DR-009**: The existing amount-and-invoice credit operation MUST NOT remain as a second way
  to reduce a receivable. One shape, one path.

### Key Entities *(when data is involved)*

- **Document (`credit_note`)**: What is credited, in quantities on its lines and in money on
  its header, and which now posts and is settled.
- **Document (`customer_refund`)**: Money going back, the mirror of the customer payment.
- **LedgerEntry and SettlementAllocation**: The postings and the relation that links a credit
  to whatever settles it.

## Success Criteria *(mandatory)*

- **SC-001**: A company can record, post and settle a credit through surfaces it actually has.
- **SC-002**: A credit against an invoice the customer already paid is expressible, which is
  the ordinary consumer return.
- **SC-003**: A credit reduces an invoice through the same derivation a payment does.
- **SC-004**: A credit promised on paper and never booked, and one booked and never given back,
  are both visible.
- **SC-005**: An operator reading `returned_not_credited` is told what it does not cover.
- **SC-006**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-007**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- Spec 079 is in place, so a credit note carries lines naming what they credit.
- Spec 080's learned-threshold helper is in place and is the right shape for another use.
- Spec 077 made a stated total mandatory on every recorded document, so a credit note always
  has one to post.
- Credit notes are low-volume in most businesses. The learned norm needs a minimum history, so a
  company issuing a handful a year may never be judged by the unposted class — named in the
  plan's review risks. The unsettled class needs no history and does not share that weakness.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1, 2 | credit posting test |
| FR-002 | US1 scenario 1 | stated-total test |
| FR-003 | US1 scenarios 3, 4, 5 | posting refusal test |
| FR-004 | US2 scenario 1 | allocation test |
| FR-005 | US2 scenario 2 | refund test |
| FR-006 | US2 scenarios 3, 4; Edge cases | settlement refusal test |
| FR-007 | US1 scenario 1 | API and tool contract test |
| FR-008 | US3 scenarios 1, 3 | unposted derivation test |
| FR-009 | US4 scenarios 1, 2 | unsettled derivation test |
| FR-010 | US3 scenario 4 | learned norm test |
| FR-011 | US3 scenario 1; US4 scenario 1 | causal values test |
| FR-012 | US4 scenario 1 | entry shape and trace test |
| FR-013 | US3 scenario 2; US4 scenario 3 | clearing test per class |
| FR-014 | Edge cases | explanation not-found parity test |
| FR-015 | US4 scenario 1 | catalog coverage and guidance gate test |
| FR-016 | US4 scenario 1 | shared list and explanation contract test |
| FR-017 | US4 scenario 1 | deterministic ordering test |
| FR-018 | — | catalog guidance assertion |
| DR-001 | — | no migration added |
| DR-002 | US4 scenario 3 | read-time derivation test |
| DR-003 | US1 scenario 1 | stated-total test |
| DR-004 | US2 scenario 1 | shared settlement path test |
| DR-005 | US3 scenario 2 | no-status test |
| DR-006 | US4 scenario 1 | opaque trace test |
| DR-007 | Edge cases | tenant isolation test |
| DR-008 | US4 scenario 1 | existing cause-vocabulary drift gate |
| DR-009 | — | the old operation is gone and the demo uses the new one |
