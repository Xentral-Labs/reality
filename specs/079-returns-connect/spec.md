# Feature Specification: A Return May Say What It Reverses

**Feature Branch**: `079-returns-connect`
**Created**: 2026-09-05
**Status**: Draft
**Language**: English
**Input**: "Returns produce two wrong signals today. Close return-to-resolution the way Spec 076 closed invoicing."

## Context and Intent

### Problem

A return is the only movement Reality refuses to connect to anything.

`record_movement` accepts a `return`, and it accepts a `commitment_id`, and it will not
accept both together. The guard reads `expected = "shipment" if customer_delivery else
"receipt"`, so a return carrying the delivery commitment it reverses is rejected with
"Movement does not match the commitment." The only way to record goods coming back is
orphaned — no promise, no document, no line.

Two wrong signals follow, and both are live today. A plain return produces:

```
['shipped_not_billed', 'unexplained_movement']
```

The goods are back in the building and Reality still reports that they were delivered and
never invoiced, because `shipped_not_billed` counts shipments and nothing subtracts what came
back. And the return itself is reported as a movement nobody can explain — which is exactly
true and completely useless, because the model gave it no way to be explained.

The demo month demonstrates it: two units come back into the Returns Area on day 18 and
appear in the queue as an unexplained movement.

Nothing about the money is missing. `post_sales_credit` reduces a receivable against an
invoice and works. What is missing is the quantity story: how much came back, against what,
and whether it has been credited.

### Scope

- Let a `return` movement carry the customer-delivery Commitment it reverses.
- Let a credit note line say which order line it credits, using the reference Spec 076
  added.
- Subtract returns from the delivered quantity that `shipped_not_billed` measures, so goods
  that came back are no longer reported as unbilled.
- Report goods returned against an order line that no credit note line credits.
- Report a credited quantity larger than what has actually come back, where something has
  come back.
- Give both new classes the identity, severity, impact, causal values, trace, explanation,
  ordering, tenant isolation and operator guidance every existing class carries.

### Non-Goals

- Ledger postings for a credit note Document. Money is already handled: `post_sales_credit`
  reduces the receivable. This feature is about quantities, and a credit note here records
  what was credited in goods, not a second accounting path for the amount.
- Supplier returns. Goods going back to a supplier are the mirror flow with a different
  document, a different promise and a different owner. `credit_note` in this feature means a
  customer credit note.
- Announced returns and RMA numbers. A return that a customer has declared but not sent is a
  promise Reality cannot express — the commitment vocabulary has two types and neither is a
  return. Reporting a declared return as late needs that vocabulary first.
- Refund without return. A company that credits a customer and tells them to keep the goods
  is making a policy decision, not producing a discrepancy, and nothing is reported where
  nothing has come back.
- Restocking, inspection and scrapping. What happens to returned goods after they arrive is
  the next question and a separate feature.
