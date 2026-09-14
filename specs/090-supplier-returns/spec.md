# Feature Specification: Goods Going Back the Other Way

**Feature Branch**: `090-supplier-returns`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "A supplier delivery accepts receipts and nothing else, so sending goods back to a supplier cannot be recorded at all. Spec 089 built the money half of a supplier credit and said so; this is the half it was missing."

## Context and Intent

### Problem

Reality can record goods coming back from a customer, what the company did with them, and
whether the customer was credited. In the other direction it can record nothing at all.

A `supplier_delivery` commitment accepts receipts and only receipts. There is no way to say that
ten of the hundred that arrived were faulty and went back, so:

- **Stock is wrong.** The goods are gone and Reality still holds them. Every reservation,
  coverage check and stocktake comparison built on that figure is wrong by the returned
  quantity.
- **The company expects an invoice for goods it no longer has.** `receipt_unbilled` reports an
  accrual for the full receipt, because nothing can tell it part of that receipt went back.
- **Nothing joins the goods to the money.** Spec 089 built the supplier credit and said plainly
  that a credit for returned goods carries no evidence of the goods behind it. Nothing compares
  what went back against what was credited, the way `returned_not_credited` does on the selling
  side.

And there is a case the two chains should already have met on. A customer sends something back
and the company sends it on to the supplier — the ordinary path for a faulty item. Spec 082 made
a return name the movement that settles it and listed "a shipment to the supplier" as one of the
things that settles one. That movement could not be recorded, so the one resolution an operator
most often wants was the one the model could not express.

### Scope

- Record goods going back to a supplier against the delivery they came in on.
- Bound it by what actually arrived, as the selling side is bounded by what actually shipped.
- Let such a movement settle a customer return, closing return-to-resolution across both chains.
- Stop expecting an invoice for goods that went back.
- Two classes mirroring the two Spec 079 added: goods back to a supplier without a credit, and a
  supplier credit larger than what went back.

### Non-Goals

- **A mirror of `return_unresolved`.** A customer return sits in a location waiting for somebody
  to decide what happens to it, and that waiting is the condition that class reports. Goods sent
  back to a supplier are gone; there is nothing sitting and nothing to decide. Building the
  mirror would produce a class that can never be true.
- **A resolution chain for a supplier return.** For the same reason: the movement out *is* the
  resolution.
- **Deciding why the goods went back.** Faulty, over-delivered, wrong item, ordered in error —
  Reality records that they went back, not the argument about whose fault it was.
- **Recording a return with no delivery to name.** Goods can only go back against the receipt
  they came in on, exactly as a customer return can only go back against a shipment.
- **Changing what fulfilment means.** A supplier kept its promise when the goods arrived, and
  sending some back does not unmake that, exactly as a customer return does not reopen a
  delivery the company kept.

### Existing Contracts

