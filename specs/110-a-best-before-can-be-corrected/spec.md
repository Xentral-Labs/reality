# Feature Specification: A Best-Before Can Be Corrected

**Feature Branch**: `110-a-best-before-can-be-corrected`
**Created**: 2026-09-08
**Status**: Draft
**Language**: English
**Input**: "A stated best-before cannot be corrected. A typo is stuck until somebody builds the append-only restatement Spec 093 built for promises."

## Context and Intent

### Problem

Spec 109 refused to overwrite a stated best-before date, and the refusal was right: a date read off
the goods is a received value, and two different dates for one lot means one of them is wrong in a
way the product cannot adjudicate.

What it left behind is a **stuck typo**. Somebody reads `2026-10-16` as `2026-10-15`, states it,
and there is no way back. The consequences are not cosmetic:

- A day early, and `stock_expired` reports good stock as expired. Somebody writes off goods that
  were fine.
- A day late, and expired stock is not reported at all. It looks sellable, and the customer finds
  out.

Meanwhile the same product corrects a movement and corrects the lines of a manual document. A
mistyped date on a lot was the one recorded mistake with no way out.

### What kind of change this is

Worth settling before designing anything, because the answer decides the shape.

Spec 093 built an append-only record for a **revision**, and said so in its own words: *"This is
not a correction. A correction says the record was wrong; this says the record was right and the
world moved."* A counterparty restating a delivery date is the world moving. A best-before is not
like that — **the date printed on the goods does not change.** A different date means the reading
was wrong.

So this is a correction, and this product already has a shape for corrections: mutate the value,
require somebody to say what they believe they are replacing, require a reason, and put the before
and the after in a business event. `correct_movement` and `correct_manual_document_lines` both
work that way, and the second one corrects a value in place with its audit carried by the event.

### Scope

- Correct a stated best-before to another date, or to none, with a reason.
- Require the caller to say what they believe is currently stated, so a correction is something
  somebody looked at.
- Make the refusal that sends them here say where to go.

### Non-Goals

- **An append-only statements table.** It is the shape Spec 093 used and the wrong one here: this
  is a correction rather than a restatement, and the product audits corrections through business
  events. A table for the history of one scalar would also be the first place in this product where
  a *correction* got its own record, which is a bigger decision than a typo deserves.
- **Loosening `state_lot_expiry`.** It goes on refusing a different date. That refusal is the whole
  reason a correction has to cost a reason and a confirmation, and if stating quietly overwrote
  nothing here would be worth building.
- **Correcting anything else about a lot.** The number identifies the batch and is what movements
  and reservations were recorded against; changing it would be changing which goods they concerned.
  Out of scope, and not obviously ever in scope.
- **Deciding whether the new date is right.** Reality records that somebody said the first reading
  was wrong and what they now say instead. It cannot know which label was misread.
- **Refusing a correction because the lot came from a source record.** Considered, because
  `correct_manual_document_lines` refuses exactly that for a document. Rejected: a lot's source
  record says where the *lot* came from, and no import path creates lots at all — `create_lot` is
  reached only from the tool, the API and the command line, each of which may attach a source
  record itself. The date is stated by whoever calls the operation either way, so conflating the
  two would refuse a correction to a hand-typed date because the batch arrived by import.

### Existing Contracts

- [`specs/109-a-lot-can-expire/spec.md`](../109-a-lot-can-expire/spec.md) — the refusal this
  answers
- [`specs/093-promises-can-be-revised/spec.md`](../093-promises-can-be-revised/spec.md) — the
  restatement shape, and its own distinction between a revision and a correction
- [`specs/023-auditable-movement-corrections/spec.md`](../023-auditable-movement-corrections/spec.md)
- [`docs/features/inventory.md`](../../docs/features/inventory.md)
- [Constitution](../../.specify/memory/constitution.md), principles II and VIII

## Clarifications

### Session 2026-09-08

- Q: A revision or a correction? → A: A correction. The date printed on the goods does not change,
  so a different date means the reading was wrong — which is exactly the line Spec 093 drew when
  it said its own record was *not* a correction.
- Q: Where does the history live? → A: In the business event, with the before and the after, as
  `document.corrected` already does for a manual document's lines. A table for one scalar's history
  would be the first correction record in this product, which a typo does not justify.
- Q: What does a correction have to cost? → A: A stated reason, and the date the caller believes is
  currently stated. The second is the same shape as the confirmed count of Spec 085, the confirmed
  total of Spec 098 and the expected revision of a document correction: a correction confirms what
  it replaces, so it cannot be made by somebody who has not looked.
- Q: Can a correction remove the date? → A: Yes, with a reason. A date read off the wrong label on
  an item that has no shelf life is a real mistake, and the only honest fix is to say the lot has
  no date. What it cannot do is leave the record indistinguishable from one nobody ever stated —
  the event history is where that distinction lives, and this is stated as a limit.
- Q: What if the correction changes nothing? → A: Refused. A correction that corrects nothing is a
  claim about nothing, the same call Spec 097 made about a revision that restates nothing.
- Q: Does `state_lot_expiry` change? → A: Only its refusal message, which now names the correction.
  A refusal that does not say where to go is how a stuck typo stays stuck.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The Misread Label (Priority: P1)

