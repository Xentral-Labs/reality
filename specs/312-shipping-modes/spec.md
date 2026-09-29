# Feature Specification: Customer Pickup and Late 3PL Confirmations

**Feature Branch**: `312-shipping-modes`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 18. Close the capability gap behind the partial journeys D15, D12 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Delivery without a carrier works, but pickup is not recorded as a mode of its own; when goods left and when the 3PL confirmed it are not told apart.

| Journey | Title | Status today |
|---|---|---|
| D15 | Customer pickup | partial |
| D12 | 3PL confirms shipments late | partial |

### Scope

- Pickup as a delivery mode with who collected.
- The goods-left time separate from the confirmation time.

### Non-Goals

- 3PL integrations.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Customer Pickup and Late 3PL Confirmations (Priority: P1)

As a warehouse clerk, I record that a customer collected the goods.

**Why this priority**: Rank 18 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a pickup, **When** it is recorded, **Then** the shipment shows mode pickup and the collector.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A shipment MUST be able to state pickup as its mode.
- **FR-002**: A shipment MUST keep both the stated departure time and the confirmation time.
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

- [NEEDS CLARIFICATION: Is the collector's name needed, or only the mode?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-002 | US1 | Business stories and service tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
