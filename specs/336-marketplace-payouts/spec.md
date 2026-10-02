# Feature Specification: Marketplace and Payment-Provider Payouts

**Feature Branch**: `336-marketplace-payouts`

**Created**: 2026-10-02

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), round 2. Close the capability gap behind the journeys L03, R04, C09, C10, C13 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Marketplace and payment-provider payouts are not matched to orders; fees, refunds and chargebacks within a payout are not allocated; authorizations, captures and cash on delivery are not recorded.

| Journey | Title | Status today |
|---|---|---|
| L03 | Marketplace payout: one payment for hundreds of orders minus fees and refunds | missing |
| R04 | Marketplace payout with 400 orders, 12 refunds, 3 chargebacks and fees | missing |
| C09 | Card/PayPal/Klarna: authorization ≠ capture | missing |
| C10 | Authorization expires before a late partial shipment | missing |
| C13 | Cash on delivery | missing |

### Scope

- A payout statement that allocates one bank payment across many orders, minus fees, refunds and chargebacks.
- Authorization and capture as separate steps, with an expired authorization reported.
- Cash on delivery tied to a shipment.

### Non-Goals

- Live marketplace APIs; the payout is imported as a source file.
- The accounting export package of spec 148.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Marketplace and Payment-Provider Payouts (Priority: P1)

As a bookkeeper, I import a marketplace payout and see which orders it paid and what it kept.

**Why this priority**: Round 2 of the sales-gap roadmap: a structural gap that several journeys share.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a payout of 400 orders minus fees, 12 refunds and 3 chargebacks, **When** imported and confirmed, **Then** each order is paid and every deduction is booked.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A payout MUST be allocated to the orders it pays, with fees, refunds and chargebacks booked.
- **FR-002**: An authorization MUST be recordable apart from its capture.
- **FR-003**: Cash on delivery MUST tie a payment to a shipment.
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

- [NEEDS CLARIFICATION: Is a payout allocated automatically by order reference with a review, or line by line by a person?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