- [`specs/079-returns-connect/spec.md`](../079-returns-connect/spec.md)
- [`specs/082-return-resolved/spec.md`](../082-return-resolved/spec.md)
- [`specs/089-supplier-credit-notes/spec.md`](../089-supplier-credit-notes/spec.md)
- [`docs/features/movements.md`](../../docs/features/movements.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/features/procure_to_pay.md`](../../docs/features/procure_to_pay.md)
- [Constitution](../../.specify/memory/constitution.md), principles II and III

## Clarifications

### Session 2026-09-06

- Q: Can a customer return and a supplier return be the same movement type? → A: No. A customer
  return brings goods into a location and a supplier return takes them out; they are opposite
  physical facts and a single type would have to guess the direction from the commitment. Two
  types, each with the direction it actually has.
- Q: Does sending goods back reopen the supplier's promise? → A: No, and for the same reason a
  customer return does not reopen the company's. The supplier kept its word when the goods
  arrived. Fulfilment answers whether a promise was kept; what the company still holds is a
  different question, asked by the classes that need it.
- Q: Which classes should stop counting returned goods? → A: `receipt_unbilled` only. It reports
  an invoice nobody has sent for goods that arrived, and the company should not be accruing one
  for goods it sent back. `billed_not_received` keeps counting the raw receipt, because the goods
  did arrive and a return does not unmake that — the mirror of how the selling side treats
  `shipped_not_billed` and the return classes.
- Q: Should a supplier return be able to settle a customer return? → A: Yes, and it is the point.
  Spec 082 already named "a shipment to the supplier" as one of the things that settles a return,
  and the movement to do it did not exist. Now it does, and the two chains meet where an operator
  actually works.
- Q: What stops somebody returning more than arrived? → A: The same rule the selling side uses:
  the constraint is what actually moved, not what the promise has left open, because on a fully
  received promise the open quantity is zero and every return would be refused.
- Q: Does a supplier credit for a rebate get reported as a credit without goods? → A: No. The
  class only speaks once goods have started going back, exactly as its selling-side mirror does.
  A rebate, an allowance or a price correction has no return behind it and is never reported.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Send the Faulty Ones Back (Priority: P1)

Goods that arrived and went back to the supplier leave stock and are recorded against the
delivery they came in on.

**Why this priority**: Until they can be recorded, stock is wrong and every figure built on it
is wrong by the same quantity.

**Independent Test**: Receive a purchase order line, send part of it back, and read stock and the
commitment.

**Acceptance Scenarios**:

1. **Given** a purchase order line with a hundred received, **When** ten go back to the supplier,
   **Then** stock falls by ten.
2. **Given** the same line, **When** the return is recorded, **Then** the supplier's promise is
   still fulfilled, because it was kept when the goods arrived.
3. **Given** a hundred received and ten already back, **When** ninety-one more are attempted,
   **Then** it is refused.
4. **Given** a customer delivery, **When** a supplier return is attempted against it, **Then** it
   is refused.
5. **Given** a supplier return with no location to take the goods from, **When** it is attempted,
   **Then** it is refused.

### User Story 2 - Send a Customer's Return On to the Supplier (Priority: P1)

A faulty item a customer sent back is shipped on to the supplier, and that settles the customer
return.

**Why this priority**: It is the most ordinary resolution there is, and it was the one the model
could not express.

**Acceptance Scenarios**:

1. **Given** a customer return sitting in a location, **When** a supplier return takes those
   goods out of that location naming the customer return, **Then** the customer return is
   settled and stops being reported as unresolved.
2. **Given** the same customer return, **When** a supplier return takes goods from a different
   location, **Then** it is refused.
3. **Given** a customer return already settled in full, **When** more is attempted against it,
   **Then** it is refused.

### User Story 3 - See What the Supplier Owes for It (Priority: P1)

An operator sees goods that went back to a supplier and were never credited, and supplier credits
larger than what went back.

**Why this priority**: The goods and the money are the two halves of one event, and until now the
buying side could see neither the goods nor the connection.

**Acceptance Scenarios**:

1. **Given** goods invoiced by the supplier and then sent back, **When** the queue is read,
   **Then** the uncredited quantity is reported.
2. **Given** a supplier credit note line naming the same order line, **When** the queue is read,
   **Then** the entry reports only what is still uncredited.
3. **Given** goods sent back that no supplier invoice ever billed, **When** the queue is read,
   **Then** nothing is reported, because the company was never charged for them.
4. **Given** a supplier credit larger than what went back, **When** the queue is read, **Then**
   the excess is reported.
5. **Given** a supplier credit for a rebate with nothing sent back, **When** the queue is read,
   **Then** nothing is reported.

### User Story 4 - Stop Expecting an Invoice for Goods That Went Back (Priority: P2)

`receipt_unbilled` counts what the company still has, not what once arrived.

**Acceptance Scenarios**:

1. **Given** a receipt past the billing threshold with part of it sent back, **When** the queue
   is read, **Then** the unbilled quantity excludes what went back.
2. **Given** a receipt entirely sent back, **When** the queue is read, **Then** nothing is
   reported.
3. **Given** an invoice for more than was received, **When** the queue is read, **Then**
   `billed_not_received` reports as it does today, because a return does not unmake a receipt.

### Edge Cases

- A supplier return for more than the whole receipt, and for exactly all of it.
- A supplier return against a commitment for a different item.
- A supplier return whose quantity a correction later voids.
- A supplier return that both settles a customer return and belongs to a supplier delivery.
- A supplier credit note line and a supplier invoice line naming the same order line.
- Goods returned in a unit the item cannot reconcile with the order line's.
- A supplier return against a commitment with an active hold.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Goods going back to a supplier MUST be recordable as a movement that takes them out
  of a location and names the supplier delivery they came in on.
- **FR-002**: That movement MUST be its own kind, distinct from a customer return, because the
  two are opposite physical facts.
- **FR-003**: It MUST be refused against a commitment that is not a supplier delivery, against a
  commitment for another item, and without a location to take the goods from.
- **FR-004**: It MUST NOT exceed what actually arrived against that delivery less what has
  already gone back, judged from movements rather than from the promise's open quantity.
- **FR-005**: It MUST NOT change what the promise counts as fulfilled.
- **FR-006**: Stock MUST fall by the returned quantity.
- **FR-007**: It MUST be able to settle a customer return, under the rules that already govern a
  settling movement: the goods must leave the location the return came back to, and settlements
  must not exceed what came back.
- **FR-008**: A movement a correction has voided MUST stop counting, on this side as on every
  other.
- **FR-009**: The system MUST report goods sent back to a supplier that the supplier has not
  credited, counting only quantities a supplier invoice actually billed.
- **FR-010**: The system MUST report a supplier credit larger than what went back, and MUST stay
  silent where nothing went back at all, so that a rebate, an allowance or a price correction is
  never reported.
- **FR-011**: One order line MUST produce at most one of those two entries.
- **FR-012**: `receipt_unbilled` MUST count what the company still holds — received less returned
  — rather than everything that once arrived.
- **FR-013**: `billed_not_received` MUST keep counting the raw receipt, because the goods did
  arrive and a return does not unmake that.
- **FR-014**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace, in
  the same shape as every existing class.
- **FR-015**: Each entry MUST disappear as soon as the condition ends, without acknowledgement
  or any other manual step.
- **FR-016**: The explanation of an entry MUST re-derive the current condition, and a malformed,
  unknown, cleared or foreign identity MUST produce the same not-found response the queue
  already returns.
- **FR-017**: The classes MUST be declared in the closed catalog with an authority reference,
  named executable evidence, and the description, owner and clearing path every class carries,
  and each MUST name its selling-side mirror.
- **FR-018**: The new operation MUST be reachable from the surfaces that already reach a customer
  return, and MUST be declared in every catalog that governs operations.
- **FR-019**: Quantities MUST be compared under the one comparability rule Spec 087 established,
  and a pair that cannot be reconciled MUST be reported there rather than judged here.
- **FR-020**: The queue MUST remain deterministically ordered for identical data.
- **FR-021**: Every existing class and operation MUST behave exactly as it does today, except
  `receipt_unbilled`, whose correction is FR-012.

### Domain and Traceability Requirements

- **DR-001**: No schema changes. A movement type is a string the model already accepts and the
  settling reference already exists.
- **DR-002**: Both classes MUST be derived at read time and MUST store nothing.
- **DR-003**: The two directions of the return comparison MUST share one body, so neither side
  can drift in what "returned" and "credited" mean.
- **DR-004**: Traces MUST reach their records by opaque identity and MUST NOT restate business
  fields already carried in causal values.
- **DR-005**: Every read, derivation and movement MUST be tenant-scoped.
- **DR-006**: No cause is introduced; the closed cause vocabulary is untouched.
- **DR-007**: Every quantity MUST come from a movement or a document line the tenant recorded;
  nothing may be apportioned or inferred.

### Key Entities *(when data is involved)*

- **Movement**: Gains a kind it always could have carried — goods going back to a supplier.
- **Commitment**: The supplier delivery a return is bounded by and named against.
- **DocumentLine**: The supplier invoice and supplier credit note lines the goods are compared
  against.

## Success Criteria *(mandatory)*

- **SC-001**: Goods sent back to a supplier leave stock and are recorded against the delivery
  they arrived on.
- **SC-002**: The most ordinary resolution of a customer return — sending it on to the supplier —
  is expressible and settles the return.
- **SC-003**: The buying side can see goods that went back without a credit, and a credit larger
  than what went back.
- **SC-004**: The company stops accruing an invoice for goods it no longer has.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- A supplier return is bounded by what arrived against one delivery. Goods returned against no
  purchase order at all — a sample, a free replacement — are outside this and stay so.
- The uncredited comparison uses what a supplier invoice billed, so a company that returns goods
  before the invoice arrives sees nothing until it does. That is the same order of events the
  selling side assumes and the same silence it keeps.
- Both classes are silent for a company that never returns anything to its suppliers.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | supplier return movement test |
| FR-002 | US1 scenario 4 | distinct movement kind test |
| FR-003 | US1 scenarios 4, 5; Edge cases | refusal tests |
| FR-004 | US1 scenario 3 | bounded by receipts test |
| FR-005 | US1 scenario 2 | fulfilment unchanged test |
| FR-006 | US1 scenario 1 | stock falls test |
| FR-007 | US2 scenarios 1, 2, 3 | resolution tests |
| FR-008 | Edge cases | correction-aware test |
| FR-009 | US3 scenarios 1, 2, 3 | uncredited derivation test |
| FR-010 | US3 scenarios 4, 5 | over-credited derivation test |
| FR-011 | US3 scenarios 1, 4 | at most one entry test |
| FR-012 | US4 scenarios 1, 2 | kept-quantity test |
| FR-013 | US4 scenario 3 | raw receipt test |
| FR-014 | US3 scenario 1 | entry shape and trace test |
| FR-015 | US3 scenario 2 | clearing test |
| FR-016 | Edge cases | explanation not-found parity test |
| FR-017 | US3 scenario 1 | catalog coverage and guidance gate test |
| FR-018 | US1 scenario 1 | catalog drift gates and surface tests |
| FR-019 | Edge cases | incomparable units test |
| FR-020 | US3 scenario 1 | deterministic ordering test |
| FR-021 | — | the existing suites, unchanged but for FR-012 |
| DR-001 | — | no migration added |
| DR-002 | US3 scenario 2 | read-time derivation test |
| DR-003 | US3 scenario 1 | one shared body test |
| DR-004 | US3 scenario 1 | opaque trace test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US3 scenario 1 | existing cause-vocabulary drift gate |
| DR-007 | US1 scenario 1 | recorded-quantities test |
