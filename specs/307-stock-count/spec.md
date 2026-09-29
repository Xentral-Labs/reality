# Feature Specification: Stock Count Sessions

**Feature Branch**: `307-stock-count`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 13. Close the capability gap behind the partial journeys J02, R07, J03 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Gains and losses are recorded as reasoned adjustments, but there is no count record comparing counted and book quantity.

| Journey | Title | Status today |
|---|---|---|
| J02 | Stock count with gains and losses | partial |
| R07 | Month-end count difference uncovers three reservations | partial |
| J03 | Cycle count of single bins during operation | missing |

### Scope

- A count session per location with counted quantities.
- Differences posted as adjustments from the count.
- Reservations affected by a loss are named.

### Non-Goals

- Cycle-count planning.
- Mobile scanning.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stock Count Sessions (Priority: P1)

As a warehouse clerk, I count a shelf and post the differences with one confirmation.

**Why this priority**: Rank 13 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a count with a loss of 3, **When** it is confirmed, **Then** an adjustment of −3 is recorded citing the count, and reservations no longer covered are named.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A count MUST record counted and book quantity per item and location.
- **FR-002**: Posting a count MUST create adjustments that cite it.
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

- [NEEDS CLARIFICATION: Must stock movements be frozen during a count, or are movements after the count start carried forward?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-002 | US1 | Business stories and service tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
