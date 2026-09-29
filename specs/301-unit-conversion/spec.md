# Feature Specification: Unit Conversion Between Purchase and Sales Units

**Feature Branch**: `301-unit-conversion`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 7. Close the capability gap behind the partial journeys O05 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Purchase units and conversion factors are compared in exception checks, but receipts and stock are not converted: buying cartons of 12 and selling pieces does not add up.

| Journey | Title | Status today |
|---|---|---|
| O05 | Unit conversion: buy in cartons of 12, sell in pieces | partial |

### Scope

- Receive in the purchase unit and hold stock in the base unit.
- Show purchase quantities in both units.
- Refuse a receipt whose unit has no stated conversion.

### Non-Goals

- Variable conversions (catch weight).
- Unit conversion in pricing.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unit Conversion Between Purchase and Sales Units (Priority: P1)

As a wholesaler, I receive 5 cartons and see 60 pieces in stock.

**Why this priority**: Rank 7 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** an item bought in cartons of 12, **When** 5 cartons are received, **Then** stock rises by 60 pieces and the purchase shows 5 cartons received.
2. **Given** a receipt in a unit without a conversion, **When** it is recorded, **Then** it is refused with a coded reason.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Receipts in a purchase unit MUST convert to the item's base unit by the stated factor.
- **FR-002**: Stated quantities MUST be kept as stated alongside the converted quantity.
- **FR-003**: A unit without a conversion MUST be refused.
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

- [NEEDS CLARIFICATION: Is one purchase unit per item enough, or per supplier?]
- [NEEDS CLARIFICATION: Must existing stock be migrated, or does conversion apply to new receipts only?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