Somebody read the fifteenth and the goods say the sixteenth. They correct it, saying what they
thought it was and why.

**Why this priority**: It is the whole gap, and both directions of getting it wrong cost real money.

**Independent Test**: State a date, correct it, and read the lot and the events.

**Acceptance Scenarios**:

1. **Given** a lot with a stated best-before, **When** it is corrected to another date with the
   currently stated date and a reason, **Then** the lot carries the new date.
2. **Given** that correction, **When** the business events are read, **Then** one event carries the
   date before, the date after and the reason.
3. **Given** a correction with no reason, **When** it is attempted, **Then** it is refused.
4. **Given** a correction that names a date other than the one stored, **When** it is attempted,
   **Then** it is refused and nothing changes.
5. **Given** a correction to the date already stored, **When** it is attempted, **Then** it is
   refused, because a correction that changes nothing is a claim about nothing.

### User Story 2 - The Wrong Label Entirely (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a lot whose stated date was read off the wrong label, **When** it is corrected to no
   date with a reason, **Then** the lot has no best-before and nothing is asserted about its expiry.
2. **Given** a lot with no date, **When** a date is corrected in without naming that there was
   none, **Then** it is refused.
3. **Given** a lot with no date, **When** a date is corrected in and the absence is named, **Then**
   it is recorded.

### User Story 3 - The Queue Follows The Correction (Priority: P1)

**Acceptance Scenarios**:

1. **Given** stock reported as expired, **When** the date is corrected to one still ahead, **Then**
   the entry is gone with nothing stored and no manual step.
2. **Given** stock not reported, **When** the date is corrected to one already passed, **Then** it
   is reported.
3. **Given** the refusal from stating a different date, **When** an operator reads it, **Then** it
   names the correction as the way to change a stated date.

### Edge Cases

- A correction on a lot of another tenant.
- A correction naming an unreadable date.
- A correction naming an unreadable expected date.
- Two corrections in a row, each confirming what the last one wrote.
- A correction on a lot with stock already written off because of the wrong date.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A stated best-before MUST be correctable to another calendar date, or to none.
- **FR-002**: A correction MUST require a stated reason, and MUST refuse an empty one.
- **FR-003**: A correction MUST require the caller to name the date currently stated, including
  naming that none is stated, and MUST refuse when that does not match what is stored.
- **FR-004**: A correction that would leave the stated date unchanged MUST be refused.
- **FR-005**: An unreadable date, in either the new value or the named current one, MUST be refused.
- **FR-006**: One business event MUST carry the date before, the date after and the reason.
- **FR-007**: `state_lot_expiry` MUST go on refusing a different date, and its refusal MUST name
  the correction.
- **FR-008**: The operational exception queue MUST follow the corrected date on the next read, with
  nothing stored and no manual step.
- **FR-009**: Nothing about a lot other than its best-before may be corrected by this operation.
- **FR-010**: Every existing class, operation, register and projection MUST behave exactly as it
  does today for a lot nobody corrects.

### Domain and Traceability Requirements

- **DR-001**: No migration. No field is added and no table is created.
- **DR-002**: The audit MUST be carried by a business event, as a manual document's line correction
  already is, and MUST NOT be a new record type.
- **DR-003**: No operational exception class or cause is added.
- **DR-004**: Whether the corrected date is right MUST NOT be judged; only that somebody said the
  first reading was wrong and what they say instead.
- **DR-005**: Every read and write MUST be tenant-scoped.
- **DR-006**: The new date MUST be recorded exactly as stated and MUST NOT be derived or adjusted.

### Key Entities *(when data is involved)*

- **Lot**: unchanged. Its best-before becomes correctable rather than only statable.
- **BusinessEvent**: carries the before, the after and the reason. No new record type.

## Success Criteria *(mandatory)*

- **SC-001**: A misread label is fixable, and the fix costs a reason and a look.
- **SC-002**: What the date said before, what it says now and why is readable afterwards.
- **SC-003**: A correction cannot be made by somebody who has not looked at what they are
  replacing.
- **SC-004**: Stating a date still refuses to overwrite one, and says where to go instead.
- **SC-005**: The queue follows the corrected date without anything being stored.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- A lot corrected to no date is indistinguishable in the record from one nobody ever stated. The
  event history is where that distinction lives, and that is a stated limit.
- Reality cannot know which label was misread. It records that somebody said so.
- A lot's number stays as it is. Correcting it would change which goods the movements against it
  concerned.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1; US2 scenarios 1, 3 | correction tests |
| FR-002 | US1 scenario 3 | reason required test |
| FR-003 | US1 scenario 4; US2 scenario 2 | confirmation test |
| FR-004 | US1 scenario 5 | unchanged correction refused test |
| FR-005 | Edge cases | unreadable date refused test |
| FR-006 | US1 scenario 2 | event test |
| FR-007 | US3 scenario 3 | the refusal message test |
| FR-008 | US3 scenarios 1, 2 | derivation test, both directions |
| FR-009 | — | the operation's own surface |
| FR-010 | — | the existing suites, unchanged |
| DR-001 | — | no migration in the diff |
| DR-002 | US1 scenario 2 | event test; no new model |
| DR-003 | — | the closed registry test |
| DR-004 | US1 scenario 1 | nothing judged test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US1 scenario 1 | recorded-dates-only test |
