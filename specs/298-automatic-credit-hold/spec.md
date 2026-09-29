# Feature Specification: Automatic Credit Hold

**Feature Branch**: `298-automatic-credit-hold`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 4. Close the capability gap behind the partial journeys C07, C08, R08 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

The credit-limit finding exists, but it does not hold anything, it ignores the new order, open credits and payables, and it names all open invoices rather than the overdue ones.

| Journey | Title | Status today |
|---|---|---|
| C07 | Credit limit exceeded: order held, released by a person | partial |
| C08 | Limit exceeded by overdue items, not by order value | partial |
| R08 | Customer is also a supplier, with an overdue receivable, an open credit and a new order above the credit limit | partial |

### Scope

- Count open invoices, the new order's value and open credits against the credit limit.
- Hold a new order that would exceed the limit, with a hold reason that names the facts.
- Name the overdue items that caused it.
- Release by a named person with a reason.

### Non-Goals

- Credit insurance.
- Scoring or external credit checks.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Credit Hold (Priority: P1)

As a sales clerk, I see a new order held because the customer is over their limit, and I or a manager release it with a reason.

**Why this priority**: Rank 4 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a customer near the limit, **When** an order would exceed it, **Then** the order is held and the reason names the open, overdue and ordered amounts.
2. **Given** a held order, **When** a manager releases it with a reason, **Then** the release is recorded and the order can ship.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The credit exposure MUST combine open invoices, open order value and available credits, each shown in the reason.
- **FR-002**: An order that would exceed the limit MUST be held until released by a person.
- **FR-003**: The hold reason MUST name the overdue items.
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

- [NEEDS CLARIFICATION: Should payables to the same party (customer is also supplier) reduce the exposure?]
- [NEEDS CLARIFICATION: Does the hold apply at order entry, at reservation or only before shipment?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
