# Feature Specification: Payout Settlement Cost

**Feature Branch**: `342-payout-settlement-cost`

**Created**: 2026-10-03

**Status**: Accepted (owner decision, 2026-10-03)

**Language**: English

**Input**: Spec 336 books a marketplace or payment-provider payout line by line. A statement of
400 orders took about three minutes in the R04 story, and each line cost about 100 database
statements, almost all in the shared payment and allocation code. The owner asked to measure the
cost per line, name its causes, book the lines as one batch with identical results, and pin a
budget per line.

## Context and Intent

### Problem

A provider pays hundreds to thousands of orders in one payout. Settling it sent every line through
the single-payment path: each line took the same business and finance locks again, read the
company currency, accounts, parties and proposal again, stored its source record with its own
reads, resolved its order references with its own queries, and read every allocation of the
company to check one payment. Settlement cost grew with the statement and with the company's
history, and reviewing a statement cost about ten statements per line.

### Decision

Settlement and its review run as one batch. Inside it, a lock taken stays taken for the
transaction, records the batch does not change are read once, the line source records are stored
together, and the order references of the whole statement are read with a few set-based reads
before the lines are planned. Allocation reads only the allocations of the payment it checks.
What is booked is unchanged: the same documents, ledger entries, allocations, payment returns,
events, findings and refusals.

### Non-Goals

- Changing what a payout books, its review or its tool contracts.
- Batching the inserts themselves; each line still writes its own records.
- Other callers of the payment path, which keep reading per call.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A large payout settles in reasonable time (Priority: P1)

As a bookkeeper, I confirm a marketplace payout of hundreds of orders without waiting minutes.

**Independent Test**: Statement counts for payouts of different sizes.

**Acceptance Scenarios**:

1. **Given** payouts of 15 and 75 orders with refunds, chargebacks and fees, **When** each is
   reviewed and settled, **Then** each further line costs at most 18 statements to settle and 2
   to review.
2. **Given** the R04 story of 400 orders, **When** it is reviewed and settled, **Then** it takes
   fewer than 20 statements per line.

### User Story 2 - Nothing booked changes (Priority: P1)

As an auditor, I see the same records whether a payout was booked as one batch or line by line.

**Independent Test**: The same statement shape is settled with the batch switched off and on.

**Acceptance Scenarios**:

1. **Given** two statements of the same shape, **When** one is settled line by line and the
   other as a batch, **Then** their documents, ledger entries, allocations, payment returns,
   events, line source records and finance revision rise are the same.

### Edge Cases

- A reversal recorded during the batch (a chargeback) is seen by every later line.
- A line source already stored (settling the same statement again) is returned, not stored twice.
- Outside a payout settlement, every read and lock behaves as before.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Settling a payout MUST cost at most 18 further statements per line, and reviewing
  it at most 2, measured as the growth between two statement sizes.
- **FR-002**: What a batched settlement books MUST equal what line-by-line booking books.
- **FR-003**: Locks and stable reads MUST be kept only within one settlement or review and its
  transaction; nothing is remembered past it.

### Domain and Architecture Requirements

- **DR-001**: No schema change.
- **DR-002**: Allocation of one payment reads only the allocations touching it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Statements per line to settle drop from about 82 to about 15; to review from about
  10 to under 1 (see [research.md](research.md)).
- **SC-002**: The R04 story's statement budget is 20 per line instead of 120.

## Assumptions and Dependencies

- Builds on [spec 336](../336-marketplace-payouts/spec.md).

## Clarifications

### Session 2026-10-03

- The owner delegated these decisions to the recommended options.
- Q: What budget per line is pinned? → A: What the measurement shows is honestly achievable: 18
  to settle (measured 15) and 2 to review (measured under 1). The remaining statements are the
  line's own writes (source record, document, ledger entries, allocation, events) and the
  revision and event-progress updates each flush carries; going lower would mean bulk inserts.
- Q: Where does the batch apply? → A: Only to payout settlement and its review; other callers of
  the shared payment code keep their behaviour.
- Q: Is the savepoint per payment kept inside the batch? → A: No. The batch stands or falls as
  one transaction, so a failure inside it aborts the whole settlement either way.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, SC-001 | US1.1 | `tests/finance/test_payout_cost.py::test_booking_a_line_costs_a_bounded_number_of_statements` |
| SC-002 | US1.2 | `tests/scenarios/test_catalog_finance.py::test_a_payout_of_400_orders_with_refunds_chargebacks_and_fees_books_every_line` |
| FR-002 | US2.1 | `tests/finance/test_payout_cost.py::test_the_batch_books_exactly_what_line_by_line_booking_books` |
| FR-003, DR-001, DR-002 | All | Diff review; `tests/finance/test_payouts.py`, finance suite |
