# Feature Specification: Blocked Stock and Best-Before Dates

**Feature Branch**: `304-blocked-stock`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 10. Close the capability gap behind the partial journeys B05, J05, H08, H15 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

There is no blocked-stock state: quality holds, quarantine and expiry only work by moving goods to another location, and expired lots deliberately stay available.

| Journey | Title | Status today |
|---|---|---|
| B05 | Stock exists but is blocked (quality, quarantine, expiry) | partial |
| J05 | Expired stock blocked and scrapped | partial |
| H08 | Damaged goods, part to quarantine | missing |
| H15 | Quality inspection releases days later | missing |

### Scope

- A blocked quantity per item and location with a reason (quality, damage, expiry).
- Blocked stock is excluded from availability and reservation.
- Release or scrap from blocked with a reviewed action.
- Optionally block expired lots automatically.

### Non-Goals

- Full quality management workflows.
- Minimum remaining shelf life per customer (missing journey B17).
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Blocked Stock and Best-Before Dates (Priority: P1)

As a warehouse clerk, I block a damaged batch; it can no longer be reserved until quality releases it.

**Why this priority**: Rank 10 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** 20 in stock, **When** 5 are blocked for quality, **Then** 15 are available and the 5 show the reason.
2. **Given** a blocked quantity, **When** quality releases it, **Then** it is available again and the release names who and why.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A person MUST be able to block and release a quantity with a reason through a reviewed action.
- **FR-002**: Blocked quantities MUST be excluded from availability and reservation.
- **FR-003**: Blocking MUST NOT create a stock movement.
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

- [NEEDS CLARIFICATION: Should expired lots block automatically, or only be reported as today?]
- [NEEDS CLARIFICATION: Is blocking per lot, per location, or both?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
