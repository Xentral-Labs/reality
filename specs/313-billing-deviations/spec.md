# Feature Specification: Over-Billing and Quantity Lowered Below Delivered

**Feature Branch**: `313-billing-deviations`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 19. Close the capability gap behind the partial journeys A05, E07 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

- **A05:** a customer lowers a line below what was already shipped. The revision is accepted and closes the promise, but nothing reports that more left than the customer now wants.
- **E07:** an invoice that differs from the order is already visible:
  - billing more than was shipped is *Invoiced and not shipped* (spec 299);
  - billing less is *Shipped and not billed*;
  - another price is *Invoice price differs*.
  - The journey still reads partial, because no story proves the three together.

| Journey | Title | Status today |
|---|---|---|
| A05 | Customer lowers the quantity below the delivered quantity | partial |
| E07 | Invoice differs from the order (quantity/price) | partial |

### Scope

- A new finding, *Shipped beyond the order*, for a customer promise whose shipments (net of what came back) exceed the quantity in force. It names the excess. It clears when the excess comes back or the quantity is revised up to what was shipped.
- A business story for E07 proving that over-billing, under-billing and a different price are each reported, using the existing classes.

### Non-Goals

- Automatic credit notes or return requests.
- The supplier side (over-receipt), which belongs to the structural gap "a movement must match its commitment exactly".
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

The owner delegated these decisions to the recommended options.

- Q: Is billing more than shipped a new class? → A: No. *Invoiced and not shipped* (spec 299) already reports it per order line. E07 is proven by a story with the existing classes.
- Q: How is the excess of a lowered line reported? → A: As a new finding, *Shipped beyond the order*, on customer promises only, of normal severity. It clears through a return of the excess or a revision back up to what was shipped. The revision itself stays accepted.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Quantity Lowered Below Delivered (Priority: P1)

As a sales clerk, I see when a customer lowered an order below what we already shipped.

**Why this priority**: Rank 19 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** 10 shipped, **When** the customer lowers the line to 8, **Then** 2 are reported as shipped beyond the order.
2. **Given** that finding, **When** 2 come back, or the line is revised to 10, **Then** it clears.

### User Story 2 - Invoice Differs From the Order (Priority: P1)

As a controller, I see every way an invoice differs from what was ordered and shipped.

**Acceptance Scenarios**:

1. **Given** 10 shipped and 12 invoiced, **When** read, **Then** 2 are reported as invoiced and not shipped.
2. **Given** 10 shipped and 8 invoiced, **Then** 2 are shipped and not billed. **Given** an invoice at another price, **Then** the price difference is reported.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).
- A cancelled promise expects nothing more: shipments on it are not beyond the order, since the cancellation applies only to the open rest.
- Quantities are compared in the promise's unit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sales MUST report billing beyond shipped quantity per order line (existing, spec 299), proven by a story.
- **FR-002**: Lowering a line below delivered MUST report the excess delivery until it comes back or the quantity is raised again.
- **FR-003**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI. This feature adds no new mutation.
- **FR-004**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan. This feature adds none.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Builds on commitment revisions, spec 299 *Invoiced and not shipped* and the return flows.

## Open Questions

None; see Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-002 | US1 | Story A05 and exception tests (planned) |
| FR-001 | US2 | Story E07 (planned) |
| FR-003, DR-001, DR-002 | All | Diff review (planned) |
| FR-004, SC-001, SC-002 | All | Catalog tests and Guide questions (planned) |