- Netting returns into fulfilment. A kept promise stays kept; see the clarifications.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/features/movements.md`](../../docs/features/movements.md)
- [`specs/076-invoice-order-link/spec.md`](../076-invoice-order-link/spec.md)
- [`specs/009-inventory-execution/spec.md`](../009-inventory-execution/spec.md)
- [`specs/012-ledger-finance/spec.md`](../012-ledger-finance/spec.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-05

- Q: Should a return reduce the fulfilled quantity of the delivery commitment? → A: No, and
  this is the decision the whole feature turns on. Fulfilment answers "did the company keep
  its promise", and it did — the goods went out on time. Subtracting returns would reopen a
  kept promise as overdue and would make a returned order look undelivered. Returns are
  counted separately and subtracted only where the question is "how much did the customer
  keep", which is what billing and crediting are about.
- Q: Then what does `shipped_not_billed` measure after this? → A: Delivered minus returned.
  A customer who sent everything back owes nothing, so nothing is unbilled. That is a
  correction to a class that ships today, not a new behaviour.
- Q: What does a credit note line point at? → A: The order line, the same grain Spec 076
  chose. Everything then hangs off one line — invoice lines bill it, credit note lines credit
  it, its Commitment carries the movements — and the returns classes are the same comparison
  as the invoicing classes with different inputs.
- Q: Why report crediting beyond what came back only when something came back? → A: Because
  a refund with no return at all is ordinary, especially in consumer trade where "keep it"
  is a normal instruction. Once goods have started coming back, a credit larger than what
  arrived is a real difference. This is the same shape as `shipped_not_billed` saying nothing
  about a line with no delivery.
- Q: Can a customer return more than was shipped? → A: No. The write path refuses a return
  larger than what went out against that commitment, in the same way it already refuses a
  shipment larger than the promise.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record a Return Against What It Reverses (Priority: P1)

Somebody records goods coming back against the delivery they came from, and Reality stops
calling it unexplained.

**Why this priority**: Every return today produces a wrong signal, and no correct way to
record one exists.

**Independent Test**: Ship against a commitment, record a return against the same commitment,
verify it is accepted and no longer reported as unexplained.

**Acceptance Scenarios**:

1. **Given** goods shipped against a customer-delivery commitment, **When** a return is
   recorded against that commitment, **Then** it is accepted.
2. **Given** that return, **When** the queue is listed, **Then** no unexplained movement is
   reported for it.
3. **Given** a return larger than what was shipped against that commitment, **When** it is
   recorded, **Then** it is refused.
4. **Given** a return recorded against a supplier-delivery commitment, **When** it is
   recorded, **Then** it is refused, because goods returning to a supplier are a different
   flow.
5. **Given** the commitment behind that return, **When** its fulfilment is read, **Then** it
   is unchanged, because the promise was kept when the goods went out.

### User Story 2 - Stop Billing Goods That Came Back (Priority: P1)

An order line whose goods have been returned is no longer reported as shipped and unbilled.

**Why this priority**: It is a live wrong signal on a class that already ships.

**Acceptance Scenarios**:

1. **Given** an order line shipped in full and returned in full, **When** the queue is
   listed, **Then** no shipped-and-not-billed entry appears.
2. **Given** an order line shipped in full and returned in part, **When** the queue is
   listed, **Then** the entry reports only what the customer kept.
3. **Given** an order line billed for what the customer kept, **When** the queue is listed,
   **Then** no entry appears.

### User Story 3 - See Goods Back With No Credit (Priority: P1)

An operator sees order lines whose goods have come back and which no credit note line
credits, with the quantity returned, the quantity credited and the difference.

**Why this priority**: The customer has given the goods back and has not been given the
money back. It is the return-to-resolution equivalent of shipping without invoicing.

**Independent Test**: Return part of a delivered line, verify the difference is reported;
credit it and verify it clears.

**Acceptance Scenarios**:

1. **Given** goods returned against an order line and no credit note line crediting it,
   **When** the queue is listed, **Then** one entry appears with the returned quantity, zero
   credited, and the full difference.
2. **Given** the same line credited in part, **When** the queue is listed, **Then** the entry
   reports the difference.
3. **Given** the remainder credited, **When** the queue is listed, **Then** the entry
   disappears without any manual step.
4. **Given** an order line credited by two credit notes, **When** the queue is listed,
   **Then** both count towards the credited quantity.

### User Story 4 - See Money Back Without Goods Back (Priority: P2)

An operator sees order lines credited for more than has actually come back, where something
has come back.

**Why this priority**: It is money given away, and it only becomes a question once a return
is under way.

**Acceptance Scenarios**:

1. **Given** an order line where more is credited than has been returned, and something has
   been returned, **When** the queue is listed, **Then** one entry appears with both
   quantities and the difference.
2. **Given** an order line credited with nothing returned at all, **When** the queue is
   listed, **Then** no entry appears, because a refund without a return is a decision.
3. **Given** the outstanding goods arriving, **When** the queue is listed, **Then** the entry
   disappears.

### Edge Cases

- A return against a commitment whose order line was never billed.
- A credit note line referencing an order line on the purchase side.
- A credit note line in a different unit from the order line it credits.
- A return recorded, then corrected or voided through the existing movement correction, and
  a shipment voided the same way, which is reported as delivered today.
- An order line returned and credited by different quantities in the same read.
- A return against a cancelled commitment, which is accepted: the goods went out before the
  promise was cancelled and coming back does not depend on the promise still standing.
- A credit note line with no reference at all, which credits nothing from an order.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A `return` movement MUST be able to carry the customer-delivery Commitment it
  reverses.
- **FR-002**: A return MUST NOT be accepted against a supplier-delivery Commitment.
- **FR-003**: A return MUST NOT exceed the quantity shipped against that Commitment.
- **FR-004**: A return MUST NOT change the fulfilled or open quantity of the Commitment it
  carries, so a kept promise stays kept and no delivery class is affected.
- **FR-005**: A credit note line MUST be able to reference the order line it credits, using
  the existing billed-line reference, and that reference MUST be validated on the sales side.
- **FR-006**: The delivered quantity that `shipped_not_billed` measures MUST be reduced by
  what has been returned against the same Commitment.
- **FR-007**: The system MUST report one entry for every order line whose returned quantity
  exceeds the quantity credited against it by credit note lines.
- **FR-007a**: Only a quantity that was actually billed can require crediting. Where goods
  come back that no invoice line ever billed, nothing is reported, because the company never
  charged for them and owes nothing back.
- **FR-008**: The system MUST report one entry for every order line whose credited quantity
  exceeds the quantity returned against it, and only where some quantity has been returned.
- **FR-008a**: One order line MUST produce at most one of the two return entries. The
  comparisons are opposite directions of one difference and cannot both hold.
- **FR-009**: Credited quantities MUST be summed across every credit note line referencing
  the same order line, so partial and consolidated crediting behave correctly.
- **FR-010**: A quantity comparison MUST be made only between lines recorded in the same
  unit, as it is for the invoicing classes.
- **FR-011**: Returned quantities MUST come from the movements already linked through the
  order line's Commitment, not from a second count.
- **FR-011a**: Every movement quantity a class compares MUST exclude movements a correction
  has voided, through the same rule the service layer already applies to fulfilment. The
  operational exception queue does not apply that rule today, so a shipment recorded in error
  and voided is still reported as delivered and unbilled; this requirement corrects that as
  well as covering returns.
- **FR-012**: Each entry MUST state the two quantities it compares and their difference.
- **FR-013**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace, in
  the same shape as every existing class.
- **FR-014**: Each entry MUST disappear as soon as its condition ends, without
  acknowledgement or any other manual step.
- **FR-015**: The explanation of an entry MUST re-derive the current condition, and a
  malformed, unknown, cleared or foreign identity MUST produce the same not-found response the
  queue already returns.
- **FR-016**: Both classes MUST be declared in the closed catalog with an authority
  reference, named executable evidence, and the description, owner and clearing path every
  class carries.
- **FR-017**: Every surface that consumes the queue MUST receive both classes through the
  existing shared list and explanation contract.
- **FR-018**: The queue MUST remain deterministically ordered for identical data.

### Domain and Traceability Requirements

- **DR-001**: No schema changes. The Commitment link on a Movement exists, and the billed-line
  reference on a DocumentLine exists; this feature makes both usable where they are not.
- **DR-002**: Both classes MUST be derived at read time from existing tenant-owned Documents,
  DocumentLines, Commitments and Movements.
- **DR-003**: Returned and delivered quantities MUST reuse the existing path from an order
  line through its Commitment to its Movements, so a quantity is never counted two ways. One
  correction-aware helper MUST serve both the service layer and the exception queue, because
  two helpers with one of them ignoring corrections is exactly the divergence FR-011a
  corrects.
- **DR-004**: A return MUST NOT add operational state to a Document, a line or a Commitment.
  Whether goods have come back is derived from movements.
- **DR-005**: Traces MUST reach their records by opaque identity and MUST NOT restate business
  fields.
- **DR-006**: Every read, derivation, validation and explanation MUST be tenant-scoped.
- **DR-007**: No cause is introduced; the closed cause vocabulary is untouched.
- **DR-008**: Movement correction MUST keep working unchanged for a return, so a return
  recorded in error is voided the way any other movement is.

### Key Entities *(when data is involved)*

- **Movement (`return`)**: Goods coming back, now able to name the delivery they reverse.
- **DocumentLine (credit note)**: What was credited, referencing the order line it credits.
- **DocumentLine (order)**: The line everything hangs off — shipped against, returned
  against, billed and credited.

## Success Criteria *(mandatory)*

- **SC-001**: A recorded return no longer produces a wrong signal in the queue.
- **SC-002**: Goods that came back are not reported as unbilled.
- **SC-003**: An operator can see, for any order line, how much came back and how much was
  credited, and is told when the two disagree in the direction that costs money.
- **SC-004**: A kept delivery promise stays kept after a return.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- Spec 076's billed-line reference is in place and is the right grain for crediting too.
- A credit note is recorded as a Document of type `credit_note` with lines. Nothing posts it,
  and this feature does not change that.
- Absence of a credit note line means the goods have not been credited. That rests on the
  same contract as Spec 076: every crediting line sets the reference.
- Consumer trade credits without a return often enough that reporting it would be noise. If
  that turns out to be wrong for a given business, the rule to revisit is FR-008, not the
  model.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | return acceptance test |
| FR-002 | US1 scenario 4 | supplier-side refusal test |
| FR-003 | US1 scenario 3 | over-return refusal test |
| FR-004 | US1 scenario 5 | unchanged fulfilment test |
| FR-005 | US3 scenario 1 | credit reference validation test |
| FR-006 | US2 scenarios 1, 2 | returned-goods netting test |
| FR-007 | US3 scenarios 1, 2 | returned-not-credited derivation test |
| FR-007a | Edge cases | unbilled-return test |
| FR-008 | US4 scenarios 1, 2 | credited-not-returned derivation test |
| FR-008a | US3, US4 | mutual exclusivity test |
| FR-009 | US3 scenario 4 | consolidated crediting test |
| FR-010 | Edge cases | mismatched unit test |
| FR-011 | US3 scenario 1 | shared movement path test |
| FR-011a | Edge cases | voided movement test |
| FR-012 | US3 scenario 1 | causal values test |
| FR-013 | US3 scenario 1 | entry shape and trace test |
| FR-014 | US3 scenario 3; US4 scenario 3 | clearing test per class |
| FR-015 | Edge cases | explanation not-found parity test |
| FR-016 | US3 scenario 1 | catalog coverage and guidance gate test |
| FR-017 | US3 scenario 1 | shared list and explanation contract test |
| FR-018 | US3 scenario 1 | deterministic ordering test |
| DR-001 | — | no migration added |
| DR-002 | US3 scenario 3 | read-time derivation test |
| DR-003 | US3 scenario 1 | shared movement path test |
| DR-004 | US1 scenario 5 | no-operational-state test |
| DR-005 | US3 scenario 1 | opaque trace test |
| DR-006 | Edge cases | tenant isolation test |
| DR-007 | US3 scenario 1 | existing cause-vocabulary drift gate |
| DR-008 | Edge cases | movement correction test |
