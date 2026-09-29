# Feature Specification: Dunning Run and Escalation

**Feature Branch**: `295-dunning-run`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 1. Close the capability gap behind the partial journeys N04 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Dunning notices at levels 1 to 3 with a fee can only be created one by one. There is no run over overdue open items, no escalation from one level to the next and no handover to collection, so every B2B company has to track reminders outside Reality.

| Journey | Title | Status today |
|---|---|---|
| N04 | Dunning in three levels, then collection | partial |

### Scope

- A reviewed dunning run proposes notices for overdue open items by level.
- A notice escalates to the next level after a stated waiting period.
- A final level can hand an item to collection as a recorded decision.
- Blocked items (disputed, paid after the run, credit available) are left out and named.

### Non-Goals

- Sending letters or emails.
- Interest calculation.
- Integration with a collection agency.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dunning Run and Escalation (Priority: P1)

As a receivables clerk, I run dunning over all overdue items and confirm the proposed notices, so no overdue invoice is forgotten.

**Why this priority**: Rank 1 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** overdue open items at different ages, **When** a dunning run is prepared, **Then** each item is proposed at the level its last notice and waiting period allow, and nothing is recorded before confirmation.
2. **Given** an item paid or credited after the run was prepared, **When** the run is confirmed, **Then** that item is skipped and named.
3. **Given** an item at the last level, **When** the clerk hands it to collection, **Then** the handover is a recorded decision with a reason.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A dunning run MUST propose notices only for overdue, unsettled open items and MUST record nothing before confirmation.
- **FR-002**: Each proposed notice MUST state its level, fee and the waiting period that allowed it.
- **FR-003**: Escalation MUST follow the tenant's stated level sequence and waiting periods.
- **FR-004**: Handing an item to collection MUST be a reviewed decision and MUST stop further notices for it.
- **FR-005**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-006**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

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

- [NEEDS CLARIFICATION: Where are dunning levels, fees and waiting periods configured: per company, per payment term or per party group?]
- [NEEDS CLARIFICATION: Does a run cover all customers or a selection, and is it scheduled or started by a person?]
- [NEEDS CLARIFICATION: Which existing record states 'handed to collection', or is a new one needed?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-004 | US1 | Business stories and service tests (planned) |
| FR-005, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-006, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
