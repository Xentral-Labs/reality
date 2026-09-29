# Feature Specification: Orders Served From Several Warehouses

**Feature Branch**: `303-multi-warehouse-orders`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 9. Close the capability gap behind the partial journeys A02, B06, D02 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

An order is entered for one warehouse, reservation and readiness are bound to the promise's location, and stock elsewhere is neither reserved nor proposed as a transfer.

| Journey | Title | Status today |
|---|---|---|
| A02 | Order with 30 lines from several warehouses | partial |
| B06 | Stock exists in the wrong warehouse | partial |
| D02 | Two warehouses, two parcels, one order | missing |

### Scope

- Reserve an order line against stock in another location.
- Propose a transfer when stock sits in the wrong warehouse.
- Ship one order from two warehouses as two packages.

### Non-Goals

- Automatic routing optimisation.
- In-transit stock (missing journey J01).
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Orders Served From Several Warehouses (Priority: P1)

As a warehouse lead, I serve one order from two warehouses without splitting it by hand.

**Why this priority**: Rank 9 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** stock split across two warehouses, **When** a line is reserved, **Then** it reserves from both and ships as two packages against one promise.
2. **Given** stock only in the wrong warehouse, **When** the order is read, **Then** a transfer is proposed.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A promise MUST be reservable against stock in more than one location.
- **FR-002**: Readiness MUST consider every location the promise may ship from.
- **FR-003**: A transfer proposal MUST be a reviewed action.
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

- [NEEDS CLARIFICATION: Which locations may serve an order: all, or a stated set per company?]
- [NEEDS CLARIFICATION: Does D02 (missing today) join this package or stay separate?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
