# Feature Specification: Unconfirmed Purchase Orders

**Feature Branch**: `346-unconfirmed-purchase-orders`

**Created**: 2026-10-03

**Status**: Accepted

**Language**: English

**Input**: Journey G10 "Supplier never confirms — unconfirmed purchase flagged?" from the
scenario coverage; the owner asked to build it (round 4 of small gaps).

## Context and Intent

### Problem

Reality does not expect a supplier to confirm a purchase order. A purchase the supplier never
answered is noticed only once its delivery date has passed, as an overdue supplier promise —
weeks too late to order elsewhere.

### Scope

- A supplier's confirmation is what Reality already keeps: a statement restating the purchase
  promise (a commitment revision with a date, quantity or price; a confirmation exactly as
  ordered restates the date). Goods arriving answer the question too.
- A new finding reports an open purchase line with neither, three days after its order was
  placed.

### Non-Goals

- A per-company or per-supplier response time.
- A new confirmation record, document status or automatic reminder to the supplier.

## Clarifications

### Session 2026-10-03

The owner delegated these decisions to the recommended options.

- Q: What is a confirmation? → A: Any revision of the purchase promise stated by the supplier
  (spec 310's confirmed date, quantity or price), or a receipt against it. No new record.
- Q: How long may a supplier take? → A: Three days after the order was placed, fixed for every
  company like the other floors of the exception catalog.
- Q: Per order or per line? → A: Per line, like the other purchase-line findings; a line already
  confirmed is not reported while another line of the same order is.
- Q: When is the order placed? → A: The order's stated order time, else its document date, else
  when the promise was recorded.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask the silent supplier early (Priority: P1)

As a buyer, I see which purchase lines the supplier has not confirmed, before their delivery
date, so I can chase the supplier or order elsewhere.

**Independent Test**: A purchase placed four days ago and due in three weeks is reported; the
supplier's confirmation clears it.

**Acceptance Scenarios**:

1. **Given** a purchase placed four days ago and due in three weeks, **When** the findings are
   read, **Then** it is reported as Purchase order not confirmed, and not as overdue.
2. **Given** a purchase placed yesterday, **When** the findings are read, **Then** it is not yet
   reported.
3. **Given** a reported line, **When** the supplier's confirmation is recorded as a revision, or
   goods arrive, or the line is cancelled, **Then** it is no longer reported.

### Edge Cases

- Read as of a moment before the confirmation was stated, the line is still reported.
- Tenant isolation: another company sees nothing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Reality MUST report an open purchase line without a stated revision or receipt
  three days after its order was placed, naming the order, when it was placed and since when a
  confirmation was expected; derived at read time and dated at that moment.
- **FR-002**: A revision of the line, a receipt against it, or its cancellation MUST clear it.

### Domain and Architecture Requirements

- **DR-001**: No schema change; the confirmation is the existing commitment revision.
- **DR-002**: The finding is derived at read time and never stored.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Journey G10 is supported with a business story.

## Assumptions and Dependencies

- Builds on spec 310 (supplier confirmations as revisions with a confirmed price).

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US1.1, US1.2 | `tests/test_purchase_order_unconfirmed.py::test_an_unconfirmed_line_is_reported_after_three_days` |
| FR-002 | US1.3 | `tests/test_purchase_order_unconfirmed.py::test_a_confirmation_or_a_receipt_clears_it` |
| SC-001 | US1 | `tests/scenarios/test_catalog_purchasing.py::test_a_purchase_order_the_supplier_has_not_confirmed_is_flagged` |
