# Feature Specification: Multichannel Oversell, Deadlines and Peak Intake

**Feature Branch**: `300-multichannel-oversell`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 6. Close the capability gap behind the partial journeys B14, L02, L07 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Every unreserved promise is flagged, but there is no channel dimension and no overall 'demand exceeds stock' view; a fully reserved order close to its deadline is not flagged before it is overdue; intake throughput at peak volume is not measured.

| Journey | Title | Status today |
|---|---|---|
| B14 | Oversold across channels (shop and marketplace) | partial |
| L02 | Marketplace order shipped by us with a deadline | partial |
| L07 | Black Friday: 10,000 orders in two hours | partial |

### Scope

- An item-level view of demand exceeding available stock across channels.
- A deadline-at-risk signal before a promised date is missed.
- A measured intake throughput at 10,000 orders in two hours.

### Non-Goals

- Channel quotas (missing journey B16).
- Automatic stock sync back to shops.
- Anything that requires a document status field (Constitution II).
- A marketplace connector; marketplace orders arrive by file import or manually.
- Making intake faster than measured; a shortfall becomes a follow-up specification.

## Clarifications

### Session 2026-10-01

- Q: How does demand above stock across channels become visible (B14)? → A: As a finding per item. A new class reports an item whose open customer demand exceeds stock on hand plus confirmed incoming supply, and names the orders involved grouped by sales channel. The channel is the existing `document.sales_channel`; no new field.
- Q: When is an order with a deadline at risk before it is overdue (L02)? → A: At a fixed margin of one day. An open customer promise with a promised date less than 24 hours ahead and quantity not yet shipped is reported, even when it is fully reserved. No setting and no schema.
- Q: What must hold for 10,000 orders in two hours (L07)? → A: Measure it reproducibly in the repository (`benchmarks/ingest_cost`): 10,000 shop orders through the worker, with correct reservations. L07 is promoted only if the target is met; otherwise it stays partial with the measured figure and a follow-up.
- Q: Does this need a marketplace source (L02)? → A: No. Marketplace orders arrive by file import or manually with their channel and date; the business story proves the deadline and the channel. A marketplace connector is its own specification.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multichannel Oversell, Deadlines and Peak Intake (Priority: P1)

As an e-commerce operator, I see before a sale runs out which items are oversold across my shop and marketplace.

**Why this priority**: Rank 6 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** orders from two channels exceeding stock, **When** stock is read, **Then** the item shows demand above stock with the orders involved.
2. **Given** an order due tomorrow and not shipped, **When** read today, **Then** it is flagged as at risk before it becomes overdue.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Reality MUST report, per item, where open customer demand exceeds stock on hand plus confirmed incoming supply. The finding names the orders involved grouped by their stated sales channel, and clears when stock, supply or demand changes so that demand is covered.
- **FR-002**: Reality MUST report an open customer promise whose promised date is less than one day ahead and whose quantity has not fully shipped, whether or not it is reserved. The finding clears when the quantity ships, the promise is cancelled or its date is moved. Once the date passes, the order is reported as overdue instead and never in both classes.
- **FR-003**: Intake throughput MUST be measured reproducibly at 10,000 shop orders processed through the worker, with reservations checked for correctness. The figure and how it was measured MUST be recorded. L07 is promoted only if the orders are processed within two hours.
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

None. See Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US1 1 | `tests/test_item_oversold.py`, story B14 |
| FR-002 | US1 2 | `tests/test_deadline_due_soon.py`, story L02 |
| FR-003 | US1 | `tests/test_peak_intake_benchmark.py`, `results.md`, story L07 |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | `tests/scenarios/test_catalog_orders_and_shipments.py` (B14, L02, L07); `tests/test_business_journey_catalog.py` |
