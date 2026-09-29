# Feature Specification: EDI Order Changes

**Feature Branch**: `311-edi-order-changes`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 17. Close the capability gap behind the partial journeys M04, R05 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

An order line can be revised by hand, but EDI order changes (ORDCHG) and shipping advices are not read.

| Journey | Title | Status today |
|---|---|---|
| M04 | ORDCHG after confirmation | partial |
| R05 | EDI customer sends ORDCHG after a partial delivery was advised | partial |

### Scope

- Interpret ORDCHG into revisions of open lines.
- Respect quantities already shipped or advised.

### Non-Goals

- The full EDI chain (missing journey M03).
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - EDI Order Changes (Priority: P1)

As a supplier to retail, I receive an order change by EDI and the open lines follow it.

**Why this priority**: Rank 17 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a partly shipped line, **When** an ORDCHG lowers it, **Then** the open rest is revised and the shipped part stays.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An ORDCHG MUST revise only open quantities and MUST keep the message as evidence.
- **FR-002**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-003**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

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

- [NEEDS CLARIFICATION: Which EDI format and channel is the first target (EDIFACT via which provider)?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-001 | US1 | Business stories and service tests (planned) |
| FR-002, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-003, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
