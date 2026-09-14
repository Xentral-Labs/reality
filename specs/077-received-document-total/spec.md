# Feature Specification: A Document's Amounts Are Received, Not Computed

**Feature Branch**: `077-received-document-total`
**Created**: 2026-09-05
**Status**: Draft
**Language**: English
**Input**: "Reality should always receive values and never calculate them, because otherwise rounding starts."

## Context and Intent

### Problem

Reality computes the one figure a document is most often judged by. When a manual document
is recorded without a total, the total is produced by adding up its lines and stored on the
header as though it had been stated. Every caller in the product does exactly that: the
manual order operation never supplies a total, the document endpoint accepts one and the
interface never sends it, and the field exists as an optional parameter nobody uses.

It happens twice. A line without a stated amount gets one from its quantity times its
unit price, and the header then adds those up. Both figures are money, both are stored, and
neither was stated by anybody.

Nothing is wrong with the arithmetic. What is wrong is who owns it. The moment Reality adds
up lines, it owns a rounding rule, and that rule will differ from the rule of whatever
produced the document being recorded. Typing a supplier's invoice into the system then
produces a total that quietly disagrees with the total printed on the paper, and the
disagreement is invisible precisely where it matters — the figure the ledger posts.

This is now settled policy rather than an opinion. Constitution 1.2.0 states that a value a
source states is recorded as received and never recalculated, and that a derivation may not
be stored as a new authority. A document total is stored, and the ledger posts it.

### Scope

- Require the amount on every line and the total on the header when a document is
  recorded, at every entry point.
- Move the convenience of adding up lines to the interface, where the sum is offered to a
  person, shown, and can be corrected before it is sent.
- Require the total from the agent tool that creates an order, so an agent takes it from
  whatever it is reading rather than leaving the core to invent one.

### Non-Goals

- Validating the total against the sum of the lines. A difference is exactly what this
  change makes visible; refusing it would hide the case again and would re-introduce our
  rounding as the arbiter.
- Any other computed value. Stock, outstanding amounts and derived exceptions are
  observations over recorded facts and are untouched.
- Tax, discounts, or any figure the product does not hold today.
- Source adapters. The Shopify adapter records the order total the payload states, but
  produces each line's amount from quantity times price because that payload states no line
  total. Fixing it means deciding what Reality holds when a source is silent, which is a
  question about sources rather than about the write path this feature owns.
- Changing what the ledger posts. It still posts the document's total; that total is now
  one somebody stated.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md), principle VIII
- [`AGENTS.md`](../../AGENTS.md), hard rule 11
- [`specs/006-documents-evidence/spec.md`](../006-documents-evidence/spec.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)

## Clarifications

### Session 2026-09-05

- Q: Manual documents have no external source. Is computing their total a violation? → A:
  Yes as written, and harmlessly so only while the document represents nothing external. As
  soon as somebody types in a supplier's invoice there is a second total, and the rule has
  to hold for the case that matters.
- Q: Does requiring the total mean double entry? → A: No. The interface adds the lines up
  and offers the result in the field, where a person sees and confirms it. The computation
  happens at the edge under human eyes instead of invisibly in the core.
- Q: Why require it from the agent tool as well? → A: Because an agent creating an order is
  reading something — a mail, an attachment, a conversation — and the total should come from
  there. Leaving it optional would put the core back in charge of inventing it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Type an Invoice and See a Difference (Priority: P1)

Somebody records a supplier's invoice. The interface adds up the lines and offers the sum;
the paper says something else; they enter what the paper says and the difference is now in
the system rather than smoothed away.

**Why this priority**: It is the case the principle exists for.

**Independent Test**: Record a document whose stated total differs from the sum of its
lines and verify the stated total is what is stored and posted.

**Acceptance Scenarios**:

1. **Given** a document recorded with a total that differs from the sum of its lines,
   **When** it is stored, **Then** the stated total is kept unchanged and nothing
   recalculates it.
2. **Given** a document recorded without a total, **When** it is stored, **Then** it is
   refused, naming the missing total.
3. **Given** the interface with lines entered, **When** the total field is shown, **Then**
   it already contains the sum of those lines and can be edited before sending.

### User Story 2 - Create an Order Through the Agent Tool (Priority: P2)

An agent proposing an order supplies the total from what it is reading, and is refused if
it does not.

**Why this priority**: It closes the last entry point; leaving it open would keep the core
computing for the caller that most often has a source to read from.

**Acceptance Scenarios**:

1. **Given** an order proposal without a total, **When** it is validated, **Then** it is
   refused before anything is created.
2. **Given** an order proposal with a total, **When** it is executed, **Then** the document
   carries exactly that total.

### Edge Cases

- A total or a line amount of zero, which is a statement and not an omission.
- A line amount that differs from quantity times unit price, which a rebate or a rounding
  convention on the source can produce.
- A negative total on a credit-style document.
- A total in a currency other than the lines' own.
- A document recorded with a total and later corrected line by line.

## Requirements *(mandatory)*

- **FR-001**: Recording a document MUST require a stated amount on every line and a stated
  total on the header, at every entry point that creates one.
- **FR-002**: Both MUST be stored exactly as given. A line amount MUST NOT be produced from
  quantity and unit price, and a header total MUST NOT be produced from the lines.
- **FR-003**: A document recorded without a total MUST be refused with a message naming
  what is missing.
- **FR-004**: A header total that differs from the sum of the lines, and a line amount that
  differs from quantity times unit price, MUST both be accepted. Those differences are the
  signal this change exists to preserve.
- **FR-005**: A total of zero MUST be treated as a statement and not as an omission.
- **FR-006**: The interface MUST offer a suggestion for every amount it asks for — quantity
  times unit price on each line, and the sum of the lines on the header — and MUST allow
  each to be changed before the document is sent.
- **FR-007**: The agent tool that creates an order MUST require the total in its schema, so
  a proposal without one is refused before execution.

### Domain and Traceability Requirements

- **DR-001**: The total is Evidence stated by whoever recorded the document. Reality stores
  it and does not become its author.
- **DR-002**: No derivation over recorded facts is affected. Stock, outstanding amounts and
  operational exceptions remain observations and are untouched.
- **DR-003**: The ledger continues to post the document's total; what changes is only where
  that number came from.

## Success Criteria *(mandatory)*

- **SC-001**: No money figure on a document, on a line or on its header, is produced by
  the core.
- **SC-002**: A person recording a document types a total once, prefilled, and can correct
  it.
- **SC-003**: A stated total that differs from the sum of the lines survives unchanged.
- **SC-004**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- Constitution 1.2.0 is in force. This feature is the first correction made under it and
  the only violation its impact review found.
- Adding up lines in the interface is presentation, not authority: the number becomes real
  only when a person sends it.
- Existing callers inside the repository — tests and demo scenarios — state a total from
  now on. There is no production data to migrate and no stored value changes.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 2; US2 scenario 1 | required-total test per entry point |
| FR-002 | US1 scenario 1 | stated-total persistence test |
| FR-003 | US1 scenario 2 | refusal message test |
| FR-004 | US1 scenario 1 | differing-total acceptance test |
| FR-005 | Edge cases | zero-amount test |
| FR-006 | US1 scenario 3 | interface prefill review |
| FR-007 | US2 scenarios 1, 2 | tool schema test |
| DR-001 | US1 scenario 1 | stated-total persistence test |
| DR-002 | US1 scenario 1 | unchanged derivation suite |
| DR-003 | US1 scenario 1 | posting uses the stated total test |
