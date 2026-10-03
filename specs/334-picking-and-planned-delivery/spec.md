# Feature Specification: Picking and Planned Outbound Deliveries

**Feature Branch**: `334-picking-and-planned-delivery`

**Created**: 2026-10-02

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), round 2, rank 21. Close the capability gap behind the journeys A08, A11, A21, A24, D04, D13, M05 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Nothing exists between reservation and dispatch. There is no picking record and no planned outbound delivery. A shipment carries no recipient or address of its own, and there is no booked delivery slot.

| Journey | Title | Status today |
|---|---|---|
| A08 | Cancelled after picking, before shipment | gap |
| A11 | Delivery address changes after release, before shipment | gap |
| A21 | One order split across two delivery addresses | gap |
| A24 | Line added later that should ride with the open shipment | gap |
| D04 | Picking error caught before shipment | gap |
| D13 | Pallet freight with booked delivery slot | gap |
| M05 | Retail chain: central warehouse plus store delivery | gap |

### Scope

- **Planned delivery:**
  - A planned outbound delivery groups customer promises of one customer before dispatch.
  - It states its recipient, its address and optionally a booked delivery slot.
  - One promise can be split across several planned deliveries, up to what is still open.
- **Revision:** A planned delivery can be revised until it is dispatched: its address, recipient, slot, staging location and lines. Every statement is kept.
- **Picking:**
  - Picking is a recorded stock movement from where a promise is reserved to the delivery's staging location. The reservation moves with the goods.
  - A put-back moves picked goods out of staging again.
- **Dispatch:** A dispatch names its planned delivery and ships exactly what the delivery carries. The shipment keeps the recipient, address and slot it used.

### Non-Goals

- Warehouse route optimisation, pick lists by bin path, waves and handheld scanning.
- Freight booking with carriers.
- A planned delivery for inbound goods.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

The owner delegated these decisions to the recommended options.

- Q: Is picking a stock movement to a staging location, or a state of the planned delivery?
  - A: A stock movement. Picking transfers the goods from the location where the promise is reserved to the planned delivery's staging location, and the promise's reservation moves with them.
  - Availability therefore stays true at both places.
  - A put-back is the reverse transfer, and while the promise is open the reservation moves back with it.
  - "Picked" is read from these movements and never stored.
- Q: What is a planned delivery?
  - A: A reviewed record grouping open customer promises of one customer, with planned quantities.
  - It names an optional recipient (a business partner such as a store of a retail chain; without one, the customer) and a stated address.
  - A booked slot is optional, and so is a staging location.
  - It has no status. Planned, picked and shipped are derived from its lines, its pick movements and its shipment.
- Q: How does an address change after release become traceable?
  - A: A revision before dispatch states the new address. Each statement of the delivery is kept as a version of its internal source.
  - The shipment keeps the address, recipient and slot it went with.
  - A dispatched delivery cannot be revised.
- Q: How does a line added later ride with the open shipment?
  - A: Adding a line to the original order document stays blocked once Reality exists.
  - A promise of the same customer, for example from a follow-up order, joins the open planned delivery through a revision and ships with it.
- Q: How is a picking error caught before shipment?
  - A: The review refuses picking more than is planned, and picking a promise that is not on the delivery.
  - A wrong recorded pick is undone by a put-back, which is a true movement of the goods back out of staging.
  - The dispatch refuses a shipment that differs from what the delivery carries.
- Q: What happens to picked goods when the promise is cancelled?
  - A: The cancellation releases the reservation as before. The goods stay in staging and the planned delivery shows them as to be put back, until a put-back moves them to a stock location.
  - The dispatch carries nothing for a cancelled promise.
  - It is refused while goods of a cancelled promise are still waiting in staging.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plan, Pick and Ship (Priority: P1)

As a warehouse lead, I plan a delivery, pick it into the packing zone and then ship it, and I see where each part goes.

**Why this priority**: Round 2 of the sales-gap roadmap: a structural gap that seven journeys share.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a reserved order, **When** it is picked into the staging location, **Then** the picked quantity is visible before dispatch, and the stock and the reservation are at staging.
2. **Given** a picked order that is cancelled, **When** the goods are put back, **Then** they are back in their bin and the delivery shows the put-back.
3. **Given** a pick of more than is planned, **When** it is reviewed, **Then** it is refused and nothing moves.
4. **Given** a planned delivery, **When** the shipment differs from what it carries, **Then** the dispatch is refused.

### User Story 2 - Recipients, Addresses and Slots (Priority: P1)

As an order manager, I send one order to several addresses, change an address before it ships, and book a slot for pallet freight.

**Acceptance Scenarios**:

1. **Given** one order, **When** its quantities are planned on two deliveries to two stores, **Then** each shipment goes to its own recipient and address.
2. **Given** a planned delivery whose address changes, **When** it is shipped, **Then** the shipment uses the new address and both statements are kept.
3. **Given** a delivery with a booked slot, **When** it is shipped, **Then** the shipment shows the slot it was booked for.
4. **Given** an open planned delivery, **When** a later promise of the same customer is added, **Then** it ships in the same shipment.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A planned quantity cannot exceed what is still open on the promise, less what other open planned deliveries already plan.
- Picking requires an active reservation where the goods are taken from, and a staging location that holds stock and differs from it.
- A put-back cannot exceed what is picked and still in staging.
- A booked slot ends after it starts.
- A dispatched delivery cannot be revised, picked or put back.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A planned outbound delivery MUST name its customer, its recipient and its address, and MAY state a booked slot.
- **FR-002**: Picking MUST be recordable against a planned delivery and reversible by a put-back before dispatch.
- **FR-003**: An order MUST be able to go to more than one recipient.
- **FR-004**: A planned delivery MUST be revisable until it is dispatched, with every statement kept.
- **FR-005**: A dispatch that names a planned delivery MUST ship exactly what it carries, and the shipment MUST keep the recipient, address and slot it used.
- **FR-006**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-007**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Builds on reservations at a named location (spec 303), the reviewed shipment tools (spec 095) and the stated shipment values of spec 312.

## Open Questions

None; see Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-003 | US2 | Stories A21, M05, D13 and service tests |
| FR-002 | US1 | Stories A08, D04 and service tests |
| FR-004 | US2 | Stories A11, A24 and service tests |
| FR-005 | US1, US2 | Dispatch tests and stories |
| FR-006, DR-001, DR-002 | All | Adapter tests and diff review |
| FR-007, SC-001, SC-002 | All | Catalog tests and Guide questions |
