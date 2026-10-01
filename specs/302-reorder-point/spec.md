# Feature Specification: Reorder Point and Replenishment Proposal

**Feature Branch**: `302-reorder-point`

**Created**: 2026-09-29

**Status**: Clarified

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 8. Close the capability gap behind the partial journeys G02 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

The purpose of a stock purchase can be stated, but there is no reorder point and nothing proposes a reorder.

| Journey | Title | Status today |
|---|---|---|
| G02 | Reorder for stock at reorder point | partial |

### Scope

- A reorder point and quantity per item and location.
- A replenishment proposal when available plus incoming stock falls below it.
- The proposal becomes a purchase only through a reviewed action.

### Non-Goals

- Forecasting.
- Automatic ordering without review.
- An order-up-to (maximum) level.
- A preferred supplier other than the one a purchase price list states.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-01

- Q: Is the reorder point a typed field on the item, or a stated fact? → A: A typed table, one row per item and location, holding the reorder point and the reorder quantity in the item's stock unit. Proposals filter and calculate on it every time they are read (Constitution III). Available and incoming stock are read per location.
- Q: Should the proposal pick the supplier from the purchase price list? → A: Yes. When exactly one supplier has a purchase price list that states a price for the item, the proposal names that supplier and price. When there are several, or none, the buyer chooses the supplier in the review.
- Q: Where does the proposal appear? → A: As an operational exception class, "Reorder point reached", one entry per item and location. Its action prepares a purchase order through the existing reviewed `order_create`. This reuses the inbox, the agent tools and the catalog.
- Q: Which quantity is proposed? → A: The stated reorder quantity. If the item has a purchase unit into which that quantity divides evenly, it is proposed in that unit, otherwise in the stock unit. It is never rounded.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reorder Point and Replenishment Proposal (Priority: P1)

As a buyer, I see which items fall below their reorder point and turn the proposal into a purchase order.

**Why this priority**: Rank 8 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** an item whose available plus incoming stock at a location is at or below its reorder point, **When** exceptions are read, **Then** "Reorder point reached" names the item and location. It states the reorder point, available stock, incoming stock, the proposed quantity, and the supplier and price when a purchase price list states exactly one.
2. **Given** that entry, **When** the buyer prepares and confirms the purchase order, **Then** it is created through the reviewed `order_create`. The incoming stock then covers the reorder point, and the entry disappears.
3. **Given** a reorder point, **When** it is set, changed or removed, **Then** that happens through a reviewed, tenant-scoped action shared by Web, Chat/MCP and CLI.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- An item without a reorder point is never proposed, whatever its stock.
- Several suppliers, or none, with a purchase price: the entry names no supplier, and the buyer chooses one.
- A reorder quantity that does not divide into the purchase unit is proposed in the stock unit.
- An inactive item or a non-stocked item cannot carry a reorder point.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An item MAY state one reorder point and one reorder quantity per location, both in the item's stock unit. The reorder point is zero or more; the reorder quantity is positive. Setting, changing and removing them MUST be reviewed actions.
- **FR-002**: "Reorder point reached" MUST appear for an item and location when available stock (physical minus active reservations, at that location) plus incoming stock (open supplier promises to that location) is at or below the reorder point. It MUST be derived at read time and never stored.
- **FR-003**: The entry MUST state the proposed quantity, and the supplier and price when exactly one supplier's purchase price list prices the item. A purchase MUST NOT be created without the reviewed `order_create`.
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
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
