# Feature Specification: Ship-Complete and No-Partial-Delivery Rules

**Feature Branch**: `306-ship-complete`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 12. Close the capability gap behind the partial journeys B10, M06 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

A hold can explain why reserved goods are not shipped, but no ship-complete or no-backorder rule exists for an order or a customer. A partial shipment is always possible. When a customer wants no backorders, the rest of a partly shipped order is only closed if someone remembers to do it.

| Journey | Title | Status today |
|---|---|---|
| B10 | Customer refuses partial delivery | partial |
| M06 | Customer rule: cancel backorders instead of delivering later | missing |

### Scope

- A stated delivery rule for a customer, which an order may state differently:
  - **partial allowed** (today's behaviour, the default);
  - **ship complete**: the whole order ships at once;
  - **no backorders**: what is not shipped with the first shipment is cancelled rather than delivered later.
- Readiness and every person-facing shipment path apply the rule with a coded reason.
- Two findings:
  - an order waiting only because of ship complete, which offers to lift the rule for that order with a reason;
  - an open rest under no backorders, which offers the reviewed cancellation.
- Business stories for B10 and M06.

### Non-Goals

- Cancelling a rest automatically; a person confirms every cancellation.
- Per-line completeness or a parcel limit (B11).
- Anything that requires a document status field (Constitution II). The rule is a stated term of the order, not a fulfilment state.

## Clarifications

### Session 2026-10-02

- Q: Where does the rule apply? → A: At the customer as the default; an order may state its own rule, which wins. A person states the rule for a customer or an order through the review, with a reason.
- Q: What does "complete" mean? → A: The whole order. Under ship complete an order ships only when every open line can ship its whole open quantity, all in one shipment.
- Q: What happens when an order under the rule is not complete? → A: Readiness names the reason, and a partial shipment is refused with its code. A finding shows orders that wait only because of the rule while some lines are ready. A person may lift the rule for that order with a reason, by stating partial allowed for it.
- Q: Is M06 in scope? → A: Yes, as a third rule, no backorders. After a partial shipment, a finding reports the open rest and offers the reviewed cancellation with its reason. Nothing cancels by itself.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deliver Complete Only (Priority: P1)

As a sales clerk, I mark a customer as "deliver complete only", and no partial shipment leaves for them.

**Why this priority**: Rank 12 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a ship-complete customer and an order with one line ready and one short, **When** a shipment of the ready line is prepared, **Then** it is refused naming the rule. Readiness names the missing line, and the finding reports the order as waiting for completeness.
2. **Given** the same order, **When** every line is reserved in full, **Then** one shipment with all lines is accepted and the finding clears.
3. **Given** a ship-complete customer, **When** a person states partial allowed for one order with a reason, **Then** that order ships in parts, and the customer's other orders still wait.
4. **Given** a customer without a rule, **When** a partial shipment is prepared, **Then** it is accepted as today (positive control).

### User Story 2 - No Backorders (Priority: P2)

As a sales clerk, I mark a customer as "no backorders": what cannot ship now is cancelled, not delivered later.

**Acceptance Scenarios**:

1. **Given** a no-backorder customer and an order of 10 with 6 available, **When** 6 are shipped, **Then** a finding reports the open 4 and offers the cancellation. A person confirms it with its reason, and the finding clears.
2. **Given** a no-backorder customer, **When** nothing has been shipped yet, **Then** no finding is raised.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII). The rule is stated by a person and kept as stated, and every change is a new statement with its reason.
- Without a rule, readiness, shipments and findings are unchanged.
- A cancelled or fulfilled line does not count against completeness.
- An importer recording what a source states is not refused (spec 294 FR-006); the rule binds what a person ships.
- An order's rule outranks the customer's, also when the customer's rule changes later.
- A line may ship complete in several movements of one shipment, for example from two warehouses or as serial units; the shipment as a whole carries the order.
- A shipment that was corrected away is no shipment for no backorders.
- An order kept back by a hold is not reported as waiting for completeness; the hold classes name it.
- The order's customer is the order's own party.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A customer and an order MAY state a delivery rule: partial allowed, ship complete or no backorders. The order's rule wins, and every statement keeps who stated it and why.
- **FR-002**: Under ship complete, readiness and every person-facing shipment path MUST refuse a shipment that does not carry every open line's whole open quantity, with a coded reason.
- **FR-005**: A finding MUST report orders waiting only because of ship complete, and open rests under no backorders after a partial shipment. Each offers its reviewed next step: lift the rule for the order, or cancel the rest.
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

None; see Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-002, FR-005 | US1, US2 | Business stories and service tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
