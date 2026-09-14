# Feature Specification: A Fee Is a Charge, Not a Smaller Credit

**Feature Branch**: `095-a-fee-is-a-charge`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "A restocking fee recorded as a reduced credit quantity leaves `returned_not_credited` reporting the difference for ever. Recorded as its own charge it clears. The model already does the right thing and nothing says which way is right."

## Context and Intent

### Problem

A customer returns ten and the company credits eight, keeping the value of two as a restocking
fee. `returned_not_credited` compares quantities, so it reports two uncredited — and nothing will
ever clear it, because nobody is going to credit those two.

That is a false entry of exactly the shape Spec 088 removed from `overdue_receivable`, where a
customer taking an agreed discount looked like a debt. This one has a different cause and a
different fix.

**The model already expresses a fee correctly.** Measured rather than assumed:

| How the fee is recorded | What the queue does |
|---|---|
| Credit note line for **8** naming the order line | reports 2 uncredited, for ever |
| Credit note line for **10** naming the order line, plus a **charge line** for the fee | clears, and the total is still the reduced amount |

The crediting comparison gathers lines by the order line they name. A charge line names none, so
it is not counted as credit for goods — which is right, because it is not.

So there is no defect in the derivation and no capability missing. There is a **recording trap**:
the natural-looking way to record a fee produces a permanent false entry, and nothing in the
product says so.

### Scope

- Pin the correct recording with a test, so it cannot silently break.
- Say in the class's own guidance which recording is right, what the other one does, and why the
  difference exists.

### Non-Goals

- **A way to declare part of a return uncreditable.** The charge line already is that: whether
  the reason is a restocking fee, damage or a write-off, the shape is the same — the goods came
  back and something was charged for them. Adding a second way to say it would leave two answers
  that could disagree.
- **Teaching the class about line types.** It counts what credits the order line, which is
  already the correct rule. Making it inspect a line's type would be a second rule about what
  counts as credit.
- **Validating that a company records fees the right way.** Reality records what somebody wrote
  down. A tenant recording the fee as a reduced quantity is describing a partial credit, and the
  queue is right to say so; the guidance is what makes that a choice rather than a surprise.
- **Changing any derivation.** Nothing about what the queue computes changes.

### Existing Contracts

- [`specs/079-returns-connect/spec.md`](../079-returns-connect/spec.md)
- [`specs/088-early-payment-discount/spec.md`](../088-early-payment-discount/spec.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [Constitution](../../.specify/memory/constitution.md), principle VI

## Clarifications

### Session 2026-09-06

- Q: Is this a defect? → A: No, and checking rather than assuming is the whole story. It looked
  like the Skonto false positive; it is a recording trap around behaviour that is already
  correct. Building a feature for it would have added a second way to say something the model
  already says.
- Q: Should the class distinguish a fee from an unmade credit? → A: It cannot and should not. A
  credit note line for eight says eight were credited. If a company means "ten credited, two
  charged", that is two facts and the document should carry two lines.
- Q: Does the same apply to damaged goods or a write-off? → A: Yes, identically. The goods came
  back and something was charged for them; the reason is a description on the charge, not a
  different shape.
- Q: Why is a guidance change worth a specification? → A: Because the guidance is what an
  operator reads to decide what a class means, and a class whose clearing path is ambiguous is
  the same failure as a class with none. The test is what stops the guidance becoming untrue.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A Fee Recorded as a Charge Clears the Return (Priority: P1)

A company that keeps a restocking fee records it as a charge, and the return stops being
reported.

**Why this priority**: It is the recording the product wants and nothing proves it works.

**Independent Test**: Return ten against an invoiced order line, credit ten with a charge line
for the fee, and read the queue.

**Acceptance Scenarios**:

1. **Given** ten returned and ten credited with a separate charge line, **When** the queue is
   read, **Then** nothing is reported for that line.
2. **Given** the same documents, **When** the credit note total is read, **Then** it is the
   reduced amount the customer actually receives.
3. **Given** ten returned and only eight credited, **When** the queue is read, **Then** two are
   reported as uncredited, because that is what the document says.

### User Story 2 - The Guidance Says Which Way Is Right (Priority: P1)

An operator reading the class learns how to record a fee before recording it the other way.

**Acceptance Scenarios**:

1. **Given** the class guidance, **When** it is read, **Then** it says a fee is a charge line and
   what a reduced credit quantity means instead.

### Edge Cases

- A charge line that names the order line anyway.
- A fee larger than the credit.
- A return credited in two notes, one of which carries the charge.

## Requirements *(mandatory)*

- **FR-001**: A return credited in full with a separate charge line MUST NOT be reported as
  uncredited.
- **FR-002**: A return credited for fewer units MUST be reported as uncredited for the
  difference, because that is what the document states.
- **FR-003**: A charge line that names no order line MUST NOT count as credit for goods.
- **FR-004**: The class guidance MUST say that a fee, a damage deduction or a write-off is
  recorded as a charge line beside a full credit, and MUST say what recording a smaller credit
  quantity means instead.
- **FR-005**: No derivation, service or schema may change.

### Domain and Traceability Requirements

- **DR-001**: No schema changes, no service changes and no derivation changes.
- **DR-002**: The correct recording MUST be pinned by an executable test, so the guidance cannot
  become untrue without the suite saying so.
- **DR-003**: No operational exception class or cause is added.

### Key Entities *(when data is involved)*

- **DocumentLine**: The credit line that names an order line, and the charge line that names
  none.

## Success Criteria *(mandatory)*

- **SC-001**: A company keeping a restocking fee can record it without a permanent false entry.
- **SC-002**: The right recording is written where an operator reads about the class.
- **SC-003**: Both recordings are pinned by tests, so neither behaviour can drift unnoticed.
- **SC-004**: Nothing the queue computes changes.
- **SC-005**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- A company that records a fee as a reduced credit quantity gets a true statement about its own
  document and a permanent entry. Guidance is the only thing that helps, because Reality cannot
  know what was meant.
- The same shape covers a restocking fee, a damage deduction and a write-off. If those ever need
  telling apart, it is the charge that should say which, not the credit.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1, 2 | fee as a charge test |
| FR-002 | US1 scenario 3 | reduced credit test |
| FR-003 | US1 scenario 1 | charge line not counted test |
| FR-004 | US2 scenario 1 | guidance content test |
| FR-005 | — | no diff under `services/` |
| DR-001 | — | no migration, no service diff |
| DR-002 | US1 scenarios 1, 3 | both recordings pinned |
| DR-003 | — | the closed registry expectation, unchanged |
