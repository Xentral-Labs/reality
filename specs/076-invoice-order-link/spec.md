# Feature Specification: Invoice Lines Know What They Bill

**Feature Branch**: `076-invoice-order-link`
**Created**: 2026-09-05
**Status**: Draft
**Language**: English
**Input**: "Add the one missing edge between an invoice line and the order line it bills, and the three conditions it makes derivable."

## Context and Intent

### Problem

Reality can follow a promise from the order to the goods and cannot follow it to the money.
An order line becomes a Commitment, the Commitment carries `document_line_id` back to that
line, and every Movement points at its Commitment. Ask how much of one order line has
shipped and the answer is exact.

Ask whether it was billed and there is no answer at all. An invoice is a Document like any
other, with lines of its own, and nothing on those lines says which order line they bill.
The two halves of the same transaction sit in the same table and are not connected.

Three conditions a trading business depends on fall into that gap. Goods leave and nobody
raises an invoice, which is revenue given away. An invoice arrives for goods that never
came, which is money paid for nothing. A supplier bills a price other than the one agreed,
which is the oldest leak in purchasing. None of them can be derived today, and none of them
is a quantity or a price Reality is missing — it holds all four numbers and cannot pair
them up.

The edge has to sit on the line. A header reference from an invoice to an order cannot
express a consolidated invoice covering twelve orders, which is ordinary B2B billing, and
even a many-to-many relation at header level would say only that an invoice touches an
order, never how much of it. With partial deliveries — the case where these conditions
matter most — how much is the entire question.

### Scope

- Give a document line an optional reference to the order line it bills.
- Accept that reference when a document is recorded, and validate that it points at an
  order line of the same tenant on the matching side of the business.
- Report goods shipped against a sales order line that no invoice line bills.
- Report a purchase order line billed beyond what has been received.
- Report an invoice line whose unit price differs from the price agreed on the order line.
- Give all three the identity, severity, impact, causal values, trace, explanation,
  ordering, tenant isolation and operator guidance every existing class carries.

### Non-Goals

- Teaching the financial flow to read lines. Posting, settlement and open items work on the
  header amount today, and they still will. Tax per position, crediting a single position
  and margin by item all depend on that larger change and none of them is in this feature.
- Creating an invoice from an order. Filling the reference is the caller's job here; an
  operation that bills an order and produces the lines itself is a separate feature.
- Backfilling, cut-off dates, or any tolerance for lines recorded before this exists. There
  is no production data, which is what makes absence a usable signal from the first day.
- Ledger handling for the `credit_note` document type, which the interface offers and the
  backend ignores. It is a real open thread and it is not this one.
- Reporting an invoice raised ahead of shipment on the sales side, or goods received that a
  supplier has not billed yet. Both are ordinary — prepayment on one side, an invoice still
  in the post on the other — and reporting them would be noise.
