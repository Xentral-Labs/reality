# Feature Specification: Chargebacks, Returned Direct Debits and Payment Fees

**Feature Branch**: `297-payment-returns-fees`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 3. Close the capability gap behind the partial journeys C15, E08 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Reversing a payment reopens the receivable, but a chargeback or returned direct debit is not a recorded event, its fee is not recorded, and payment-provider fees on payouts are not recorded either.

| Journey | Title | Status today |
|---|---|---|
| C15 | Chargeback / returned direct debit after shipment | partial |
| E08 | Shipping cost, small-quantity surcharge, payment fees | partial |

### Scope

- Record a returned direct debit or chargeback as its own event against the payment it reverses.
- Record the provider fee as a separate charge.
- Reopen the receivable and make it visible for follow-up.
- Record freight and surcharges on sales invoices as separate lines (E08).

### Non-Goals

- Dispute handling with the provider.
- Marketplace payout reconciliation (see missing journey L03).
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Chargebacks, Returned Direct Debits and Payment Fees (Priority: P1)

As a receivables clerk, I record a returned direct debit with its bank fee, and the customer's open item is back with the reason.

**Why this priority**: Rank 3 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a paid invoice, **When** its direct debit comes back with a fee, **Then** the payment is reversed as a return event, the fee is recorded as a charge, and the invoice is open again.
2. **Given** a chargeback, **When** it is recorded, **Then** the reason and the provider reference are kept as stated.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A returned direct debit or chargeback MUST be recorded as an event linked to the payment it reverses.
- **FR-002**: A provider fee MUST be recorded separately and MUST NOT change the invoice amount.
- **FR-003**: The reopened receivable MUST show the return reason.
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

- [NEEDS CLARIFICATION: Is the fee charged on to the customer (a receivable) or kept as the company's expense?]
- [NEEDS CLARIFICATION: Do chargebacks arrive from sources (PSP files) or are they recorded by a person first?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
