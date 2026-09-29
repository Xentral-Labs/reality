# Feature Specification: Invoiced Not Shipped, Down-Payment and Pro-Forma Invoices

**Feature Branch**: `299-invoiced-not-shipped`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 5. Close the capability gap behind the partial journeys E03, Q01, E11, C14 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Invoicing before delivery works, but sales have no 'invoiced but not shipped' list for month-end, there is no down-payment invoice document, and a down payment before any invoice is not tied to the order.

| Journey | Title | Status today |
|---|---|---|
| E03 | Invoice before delivery (prepayment, pro forma) | partial |
| Q01 | Month-end: shipped not invoiced, invoiced not shipped | partial |
| E11 | Down-payment invoice and final invoice | partial |
| C14 | 30 % down payment, rest before shipment | partial |

### Scope

- A sales-side 'invoiced but not shipped' finding and month-end list.
- A down-payment invoice tied to an order, and a final invoice that states the offset.
- A pro-forma document that is evidence but not a receivable.

### Non-Goals

- Revenue recognition rules.
- Tax treatment of down payments beyond stated values.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Invoiced Not Shipped, Down-Payment and Pro-Forma Invoices (Priority: P1)

As a controller, I see at month-end what was invoiced but not yet delivered, and down payments are offset on the final invoice.

**Why this priority**: Rank 5 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** an invoice for goods not yet shipped, **When** month-end is read, **Then** the line appears as invoiced but not shipped until it ships.
2. **Given** a 30 % down-payment invoice paid, **When** the final invoice is recorded, **Then** it states the offset and only the rest is open.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sales MUST report invoiced quantities that were not shipped, per order line.
- **FR-002**: A down-payment invoice MUST be linked to its order and MUST count toward prepayment readiness.
- **FR-003**: A final invoice MUST state the down payments it offsets.
- **FR-004**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-005**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Created as a short draft from the sales-gap roadmap; it must be clarified and accepted by the owner before planning.
- Builds on the capabilities and limitations recorded in `docs/scenarios/coverage.md` for the journeys in scope.

## Open Questions

- [NEEDS CLARIFICATION: Is a pro-forma invoice needed in the first step, or only down-payment invoices?]
- [NEEDS CLARIFICATION: Should the down payment be a separate document type or an invoice with a role?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
