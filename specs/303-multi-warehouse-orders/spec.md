# Feature Specification: Orders Served From Several Warehouses

**Feature Branch**: `303-multi-warehouse-orders`

**Created**: 2026-09-29

**Status**: Clarified

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 9. Close the capability gap behind the partial journeys A02, B06, D02 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

An order is entered for one warehouse, reservation and readiness are bound to the promise's location, and stock elsewhere is neither reserved nor proposed as a transfer.

| Journey | Title | Status today |
|---|---|---|
| A02 | Order with 30 lines from several warehouses | partial |
| B06 | Stock exists in the wrong warehouse | partial |
| D02 | Two warehouses, two parcels, one order | missing |

### Scope

- Reserve an order line against stock in another location.
- Propose a transfer when stock sits in the wrong warehouse.
- Ship one order from two warehouses as two packages.

### Non-Goals

- Automatic routing optimisation, or reserving across warehouses without a person naming the warehouse.
- A flag or list of locations allowed to serve orders.
- In-transit stock (missing journey J01).
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-01

- Q: Which locations may serve an order? → A: Every active location that holds stock (`is_active` and `allows_stock`). No new field is needed. The order's own location stays the first one.
- Q: How is a line reserved when its own warehouse is short? → A: Reserving takes the order's own location, as today. For the rest, the person names another location. The review shows what is available there, and nothing is distributed silently. Readiness and shipping then count every reservation at the location it holds, and a shipment leaves from where its stock is reserved.
- Q: What does Reality propose when stock sits in the wrong warehouse (B06)? → A: A new exception class, "Stock in another warehouse", one entry per open customer promise whose own location cannot cover its unreserved rest while other locations can. It names those locations and their available quantity, and offers both ways as reviewed actions: "Reserve there" and "Prepare transfer" to the order's location.
- Q: Does D02 (two warehouses, two parcels, one order) join this package? → A: Yes. One package per warehouse, both against the same promise, proven by a business story.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Orders Served From Several Warehouses (Priority: P1)

As a warehouse lead, I serve one order from two warehouses without splitting it by hand.

**Why this priority**: Rank 9 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** stock split across two warehouses, **When** the line is reserved at its own location and the rest at a named second location, **Then** the promise is ready to ship, and it ships as two packages, one from each warehouse, against the one promise.
2. **Given** stock only in the wrong warehouse, **When** exceptions are read, **Then** "Stock in another warehouse" names the location and its available quantity, and offers to reserve there or to prepare a transfer, each through the review.
3. **Given** an order with many lines across warehouses (A02), **When** each line is reserved where its stock is, **Then** readiness and shipping follow every line's reservations.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A named location that is inactive, holds no stock, or has nothing available is refused with a coded reason.
- A transfer moves stock only. It reserves nothing and changes no promise. Reserving after the transfer is the usual step.
- A reservation at another location is released, consumed by shipping and reported like any other.
- When the order's own location can cover the rest, no entry appears, even if other locations hold stock.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A promise MUST be reservable against stock at a location the person names, besides its own. The reservation MUST record that location, and only active locations holding stock qualify.
- **FR-002**: Readiness and the fulfilment queue MUST count each reservation with the stock at its own location. A shipment against the promise MUST consume the reservations at the location it leaves from.
- **FR-003**: "Stock in another warehouse" MUST be derived at read time for an open customer promise whose unreserved rest its own location cannot cover while other locations can. Reserving there and preparing a transfer MUST be reviewed actions.
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
