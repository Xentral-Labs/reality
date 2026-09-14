# Feature Specification: Everyday Fact Predicates

**Feature Branch**: `174-everyday-fact-predicates`
**Created**: 2026-09-12
**Status**: Reviewed with the owner on 2026-09-12; implemented
**Language**: English
**Input**: "Let people and agents state the observations a clerk records every day as Facts: a delivery instruction, the customer's own order reference, a payment promise, a disputed invoice line, a quality release for a lot, damage reported on a delivery."

## Context and Intent

### Problem

The Fact core accepts exactly one predicate, `order.shipping_priority`. The handbook shows six
further observations that ERP clerks record daily and that have no typed home in Reality. Today
neither a person in the Web app nor an agent through `fact_observe_propose` can state them: the
application refuses every unregistered predicate, and a Fact may not describe a lot at all.

### Scope

- Six additional predicates in the stable Fact catalog with their subject types and value contracts.
- Lots as a supported Fact subject, so a quality decision can describe the lot it was made about.
- The existing observation path for every adapter that already reaches `observe_fact` (Web, MCP,
  Chat): same command, same confirmation, same idempotency.

### Non-Goals

- No new command, tool, screen or CLI entry; the observation path is unchanged.
- No typed columns for these observations, no derivations from them, no exception classes that
  read them, and no effect on quantities, dates, allocations or balances.
- No source-specific extraction rules; owners keep configuring rules through Open questions.
- No free-text predicate: a value type and, where reviewed, allowed values remain mandatory.

### Existing Contracts

- [Facts](../../apps/docs/content/concepts/business-reality-guide/06-facts-and-open-questions.md)
- [Fact catalog](../../packages/reality-core/config/fact_catalog.yaml)
- [Reality gaps and Fact rules](../../docs/features/reality_gaps.md)
- [Data model](../../docs/DATA_MODEL.md)

## User Scenarios & Testing

### User Story 1 - State what a customer said about a promise (Priority: P1)

A clerk receives a note with the order: "deliver mornings only, use the side entrance". The note
is retained as a source record; the clerk states it as a Fact on the delivery Commitment. Later
anyone reading the order sees the instruction with its source.

**Independent Test**: Observe `order.delivery_instruction` on a commitment with a retained source
record; the Fact exists once and carries the source.

**Acceptance Scenarios**:

1. **Given** a retained source record and an open commitment, **When** a person or an approved
   agent proposal states `order.delivery_instruction` with a text value, **Then** one Fact exists
   with that value and no commitment field changes.
2. **Given** the same idempotency key with identical content, **When** it is stated again,
   **Then** the original Fact is returned and no second Fact exists.

### User Story 2 - Record a payment promise without touching the books (Priority: P1)

Finance is told on the phone that invoice RE-1042 will be paid by 30 September. The promise is
recorded on the invoice document as a calendar day. Open items do not change.

**Independent Test**: Observe `invoice.payment_promise_date` with `2026-09-30` on an invoice
document; the Fact exists and the open amount is unchanged.

**Acceptance Scenarios**:

1. **Given** an invoice document, **When** the promise is stated with a valid date, **Then** the
   Fact stores the date in ISO form.
2. **Given** the same invoice, **When** the promise is stated with text such as "end of month",
   **Then** the observation is refused with a message naming the predicate.
3. **Given** a delivery commitment, **When** a payment promise is stated on it, **Then** the
   observation is refused because the predicate does not support that subject type.

### User Story 3 - Record a quality decision for a lot (Priority: P2)

An inspection report releases lot 4711 for sale. The decision is stated on the lot as `released`
or `blocked`; free text is refused.

**Independent Test**: Observe `lot.quality_release` on a lot with `released`; then attempt
`looks fine` and expect refusal.

**Acceptance Scenarios**:

1. **Given** a lot of a lot-tracked item, **When** `released` is stated, **Then** the Fact exists
   with subject type `lot`.
2. **Given** the same lot, **When** a value outside the allowed list is stated, **Then** the
   observation is refused.

### User Story 4 - Keep the customer's reference, a dispute and a damage report (Priority: P2)

The customer's purchase order number is stated on the order document, a disputed line carries the
stated reason, and damage reported on arrival is stated on the delivery movement. None of these
creates a credit, a return or a stock change.

**Independent Test**: Observe the three predicates on a document, a document line and a movement;
each Fact exists with the stated text.

### Edge Cases

- A Fact subject from another tenant behaves as not found, as for every other subject type.
- A predicate stated on a subject type it does not list is refused before any value is checked.
- Rule-created Facts are unaffected: rules bring their own predicate contract.

## Requirements

### Functional Requirements

- **FR-001**: The Fact catalog MUST register `order.delivery_instruction` (commitment, string),
  `order.customer_reference` (document, string), `invoice.payment_promise_date` (document, date),
  `invoice_line.dispute_reason` (document_line, string), `lot.quality_release` (lot, enum:
  released, blocked) and `movement.damage_report` (movement, string) next to
  `order.shipping_priority`.
- **FR-002**: `observe_fact` MUST accept `lot` as a subject type and resolve the lot within the
  tenant like every other subject.
- **FR-003**: Every new predicate MUST enforce its value contract through the existing canonical
  value validation; a violation is refused with a message that names the predicate.
- **FR-004**: A predicate stated on a subject type it does not list MUST be refused.
- **FR-005**: Existing observation semantics MUST hold unchanged: a retained source record is
  required, confirmation and idempotency behave as before, and no typed record is written or
  derived from these Facts.
- **FR-006**: The application catalog MUST report seven Fact predicates.

### Key Entities

- **Fact predicate**: one reviewed kind of observation with subject types and a value contract.
- **Fact**: one source-supported observation about an existing subject, appended exactly once.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All six observations from the handbook table can be stated through the existing
  observation path and read back with their source.
- **SC-002**: Invalid values and unsupported subject types are refused with a message that names
  the predicate, verified by tests.
- **SC-003**: No open item, stock or commitment quantity changes when any of the six Facts is
  stated.

## Assumptions and Dependencies

- The value types `string`, `date` and `enum` and their canonical validation already exist.
- A human statement without a system source is retained first as a manual source record; this
  specification does not change how sources are created.
- Predicate labels stay technical identifiers; adapters render them as they are.

## Requirement Traceability

| Requirement | Evidence |
| --- | --- |
| FR-001, FR-006 | `packages/reality-core/config/fact_catalog.yaml`; `tests/test_application_catalog.py`; `tests/test_http_boundary.py` |
| FR-002, FR-003, FR-004, FR-005 | `reality.services.core.observe_fact`; `tests/test_fact_observation.py::test_everyday_predicates_describe_documents_lines_lots_and_movements`; `tests/test_fact_observation.py::test_everyday_predicates_keep_their_value_and_subject_contracts` |
