# Feature Specification: Over-Billing and Quantity Lowered Below Delivered

**Feature Branch**: `313-billing-deviations`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 19. Close the capability gap behind the partial journeys A05, E07 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Price differences and under-billing are visible, but invoicing a customer for more than was shipped is not reported, and lowering a line below what was delivered is accepted without reporting the excess.

| Journey | Title | Status today |
|---|---|---|
| A05 | Customer lowers the quantity below the delivered quantity | partial |
| E07 | Invoice differs from the order (quantity/price) | partial |

### Scope

- A sales-side 'billed more than shipped' finding.
- Reporting the excess when a line is lowered below its delivered quantity.

### Non-Goals

- Automatic credit notes.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Over-Billing and Quantity Lowered Below Delivered (Priority: P1)

As a controller, I see when a customer was invoiced for more than was shipped.

**Why this priority**: Rank 19 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** 10 shipped and 12 invoiced, **When** read, **Then** 2 are reported as billed beyond shipment.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sales MUST report billing beyond shipped quantity per order line.
- **FR-002**: Lowering a line below delivered MUST report the excess delivery.
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

- [NEEDS CLARIFICATION: Should lowering below delivered be refused instead of reported?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-002 | US1 | Business stories and service tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
