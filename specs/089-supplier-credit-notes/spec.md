# Feature Specification: The Credit That Comes the Other Way

**Feature Branch**: `089-supplier-credit-notes`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "A supplier sends a credit note and Reality has nowhere to put it. The payable stays at its full amount, the money is chased or paid twice, and the queue that reports a credit nobody booked only knows about the ones the company writes itself."

## Context and Intent

### Problem

Spec 084 gave a credit note a life: it posts as the reverse of an invoice, it nets against what
a customer owes, and where the customer has already paid it is refunded instead. Every part of
that was built on the selling side only.

The buying side has none of it. A supplier sends a credit — for goods returned, for a price
correction, for damage, for a rebate agreed at quarter end — and there is nowhere in Reality it
can go. `SETTLEMENT_CONTROL` knows four settleable documents and none of them is a supplier
credit. The consequences are all money:

- **The payable stays at its full amount.** The company owes less than its own books say, and
  the aging register, `overdue_payable` and every payment run built on them are wrong by the
  credit.
- **The credit is worth nothing until somebody remembers it.** An unclaimed supplier credit is
  working capital sitting with the supplier, and no queue mentions it, because
  `credit_note_unsettled` only ever looks at credits the company wrote itself.
- **A credit against an invoice already paid cannot be expressed at all** — the same hole
  Spec 084 found on the selling side, in the other direction. The company's money is with the
  supplier and the only way back is a refund nothing can record.

Nothing here is exotic. It is the ordinary arithmetic of buying things, and the model can
already do all of it in one direction.

### Scope

- A supplier credit note that posts as the exact reverse of a supplier invoice.
- Netting one against what the company still owes that supplier.
- A refund from a supplier, for a credit that cannot be netted because nothing is open.
- Two classes mirroring the two Spec 084 added: a supplier credit recorded and never booked,
  and a booked supplier credit nobody has claimed.

### Non-Goals

- **Returning goods to a supplier.** A `supplier_delivery` commitment accepts receipts only, so
  a physical return to a supplier cannot be recorded at all today. That is the mirror of specs
  079 and 082 and it is a separate piece of work; this feature is the money half, which is also
  the half that applies to a price correction, an allowance or a rebate, where no goods move at
  all.
- **A supplier credit line naming a purchase order line.** The link exists and the quantity
  classes on the buying side do not read it, because there is no returned quantity on that side
  to compare it against. Building the comparison without the goods half would produce a class
  that is right only by accident.
- **Deciding what a credit is for.** Reality records that a supplier credited an amount, not
  whether it was for damage, a rebate or a mistake. That is a reason a source may carry and
  Reality does not adjudicate.
- **Anything the selling side does not already do.** This is a mirror. Where the two sides could
  differ, they do not, and the reason is in the plan rather than in the code.

### Existing Contracts

