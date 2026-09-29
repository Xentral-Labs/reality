# Feature Specification: Customer Item Numbers

**Feature Branch**: `308-customer-item-numbers`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 14. Close the capability gap behind the partial journeys M02 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Customer-specific prices work, but customer item numbers and names are not recorded, so B2B orders quoting the customer's number cannot be matched.

| Journey | Title | Status today |
|---|---|---|
| M02 | Customer-specific prices, item numbers and names | partial |

### Scope

- A customer item number and name per customer and item.
- Matching incoming orders by the customer's number.

### Non-Goals

- Customer-specific labels (missing journey M07).
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Customer Item Numbers (Priority: P1)

As a sales clerk, I enter an order by the customer's own article number.

**Why this priority**: Rank 14 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a mapping, **When** an order line quotes the customer number, **Then** it resolves to our item and keeps the stated number.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A customer item number MUST map to exactly one item per customer.
- **FR-002**: Order lines MUST keep the customer number they stated.
- **FR-003**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-004**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

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

- [NEEDS CLARIFICATION: Is this a typed mapping table or a stated fact on the party?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-002 | US1 | Business stories and service tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
