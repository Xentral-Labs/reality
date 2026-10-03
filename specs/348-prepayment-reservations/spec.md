# Feature Specification: Reservations Waiting for an Unpaid Prepayment

**Feature Branch**: `348-prepayment-reservations`

**Created**: 2026-10-03

**Status**: Accepted

**Language**: English

**Input**: Owner request ("ja mach die fünf plus M07 bis grün") to close journey B12: stock
reserved for an order whose prepayment does not arrive is withheld from every other order, and
nothing tells anybody.

## Context and Intent

### Problem

A prepayment order may be reserved before it is paid (spec 275 only blocks the shipment). The
reservation has no lapse, so the stock stays withheld for as long as nobody looks, and no finding
names it.

### Scope

- A new operational exception class, Reservation waiting for prepayment, derived at read time.
- No automatic release and no stored deadline.

### Non-Goals

- Releasing reservations automatically.
- A company-specific deadline.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-03

The owner delegated these decisions to the recommended options.

- Q: Who releases the stock? → A: A person, through the existing reservation release; the
  finding only names the case.
- Q: How long is too long? → A: A fixed week, a product constant like the other "forgotten"
  floors of the queue (stalled order, unlifted hold). A company setting can follow when a
  business needs another span.
- Q: From when is the wait counted? → A: From the oldest active reservation of the promise, since
  that is when the stock became withheld; an old unpaid order reserved yesterday has withheld
  nothing yet.
- Q: What counts as unpaid? → A: The shared readiness decision of spec 275: the remaining
  prepayment is positive. Ambiguous attribution is not reported here; readiness already names it.
- Q: One finding per order or per promise? → A: Per promise, because reservations and their
  release are per promise; each names its order.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Withheld stock comes to a person (Priority: P1)

As a sales clerk, I see which orders hold stock while their prepayment has not come, so I can
chase the payment or give the stock to another order.

**Independent Test**: Business story B12.

**Acceptance Scenarios**:

1. **Given** a prepayment order reserved and invoiced but unpaid, **When** a week has passed,
   **Then** Reservation waiting for prepayment names the order, the reserved quantity and the
   unpaid amount, and the reservation is still active.
2. **Given** a paid prepayment order, an ordinary order or an unreserved prepayment order,
   **When** a week has passed, **Then** none is reported.
3. **Given** the finding, **When** the prepayment is paid, the reservation is released or the
   order is cancelled, **Then** it is gone.

### Edge Cases

- Inside the week nothing is reported.
- A part payment keeps the finding and names the unpaid rest.
- Tenant isolation: another company sees nothing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The exception queue MUST report every open customer promise of a prepayment order
  whose active reservation is older than a week while the order's remaining prepayment is
  positive, naming the order, the reserved quantity, the waiting days and the unpaid amount.
- **FR-002**: Nothing MUST be released or changed by the finding.
- **FR-003**: The finding MUST clear when the prepayment is paid, the reservation is released or
  the promise is cancelled.
- **FR-004**: The payment decision MUST be the shared readiness decision, asked once per waiting
  order.
- **FR-005**: B12 MUST be promoted in the Business Journey Guide with executable evidence.

### Domain and Architecture Requirements

- **DR-001**: No schema change; the class is derived at read time from reservations, promises,
  orders, payment terms and readiness.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: B12 is `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Builds on spec 275 (prepayment gate) and its readiness decision; reservation release is the
  existing reviewed path.
- Sibling specs 345–347, 349 and 350 change other areas in parallel.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-002 | US1.1, US1.2 | `tests/test_prepayment_reservations.py::test_stock_reserved_for_an_unpaid_prepayment_is_reported_after_a_week` |
| FR-003 | US1.3 | `tests/test_prepayment_reservations.py::test_payment_release_or_cancellation_clears_it` |
| FR-004 | Edge cases | `tests/test_prepayment_reservations.py::test_a_part_payment_still_waits_and_names_what_is_unpaid` |
| FR-005, SC-001 | US1 | `tests/scenarios/test_catalog_prepayment_reservations.py` |