- [`specs/084-credit-note-posts/spec.md`](../084-credit-note-posts/spec.md)
- [`docs/features/ledger.md`](../../docs/features/ledger.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/features/procure_to_pay.md`](../../docs/features/procure_to_pay.md)
- [Constitution](../../.specify/memory/constitution.md), principles III and VIII

## Clarifications

### Session 2026-09-06

- Q: Does a supplier credit need the goods half first? → A: No, and waiting for it would be
  wrong. A credit for a price correction, an allowance or a rebate involves no movement at all,
  and those are the common cases. Where goods did go back, the money half is still the half that
  changes what the company owes.
- Q: Should a supplier credit note settle without a supplier invoice? → A: Yes, exactly as its
  mirror does. The claim exists whether or not anything is open, and a payable going the other
  way is the statement that the supplier owes this company — which is what happens when a credit
  arrives for an invoice already paid.
- Q: Netting or a refund? → A: Both, and through the one settlement relation, so a payable falls
  exactly as a payment makes it fall and nothing downstream needs telling that a credit was
  involved. Netting where something is open; a refund where nothing is.
- Q: Are the two new classes really the same conditions as the sales ones? → A: The same shape
  and different money. A credit the company wrote and never booked overstates what it is owed; a
  credit a supplier sent and nobody booked overstates what it owes, which is the direction in
  which a company pays twice. Unclaimed is the same both ways: money sitting with the other
  party that nobody is asking for.
- Q: Should the unbooked class reuse the threshold the selling side already learns? → A: No —
  the rule, not the number. That threshold is learned from credits the company wrote itself, and
  booking somebody else's credit note is a different process with a different owner. Sharing the
  number would let one side's rhythm judge the other, and would leave a company that issues no
  sales credits unable to judge its supplier credits at all. Spec 080 set the precedent: two
  classes may share the learned rule and share no statistic.
- Q: Why not one class covering both directions? → A: Because the owner and the exit differ. A
  credit the company owes is settled by its own accounts receivable; a credit a supplier owes is
  claimed from the supplier by accounts payable. One row for two different jobs would be a
  worklist nobody owns.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Take the Credit Off What Is Owed (Priority: P1)

A supplier credit note reduces what the company owes that supplier, without anybody adjusting a
figure by hand.

**Why this priority**: Until it does, the payable is wrong and every payment decision built on
it is wrong by the same amount.

**Independent Test**: Record and post a supplier invoice and a supplier credit note, net one
against the other, and read what is still open.

**Acceptance Scenarios**:

1. **Given** a posted supplier credit note, **When** it is netted against an open supplier
   invoice, **Then** what the company still owes falls by the credited amount.
2. **Given** a credit note posted for more than one invoice is worth, **When** it is netted
   against that invoice, **Then** the excess remains claimable and the invoice is settled.
3. **Given** a supplier invoice that was overdue, **When** a credit settles the last of it,
   **Then** it stops being reported as overdue.
4. **Given** a credit note and an invoice belonging to different suppliers, **When** netting is
   attempted, **Then** it is refused.
5. **Given** a credit note that has not been posted, **When** netting is attempted, **Then** it
   is refused.

### User Story 2 - Get the Money Back When Nothing Is Open (Priority: P1)

A credit arriving after the invoice was paid is claimed from the supplier as money, not left as
a note nobody can act on.

**Why this priority**: It is the case the selling side found and fixed, in the direction where
the company's own cash is the thing sitting with somebody else.

**Acceptance Scenarios**:

1. **Given** a fully paid supplier invoice and a posted supplier credit note, **When** the
   supplier refunds it, **Then** the credit is settled and nothing remains claimable.
2. **Given** a partly claimed credit note, **When** a refund larger than the remainder is
   recorded, **Then** it is refused.
3. **Given** a refund, **When** the ledger is read, **Then** cash has come in and what the
   company owes that supplier is unchanged in total.

### User Story 3 - See the Credits Nobody Has Acted On (Priority: P1)

An operator sees supplier credits that were recorded and never booked, and booked credits nobody
has claimed.

**Why this priority**: A credit that is not booked makes the company pay too much, and a credit
that is not claimed is its own money sitting with a supplier. Neither is visible today.

**Acceptance Scenarios**:

1. **Given** a supplier credit note recorded and never booked, standing longer than this company
   normally takes, **When** the queue is read, **Then** it is reported.
2. **Given** the same credit note booked, **When** the queue is read, **Then** it is no longer
   reported as unbooked.
3. **Given** a booked supplier credit note with nothing netted or refunded against it, **When**
   the queue is read, **Then** it is reported as unclaimed.
4. **Given** the same credit netted in full, **When** the queue is read, **Then** nothing is
   reported.
5. **Given** a credit note the company wrote itself, **When** the queue is read, **Then** it is
   reported by the selling-side classes and not by these.

### Edge Cases

- A supplier credit note for zero, and for a negative amount.
- Posting the same supplier credit note twice.
- Netting more than a credit note is worth, and more than an invoice still owes.
- Netting against a document that is not a supplier invoice.
- A refund for a credit note that was never posted.
- A supplier credit note and a customer credit note recorded on the same day.
- A reversed posting group behind a supplier credit note.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A supplier credit note MUST post as the exact reverse of a supplier invoice, and
  MUST be postable whether or not any supplier invoice is open.
- **FR-002**: Posting the same supplier credit note twice MUST be refused, and an amount that is
  not above zero MUST be refused.
- **FR-003**: A posted supplier credit note MUST be settleable, through the same settlement
  relation every other settleable document uses.
- **FR-004**: A posted supplier credit note MUST be nettable against a supplier invoice of the
  same supplier, and MUST be refused against a document belonging to another party or of another
  type.
- **FR-005**: Netting MUST NOT exceed what the credit note is worth or what the invoice still
  owes, and the remainder of either MUST stay open.
- **FR-006**: A refund from a supplier MUST be recordable as money arriving, and MUST settle the
  credit note it belongs to.
- **FR-007**: A refund MUST NOT exceed what the credit note still claims.
- **FR-008**: What a supplier invoice still owes MUST fall by every credit netted against it, so
  that the aging register and every class built on it agree without being told a credit was
  involved.
- **FR-009**: The system MUST report a supplier credit note recorded and never booked, judged
  against the rhythm this company has shown for booking supplier credits rather than against a
  configured interval.
- **FR-009a**: That rhythm MUST be learned from supplier credits alone. The rule is shared with
  the selling side; the history MUST NOT be, because booking a credit a supplier sent is a
  different process from booking one the company wrote, and one side's rhythm must not silence
  or accuse the other.
- **FR-010**: The system MUST report a booked supplier credit note that has been neither netted
  nor refunded, with no threshold, because the claim exists from the moment it is booked.
- **FR-011**: Those two classes MUST report only supplier credit notes, and the two selling-side
  classes MUST keep reporting only the company's own.
- **FR-012**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace, in
  the same shape as every existing class.
- **FR-013**: Each entry MUST disappear as soon as the condition ends, without acknowledgement
  or any other manual step.
- **FR-014**: The explanation of an entry MUST re-derive the current condition, and a malformed,
  unknown, cleared or foreign identity MUST produce the same not-found response the queue
  already returns.
- **FR-015**: The classes MUST be declared in the closed catalog with an authority reference,
  named executable evidence, and the description, owner and clearing path every class carries,
  and each MUST name its selling-side mirror.
- **FR-016**: Every new operation MUST be declared in the command catalog, the tenant isolation
  catalog and the capability guidance, and MUST be reachable from the surfaces that already
  reach the selling-side operations.
- **FR-017**: The queue MUST remain deterministically ordered for identical data.
- **FR-018**: Every existing class and operation MUST behave exactly as it does today.

### Domain and Traceability Requirements

- **DR-001**: No schema changes. A Document type is a string the model already accepts and the
  settlement relation already links any two control entries on opposite sides of one account.
- **DR-002**: Both classes MUST be derived at read time and MUST store nothing.
- **DR-003**: Settlement MUST go through the one existing allocation service; no second way of
  reducing a payable may appear.
- **DR-004**: Traces MUST reach their records by opaque identity and MUST NOT restate business
  fields already carried in causal values.
- **DR-005**: Every read, derivation, posting and explanation MUST be tenant-scoped.
- **DR-006**: No cause is introduced; the closed cause vocabulary is untouched.
- **DR-007**: Every figure posted MUST come from the document the tenant recorded; no amount may
  be derived, apportioned or rounded.

### Key Entities *(when data is involved)*

- **Document**: Gains two types it always could have carried — a supplier credit note and a
  supplier refund.
- **LedgerEntry** and **SettlementAllocation**: The existing postings and the existing relation,
  used unchanged.

## Success Criteria *(mandatory)*

- **SC-001**: A supplier credit reduces what the company owes without anybody adjusting a figure.
- **SC-002**: A credit arriving after the invoice was paid can be claimed as money.
- **SC-003**: A supplier credit that was never booked, and one nobody has claimed, are both
  visible.
- **SC-004**: The two sides of the business behave identically where nothing forces them apart.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- A supplier credit note is recorded in Reality because a supplier sent one. Reality does not
  raise one on the company's behalf and does not decide whether the supplier should have.
- The goods half of a supplier return remains unbuilt, so a credit for returned goods is
  recorded as money without any movement behind it. That is honest for a price correction and
  incomplete for a physical return, and it is named as the remaining gap rather than hidden.
- Both new classes are silent for a company whose suppliers never send credits.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1; US2 scenario 1 | posting test |
| FR-002 | Edge cases | double posting and amount test |
| FR-003 | US1 scenario 1 | settlement control test |
| FR-004 | US1 scenarios 4, 5 | wrong party and wrong type test |
| FR-005 | US1 scenario 2 | remainder test |
| FR-006 | US2 scenarios 1, 3 | refund test |
| FR-007 | US2 scenario 2 | refund ceiling test |
| FR-008 | US1 scenario 3 | payable falls test |
| FR-009 | US3 scenarios 1, 2 | unbooked derivation test |
| FR-009a | US3 scenario 5 | separate rhythm test |
| FR-010 | US3 scenarios 3, 4 | unclaimed derivation test |
| FR-011 | US3 scenario 5 | two sides stay apart test |
| FR-012 | US3 scenario 1 | entry shape and trace test |
| FR-013 | US3 scenarios 2, 4 | clearing test |
| FR-014 | Edge cases | explanation not-found parity test |
| FR-015 | US3 scenario 1 | catalog coverage and guidance gate test |
| FR-016 | US1 scenario 1 | catalog drift gates and surface tests |
| FR-017 | US3 scenario 3 | deterministic ordering test |
| FR-018 | — | the existing suites, unchanged |
| DR-001 | — | no migration added |
| DR-002 | US3 scenario 4 | read-time derivation test |
| DR-003 | US1 scenario 1 | one allocation service test |
| DR-004 | US3 scenario 1 | opaque trace test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US3 scenario 1 | existing cause-vocabulary drift gate |
| DR-007 | US1 scenario 1 | posted amounts equal recorded amounts test |
