# Feature Specification: Picking and Planned Outbound Deliveries

**Feature Branch**: `334-picking-and-planned-delivery`

**Created**: 2026-10-02

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), round 2. Close the capability gap behind the journeys A08, A11, A21, A24, D04, D13, M05 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Nothing exists between reservation and dispatch: no picking record, no planned outbound delivery, no address or recipient per shipment and no booked delivery slot.

| Journey | Title | Status today |
|---|---|---|
| A08 | Cancelled after picking, before shipment | missing |
| A11 | Delivery address changes after release, before shipment | missing |
| A21 | One order split across two delivery addresses | missing |
| A24 | Line added later that should ride with the open shipment | missing |
| D04 | Picking error caught before shipment | missing |
| D13 | Pallet freight with booked delivery slot | missing |
| M05 | Retail chain: central warehouse plus store delivery | missing |

### Scope

- A planned outbound delivery that groups reserved promises before dispatch, with its own recipient and address.
- Picking as a recorded step against a planned delivery; a cancellation after picking puts the stock back.
- A booked delivery slot on a planned delivery.
- Several deliveries per order to different recipients.

### Non-Goals

- Warehouse route optimisation and handheld scanning.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Picking and Planned Outbound Deliveries (Priority: P1)

As a warehouse lead, I plan, pick and then ship an order, and see where each part goes.

**Why this priority**: Round 2 of the sales-gap roadmap: a structural gap that several journeys share.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a released order, **When** it is picked, **Then** the picked quantity is visible before dispatch.
2. **Given** a picked order that is cancelled, **When** recorded, **Then** the picked stock goes back to its bin.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A planned outbound delivery MUST name its recipient and address.
- **FR-002**: Picking MUST be recordable against a planned delivery and reversible before dispatch.
- **FR-003**: An order MUST be able to go to more than one recipient.
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

- [NEEDS CLARIFICATION: Is picking a stock movement to a staging location, or a state of the planned delivery?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
