# Feature Specification: Supplier Confirmations, Minimum Quantities and Three-Way Match

**Feature Branch**: `310-purchasing-depth`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 16. Close the capability gap behind the partial journeys G09, G06, G12, I01 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

A confirmed quantity or date is a revision, but a confirmed price cannot be stated; minimum order quantities and pack sizes are not recorded; cancellation costs cannot be recorded; a clean three-way match has no positive answer.

| Journey | Title | Status today |
|---|---|---|
| G09 | Supplier confirms different quantity/price/date | partial |
| G06 | Minimum order quantity / pack size forces more | partial |
| G12 | Purchase cancelled after supplier produced | partial |
| I01 | Three-way match: purchase = receipt = invoice | partial |

### Scope

- State a confirmed price on a supplier confirmation.
- Minimum order quantity and pack size per supplier item.
- Cancellation cost as a charge.
- A positive 'matched' answer for purchase, receipt and invoice.

### Non-Goals

- Supplier portals.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Supplier Confirmations, Minimum Quantities and Three-Way Match (Priority: P1)

As a buyer, I record the supplier's confirmed price and see which purchases are fully matched.

**Why this priority**: Rank 16 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a confirmation with a different price, **When** recorded, **Then** the purchase line shows ordered and confirmed price.
2. **Given** purchase, receipt and invoice agree, **When** read, **Then** the line shows as matched.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A supplier confirmation MUST be able to state a price.
- **FR-002**: A three-way match MUST be answerable positively per purchase line.
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

- [NEEDS CLARIFICATION: Which of the four parts has the highest priority to build first?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-002 | US1 | Business stories and service tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