- Schema beyond the single reference.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/006-documents-evidence/spec.md`](../006-documents-evidence/spec.md)
- [`specs/008-commitments-holds/spec.md`](../008-commitments-holds/spec.md)
- [`specs/074-trade-control-gaps/spec.md`](../074-trade-control-gaps/spec.md)
- [`specs/071-catalog-operator-guidance/spec.md`](../071-catalog-operator-guidance/spec.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-05

- Q: Header level or line level? → A: Line. A header reference cannot express a consolidated
  invoice over several orders, which is ordinary B2B practice, and it cannot say how much of
  an order is billed, which is the whole question when deliveries are partial.
- Q: How are lines recorded before this feature treated? → A: There are none worth treating.
  The product holds test data only, so no tolerance, cut-off or backfill is needed — and
  that is precisely what lets a missing reference mean "not billed" rather than "unknown".
- Q: Should the reference be mandatory? → A: No, and the reason matters. An invoice line may
  legitimately bill something no order promised — freight, a one-off service, a rounding
  line. `null` therefore means "this line bills nothing from an order", not "unknown", and
  the contract that every order-billing line sets it is what keeps absence meaningful.
- Q: Why only two of the four possible mismatches? → A: The other two are normal business.
  An invoice ahead of shipment is a prepayment; goods received before the supplier's invoice
  arrives is the usual sequence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See What Was Shipped and Never Billed (Priority: P1)

An operator sees sales order lines whose goods have gone out with no invoice line billing
them, with the quantity delivered, the quantity billed and the difference.

**Why this priority**: It is revenue the company has already earned and not asked for, and
partial deliveries make it routine rather than exceptional.

**Independent Test**: Ship part of an order line, bill less than was shipped, and verify the
difference is reported; bill the remainder and verify it clears.

**Acceptance Scenarios**:

1. **Given** a sales order line with goods delivered and no invoice line billing it, **When**
   the queue is listed, **Then** one entry appears with the delivered quantity, zero billed,
   and the full difference.
2. **Given** a sales order line billed for less than was delivered, **When** the queue is
   listed, **Then** the entry reports the difference rather than the whole quantity.
3. **Given** the same line, **When** an invoice line bills the remainder, **Then** the entry
   disappears without any manual step.
4. **Given** an order line billed by two invoice lines on different invoices, **When** the
   queue is listed, **Then** both count towards the billed quantity, because a consolidated
   or partial invoice is ordinary.
5. **Given** an order line with nothing delivered yet, **When** the queue is listed, **Then**
   no entry appears, whatever has or has not been billed.

### User Story 2 - See What Was Billed and Never Received (Priority: P1)

An operator sees purchase order lines billed beyond what has arrived, with the quantity
billed, the quantity received and the difference.

**Why this priority**: It is money leaving for goods the company does not have.

**Independent Test**: Bill a purchase order line beyond the receipt, verify the difference is
reported, then record the missing receipt and verify it clears.

**Acceptance Scenarios**:

1. **Given** a purchase order line billed for more than has been received, **When** the queue
   is listed, **Then** one entry appears with the billed quantity, the received quantity and
   the difference.
2. **Given** the same line, **When** the outstanding goods arrive, **Then** the entry
   disappears without any manual step.
3. **Given** a purchase order line received in full and billed in full, **When** the queue is
   listed, **Then** no entry appears.
4. **Given** a purchase order line received but not yet billed, **When** the queue is listed,
   **Then** no entry appears, because a supplier invoice still to come is the usual sequence.

### User Story 3 - See a Price That Was Not the One Agreed (Priority: P2)

An operator sees invoice lines whose unit price differs from the price agreed on the order
line they bill, on either side of the business.

**Why this priority**: It is the classic purchasing leak and the cheapest of the three to
derive once the reference exists, but it only matters where the reference is already in use.

**Independent Test**: Bill an order line at a different unit price and verify both prices and
the difference are reported; correct the invoice and verify it clears.

**Acceptance Scenarios**:

1. **Given** an invoice line billing an order line at a different unit price, **When** the
   queue is listed, **Then** one entry appears with the agreed price, the billed price and
   the difference.
2. **Given** an invoice line billing at exactly the agreed price, **When** the queue is
   listed, **Then** no entry appears.
3. **Given** an invoice line that bills no order line, **When** the queue is listed, **Then**
   no entry appears, because nothing was agreed for it to differ from.

### Edge Cases

- An invoice line references an order line of another tenant, or a line that is not on an
  order at all.
- A sales invoice line references a purchase order line, or the reverse.
- An order line is billed by more invoice lines than its quantity covers.
- An order line has no commitment — freight, a discount or a service — so nothing was ever
  promised to deliver against it.
- A movement is corrected after the line was billed.
- An invoice is reversed while its lines still reference order lines.
- Quantities are recorded in different units on the order line and the invoice line.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A document line MUST be able to reference the order line it bills, and that
  reference MUST be optional.
- **FR-002**: The reference MUST be rejected when it points at a line of another tenant, at
  a line that is not on a sales or purchase order, or at an order on the opposite side of
  the business from the billing document.
- **FR-003**: An absent reference MUST mean that the line bills nothing from an order, and
  MUST NOT be treated as unknown.
- **FR-004**: The system MUST report one entry for every sales order line whose delivered
  quantity exceeds the quantity billed against it by invoice lines.
- **FR-005**: The system MUST report one entry for every purchase order line whose billed
  quantity exceeds the quantity received against it.
- **FR-005a**: Both quantity classes MUST consider only order lines that promised a
  delivery, which is to say lines carrying a Commitment. A freight, discount or service line
  promises no goods, can never be received, and MUST NOT be reported for failing to be.
- **FR-006**: The system MUST report one entry for every invoice line whose unit price
  differs from the price agreed on the order line it bills.
- **FR-007**: Quantities billed MUST be summed across every invoice line referencing the
  same order line, so partial and consolidated invoicing behave correctly.
- **FR-007a**: A quantity comparison MUST be made only between lines recorded in the same
  unit. Where the units differ nothing is reported, because a converted figure would be a
  guess and an unconverted one would be wrong.
- **FR-008**: Delivered and received quantities MUST come from the movements already linked
  through the order line's commitment, not from a second count.
- **FR-009**: Each entry MUST state the two quantities or prices it compares and their
  difference.
- **FR-010**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace,
  in the same shape as every existing class.
- **FR-011**: Each entry MUST disappear as soon as its condition ends — billed, received or
  corrected — without acknowledgement or any other manual step.
- **FR-012**: The explanation of an entry MUST re-derive the current condition, and a
  malformed, unknown, cleared or foreign identity MUST produce the same not-found response
  the queue already returns.
- **FR-013**: All three classes MUST be declared in the closed catalog with an authority
  reference, named executable evidence, and the description, owner and clearing path every
  class carries.
- **FR-014**: Every surface that consumes the queue MUST receive the three classes through
  the existing shared list and explanation contract.
- **FR-015**: The queue MUST remain deterministically ordered for identical data, with the
  longest-standing discrepancy first within each of the three classes.

### Domain and Traceability Requirements

- **DR-001**: The reference is Evidence about Evidence: it records which agreed line a
  billed line settles. It adds no operational state to either document and no status field.
- **DR-002**: The three classes MUST be derived at read time from existing tenant-owned
  Documents, DocumentLines, Commitments and Movements.
- **DR-003**: Delivered and received quantities MUST reuse the existing path from an order
  line through its Commitment to its Movements, so a quantity is never counted two ways.
- **DR-004**: Traces MUST reach their records by opaque identity and MUST NOT restate
  business fields.
- **DR-005**: Every read, derivation, validation and explanation MUST be tenant-scoped.
- **DR-006**: The reference MUST be the shortest true link: from the billed line directly to
  the agreed line, never through the party, the item or a date window.
- **DR-007**: No cause is introduced; the closed cause vocabulary is untouched.

### Key Entities *(when data is involved)*

- **DocumentLine (invoice)**: The billed line, which gains the optional reference.
- **DocumentLine (order)**: The agreed line, which carries the quantity and the price the
  other two are measured against, and which already reaches its Movements through its
  Commitment.

## Success Criteria *(mandatory)*

- **SC-001**: An operator can see, for any order line, how much has been delivered and how
  much has been billed, and is told when the two disagree in the direction that costs money.
- **SC-002**: A consolidated invoice covering several orders is handled correctly, with each
  line counting towards its own order line.
- **SC-003**: A price billed differently from the price agreed is reported with both figures.
- **SC-004**: A cleared condition leaves the queue on the next read with no manual action,
  and its former identity is no longer explainable.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- Absence of the reference is meaningful because the product holds no production data and
  because every order-billing line will set it from now on. That contract is what the first
  class rests on; if invoices are later created by a path that omits it, the class would
  report orders that were in fact billed.
- Invoices are already recorded with lines by the only path that creates them in the
  product. The header-only path is used by demo scenarios and tests, and lines recorded that
  way simply reference nothing.
- Quantities are compared in the unit recorded on each line. A billed line in a different
  unit from the order line is out of scope for this feature and is named as an edge case
  rather than silently converted.
- All three classes are severity `high`, consistent with the existing promise-related and
  financial classes.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | reference persistence test |
| FR-002 | Edge cases | reference validation test |
| FR-003 | US1 scenario 1; US3 scenario 3 | absent-reference meaning test |
| FR-004 | US1 scenarios 1, 2, 5 | shipped-not-billed derivation test |
| FR-005 | US2 scenarios 1, 3, 4 | billed-not-received derivation test |
| FR-005a | Edge cases | non-deliverable line test |
| FR-006 | US3 scenarios 1, 2 | price difference derivation test |
| FR-007 | US1 scenario 4 | consolidated invoicing test |
| FR-007a | Edge cases | mismatched unit test |
| FR-008 | US1 scenario 2; US2 scenario 1 | shared movement path test |
| FR-009 | US1 scenario 1; US3 scenario 1 | causal values test |
| FR-010 | US1 scenario 1 | entry shape and trace test |
| FR-011 | US1 scenario 3; US2 scenario 2 | clearing test per class |
| FR-012 | Edge cases | explanation not-found parity test |
| FR-013 | US1 scenario 1 | catalog coverage and guidance gate test |
| FR-014 | US1 scenario 1 | shared list and explanation contract test |
| FR-015 | US1 scenario 1 | deterministic ordering test |
| DR-001 | US1 scenario 3 | no-operational-state test |
| DR-002 | US1 scenario 3 | read-time derivation test |
| DR-003 | US2 scenario 1 | shared movement path test |
| DR-004 | US1 scenario 1 | opaque trace test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US1 scenario 4 | shortest-link review against the Constitution |
| DR-007 | US1 scenario 1 | existing cause-vocabulary drift gate |
