# Feature Specification: Ship-Complete and No-Partial-Delivery Rules

**Feature Branch**: `306-ship-complete`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 12. Close the capability gap behind the partial journeys B10, M06 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

A hold can explain why reserved goods are not shipped, but there is no ship-complete or no-partial-delivery rule per order or customer.

| Journey | Title | Status today |
|---|---|---|
| B10 | Customer refuses partial delivery | partial |
| M06 | Customer rule: cancel backorders instead of delivering later | missing |

### Scope

- A ship-complete rule per customer or order.
- Readiness refuses a partial shipment under the rule.

### Non-Goals

- Automatic backorder cancellation (missing journey M06 beyond the rule).
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ship-Complete and No-Partial-Delivery Rules (Priority: P1)

As a sales clerk, I mark a customer as 'deliver complete only', and no partial shipment leaves for them.

**Why this priority**: Rank 12 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a ship-complete customer and a partly reserved order, **When** a partial dispatch is prepared, **Then** it is refused naming the rule.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A customer or order MAY state ship-complete.
- **FR-002**: Readiness MUST refuse partial shipments under the rule with a coded reason.
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

- [NEEDS CLARIFICATION: Is ship-complete per customer, per order, or both?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-002 | US1 | Business stories and service tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
