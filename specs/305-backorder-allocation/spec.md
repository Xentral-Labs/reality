# Feature Specification: Serving Backorders on Receipt

**Feature Branch**: `305-backorder-allocation`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 11. Close the capability gap behind the partial journeys B08, H16, B07, R02, G13, B09 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

A receipt reserves nothing automatically, there is no rule for which backorder is served first, a customer-specific purchase is not reserved on arrival, and a cancelled customer order keeps its purchase assignment.

| Journey | Title | Status today |
|---|---|---|
| B08 | Receipt resolves backorders | partial |
| H16 | Receipt for a customer-specific purchase (cross-docking) | partial |
| B07 | Stock only on order (open purchase) | partial |
| R02 | Two customers wait for one item; under-delivery; key customer re-reserved; the other cancels | partial |
| G13 | Purchase reduced after the customer order was cancelled | partial |
| B09 | Receipt covers only part of the backorders | partial (added by spec 314) |

### Scope

- Propose reservations on receipt for assigned and waiting promises.
- A stated serving order (assigned first, then due date).
- End an assignment when its customer promise is cancelled.
- A dated available-to-promise answer from open purchases.
- Assigned supply split into what has arrived and what is still to come, so a partial receipt says which assigned backorders stay uncovered (B09). Spec 314 pinned today's behaviour in `tests/scenarios/test_catalog_purchasing.py::test_a_partial_receipt_leaves_the_assigned_backorders_as_they_were`: after a receipt of 4 against assignments of 3 + 3 + 3, each customer still counts 3 as protecting supply.

### Non-Goals

- Automatic reservation without review.
- Priority by customer value.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Serving Backorders on Receipt (Priority: P1)

As a warehouse lead, I receive goods and confirm which waiting orders they go to.

**Why this priority**: Rank 11 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** two waiting orders and one receipt, **When** the receipt is recorded, **Then** reservations are proposed in the stated order and confirmed by a person.
2. **Given** a customer order cancelled, **When** it had a purchase assignment, **Then** the assignment ends with the cancellation as its reason.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A receipt MUST propose reservations for waiting promises in a stated order.
- **FR-002**: A cancelled customer promise MUST end its supply assignments.
- **FR-003**: Available-to-promise MUST name the purchase and date it relies on.
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

- [NEEDS CLARIFICATION: What is the serving order: assignment, due date, order date, or a stated priority?]
- [NEEDS CLARIFICATION: Should cross-docking receipts reserve automatically for their assigned order?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
