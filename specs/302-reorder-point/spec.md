# Feature Specification: Reorder Point and Replenishment Proposal

**Feature Branch**: `302-reorder-point`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 8. Close the capability gap behind the partial journeys G02 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

The purpose of a stock purchase can be stated, but there is no reorder point and nothing proposes a reorder.

| Journey | Title | Status today |
|---|---|---|
| G02 | Reorder for stock at reorder point | partial |

### Scope

- A reorder point and quantity per item and location.
- A replenishment proposal when available plus incoming stock falls below it.
- The proposal becomes a purchase only through a reviewed action.

### Non-Goals

- Forecasting.
- Automatic ordering without review.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reorder Point and Replenishment Proposal (Priority: P1)

As a buyer, I see which items fall below their reorder point and turn the proposal into a purchase order.

**Why this priority**: Rank 8 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** an item below its reorder point, **When** proposals are read, **Then** it is proposed with the stated reorder quantity and its current available and incoming stock.
2. **Given** a proposal, **When** the buyer confirms it, **Then** a purchase order is created through the existing reviewed order action.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An item MAY state a reorder point and quantity per location.
- **FR-002**: A proposal MUST appear when available plus incoming stock is at or below the reorder point.
- **FR-003**: A proposal MUST NOT create a purchase without a reviewed action.
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

- [NEEDS CLARIFICATION: Is the reorder point a typed field on the item (Constitution III) or a stated fact?]
- [NEEDS CLARIFICATION: Should the proposal pick the supplier from the purchase price list?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
