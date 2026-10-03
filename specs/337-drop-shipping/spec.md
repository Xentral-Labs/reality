# Feature Specification: Drop Shipping

**Feature Branch**: `337-drop-shipping`

**Created**: 2026-10-03

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), round 3. Close the capability gap behind the journeys D10, D11, G15 and R03 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

A customer order can only be kept by a movement out of the company's own stock. A supplier shipping straight to the customer cannot be recorded: the purchase order is received into stock that never arrives, and the customer order waits for a shipment that never leaves the warehouse.

| Journey | Title | Status today |
|---|---|---|
| D10 | Drop shipping: supplier ships directly | missing |
| D11 | Partial drop shipping: part own stock, part supplier | missing |
| G15 | Drop-ship purchase order for a customer order | missing |
| R03 | Drop shipment with wrong item; customer returns it to us instead of the supplier | missing |

### Scope

- A drop-ship purchase order: a purchase order that states the customer as where the goods go, assigned to the customer's order line.
- The supplier's dispatch, recorded through one reviewed action, keeps both the purchase and the customer order without touching stock.
- One customer order served partly from stock and partly by the supplier.
- A drop-shipped return that comes back to the company and is credited on both sides.

### Non-Goals

- Supplier portals, EDI dispatch advices or carrier APIs. The supplier's dispatch is stated through the reviewed action.
- Creating the purchase order from the sales order in one step. The purchase order and the assignment are recorded with the existing reviewed tools.
- Naming the item a supplier actually shipped when it differs from the ordered one (D05, H06).
- Costing a drop-shipped line from its purchase price in the contribution read.
- Taking a drop-ship line out of the warehouse's fulfillment queue before the supplier ships. The queue is a cached projection refreshed by events, and an assignment emits none; until the dispatch is recorded the line reads as not reserved there, while the at-risk finding is not raised.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-03

The owner delegated these decisions to the recommended options.

- Q: How is a drop-ship purchase linked to the customer order? → A: Through the existing supply assignment for customer demand. It already names the purchase promise and the customer promise it serves, with the quantity; no new link is needed.
- Q: What makes a purchase order a drop-ship order? → A: The purchase order states the customer as its ship-to party. That stated value is the statement that the supplier ships to the customer, not to the company.
  - Only such a purchase can be recorded as drop-shipped.
  - Its supply is not incoming stock, and the customer demand it covers is not a shortage.
- Q: How does the supplier's dispatch keep both promises? → A: With one reviewed action that records one statement and two movements under it: a receipt for the purchase and a shipment for the customer, both without a location. Received, shipped, billing, crediting and supplier invoice matching read them like any other movement; stock and availability never see them.
- Q: Does the drop shipment create a shipment record? → A: Yes. A customer shipment with the stated carrier and tracking number, so the customer's question "where is my parcel" has the same answer as for any other shipment.
- Q: Where does a drop-shipped return go? → A: To the company's warehouse, as an ordinary customer return. From then on the company owns the goods; a return to the supplier against the drop-ship purchase and the two credit notes settle both sides with the existing tools.
- Q: Is R03 supported? → A: Partly. Ownership and credits on both sides are proven; naming the wrong item the supplier sent is the separate gap D05, so R03 stays partial.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Drop-Ship a Customer Order (Priority: P1)

As a merchant without stock of an item, I order it from the supplier for the customer and record when the supplier shipped it.

**Why this priority**: Round 3 of the sales-gap roadmap: drop shipping is everyday practice for e-commerce merchants, and four journeys share the gap.

**Independent Test**: A business story per journey through the reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a customer order of 4 and a purchase order of 4 shipping to the customer, assigned to the order line, **When** read, **Then** the customer order is not at risk, and nothing is incoming to the warehouse.
2. **Given** the supplier states that it shipped 4 with a tracking number, **When** recorded, **Then** both orders are delivered, the stock is unchanged, and the customer's shipment shows the tracking number.
3. **Given** the drop shipment, **When** the customer and the supplier invoice arrive, **Then** nothing is left open on either side.

### User Story 2 - Part From Stock, Part From the Supplier (Priority: P1)

**Acceptance Scenarios**:

1. **Given** an order of 10 with 6 in stock and 4 drop-shipped, **When** both shipments are recorded, **Then** the order is delivered in full and the stock is 0.

### User Story 3 - A Drop-Shipped Return Comes to Us (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a drop-shipped and invoiced order, **When** the customer returns the goods to the company, **Then** they are in stock and reported until credited. **When** the company sends them to the supplier, **Then** they are reported until the supplier credits them.

### Edge Cases

- A purchase that does not ship to the customer is refused as a drop shipment.
- A purchase assigned to several customer lines names the one the supplier shipped.
- A drop shipment cannot exceed the assignment, nor what either order still has open.
- A stated time in the future is refused.
- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A drop-ship purchase MUST be linked to the customer order line it serves, and its supply MUST NOT count as incoming stock or leave the customer demand reported as a shortage.
- **FR-002**: The supplier's stated dispatch MUST keep the purchase and the customer order without changing stock, with a customer shipment carrying the stated carrier and tracking number.
- **FR-003**: One customer order MUST be keepable by own stock and a drop shipment together.
- **FR-004**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-005**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide; R03 is `partial` with its limitation named.

## Assumptions and Dependencies

- Builds on the supply assignment for customer demand (spec 305), the shipment record (specs 312, 334) and the return and credit classes.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US1 | `tests/test_drop_shipping.py`; story G15 |
| FR-002 | US1 | `tests/test_drop_shipping.py`; story D10 |
| FR-003 | US2 | Story D11 |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review |
| FR-005, SC-001, SC-002 | All | Story R03; catalog tests and Guide questions |
