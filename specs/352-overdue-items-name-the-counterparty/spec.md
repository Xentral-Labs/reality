# Feature Specification: Overdue Items Name the Counterparty

**Feature Branch**: `352-overdue-items-name-the-counterparty`

**Created**: 2026-10-03

**Status**: Accepted

**Language**: English

**Input**: A consumer agent asked about an overdue receivable answered with dates and amounts
only; naming the customer and the invoice took two more reads.

## Context and Intent

### Problem

An `overdue_receivable` or `overdue_payable` entry identifies its invoice only by opaque id.
To say who owes what on which invoice, an agent reads `finance_settlement_context` and then
the party. Commitment entries already carry their document number and customer reference.

### Scope

- Both overdue classes carry, in their trace, the invoice's number, its customer reference,
  the counterparty's id and the counterparty's name.

### Non-Goals

- No new class, cause, causal value or schema. Amounts and dates stay in the causal values.
- None of the new fields is an identity; `document_id` and `party_id` stay the join keys.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explain an overdue item in one read (Priority: P1)

1. **Given** an overdue sales invoice, **When** exceptions are listed, **Then** its entry
   names the invoice number, the customer reference (or none), the customer's id and name.
2. **Given** an overdue supplier invoice, **When** exceptions are listed, **Then** its entry
   names the same for the supplier.

### Edge Cases

- An invoice without a customer reference carries `customer_reference: null`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The trace of `overdue_receivable` and `overdue_payable` MUST carry
  `document_number`, `customer_reference`, `party_id` and `party_name`, each null when the
  invoice holds none.

### Domain and Architecture Requirements

- **DR-001**: The fields come from the aging register rows the classes already read; no read
  per entry. This narrows DR-003 of specs 069 and 074: the trace names its records for a
  reader and still restates no amount or date.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An agent can name the counterparty and invoice of an overdue item from the
  entry alone.

## Assumptions and Dependencies

- Builds on specs 069 (overdue receivables) and 074 (overdue payables), and on the commitment
  trace's `document_number` and `customer_reference`. Additive keys only.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US1.1, US1.2 | `tests/operational_exceptions/test_derivation.py::test_overdue_receivable_entry_shape`, `::test_overdue_payable`, `::test_overdue_items_name_the_customer_reference` |
| DR-001 | US1 | `packages/reality-core/src/reality/services/exceptions.py::_open_item_exceptions` |
| SC-001 | US1 | `tests/operational_exceptions/test_derivation.py::test_overdue_items_name_the_customer_reference` |
