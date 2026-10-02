# Feature Specification: Payment Returns Store No Forward Links

**Feature Branch**: `318-payment-return-links`

**Created**: 2026-10-02

**Status**: Implemented

**Language**: English

**Input**: Owner review of the tables added since 2026-09-29, follow-up to spec 316. `payment_return` (spec 297) stores links to what it caused, although each of those records already points back to it.

## Context and Intent

### Problem

A payment return stores three forward links:

- **`ledger_reversal_id`**: the reversal of the payment's posting. The reversal itself names that posting group (`original_posting_group_id`), and a posting group can be reversed only once.
- **`fee_document_id`**: the company's fee document.
- **`fee_charge_document_id`**: the fee charged on to the customer.

Both fee documents are created with the return's own source record.

So each link is stored twice: once where it is true, and once on the return. That is the "header that knows everything" shape of a classic ERP and breaks AGENTS.md rule 5 ("prefer the shortest true relationship; do not duplicate"). Nothing stops the two copies from disagreeing.

### Scope

- Drop the three columns. Read the links from the records that hold them.
- Keep every read output unchanged. `return_detail`, MCP, Web and CLI still show all three links.
- Migrate only when every stored link agrees with what the records say. The downgrade restores the links exactly.

### Non-Goals

- Changing what a return states: kind, reason, reference, date, fee and who bears it.
- Changing how a return posts, reverses or creates fee documents.
- The `payment.returned` event payload, which keeps naming the reversal as history.
- `item_reorder_point` without a source record (open from the same review).

## Clarifications

### Session 2026-10-02

- Q: Do the reads keep the three links? → A: Yes, derived. Readers see no change. (Owner request: "the same as for stock blocks", applied to forward links.)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A return names what it caused, read from where it is true (Priority: P1)

As a finance clerk, I open a returned payment and see its reversal and fee documents exactly as before. Those links are read from the reversal and the documents themselves.

**Why this priority**: It is the whole change.

**Independent Test**: Service tests in `tests/finance/test_payment_returns.py` and a migration test.

**Acceptance Scenarios**:

1. **Given** two returned payments, one with a fee charged on and one with a fee the company keeps, **When** each is read, **Then** each names its own reversal of its own payment's posting and its own fee documents. The kept fee names no charge document.
2. **Given** a return without a fee, **When** it is read, **Then** it names its reversal and no fee documents.
3. **Given** a database at 0109 whose stored links all agree with the records, **When** it is upgraded, **Then** the columns are dropped, and a downgrade restores the same values.
4. **Given** a stored link that the records do not confirm, **When** the database is upgraded, **Then** the migration refuses and drops nothing.

### Edge Cases

- Tenant isolation: every derivation is scoped to the return's company.
- A replayed confirmation returns the same detail as the first. It derives the same links.
- A later reversal of the reversal is a different posting group and is never taken for the return's own reversal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `payment_return` MUST NOT store links to the reversal or fee documents it caused.
- **FR-002**: Return reads MUST name the reversal of the payment's posting group and the fee documents carrying the return's source record, with the same keys and values as before.
- **FR-003**: Migration `0110` MUST refuse while any stored link differs from the derived one, and its downgrade MUST restore the links.

### Domain and Architecture Requirements

- **DR-001**: Links MUST follow the shortest true relationship. Consequences point to their cause, never the other way (AGENTS.md rule 5).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `payment_return` goes from 14 to 11 columns, and every return read shows the same output as before.

## Assumptions and Dependencies

- Builds on spec 297 (merged as #267). A payment's posting group is reversed at most once (`ledger_reversal.original_posting_group_id` is unique). The return refuses a payment whose posting was already reversed.
- Fee documents are created only by `record_return`, with the return's source record. No other path creates the types `payment_return_fee` and `payment_return_fee_charge`.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, DR-001, SC-001 | — | `test_a_return_does_not_store_what_it_caused` |
| FR-002 | US1 1–2 | `test_each_return_names_its_own_reversal_and_fee_documents`, `test_a_return_without_a_fee_names_no_fee_documents`, and the existing spec 297 tests |
| FR-003 | US1 3–4 | `test_the_migration_drops_the_links_only_when_they_can_be_read_back` |
