# Feature Specification: Customer Item Numbers

**Feature Branch**: `308-customer-item-numbers`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 14. Close the capability gap behind the partial journeys M02 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Customer-specific prices work, but customer item numbers and names are not recorded. A B2B order that quotes the customer's own article number cannot be matched: the file import refuses an unknown SKU, and manual entry needs our item.

| Journey | Title | Status today |
|---|---|---|
| M02 | Customer-specific prices, item numbers and names | partial |

### Scope

- A customer item number, with the customer's name for it, per customer and item. One number names exactly one item at that customer; an item may have several numbers there.
- The order file import resolves a line by its customer item number. An unknown number keeps the line without an item, reported by `order_line_item_unknown`. Assigning the item there offers to remember the number for the customer.
- Manual and chat order entry (Web, MCP, CLI) accepts the customer item number instead of our item.
- The number as stated stays on the line. It is shown with the customer's name on the order, the delivery and the invoice, and the customer's numbers are listed on the customer.

### Non-Goals

- Customer numbers for Shopify orders, which quote our SKU.
- Numbers per customer group.
- Customer-specific labels or documents (M07).
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

- Q: Through which paths does a customer item number resolve a line? → A: The file import and order entry. The order import takes a customer item number column, and manual or chat entry takes the customer's number per line instead of our item. Shopify keeps our SKU.
- Q: How is the mapping kept? → A: In its own table, per customer. One number names one item at a customer, with the customer's name for it, and an item may have several numbers there. It is stated and changed through the review, and every statement is kept as a source version (spec 320 pattern).
- Q: What happens to an unknown customer number in the import? → A: The line is kept and reported, as in spec 296. It stays without an item and is reported as an order line with an unknown item. Assigning the item offers to remember the number for the customer.
- Q: Where does the number appear? → A: On order and invoice lines. The stated number stays on the line as stated, never recomputed, and is shown with the customer's name on the order, the delivery and the invoice. The customer's numbers are listed on the customer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Order by the Customer's Number (Priority: P1)

As a sales clerk, I enter an order by the customer's own article number.

**Why this priority**: Rank 14 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a mapping "K-4711 → our bike" for a customer, **When** an order line quotes K-4711, **Then** it resolves to our bike. The line keeps K-4711, and order and invoice show it with the customer's name for it.
2. **Given** an imported order whose line quotes an unknown customer number, **When** it is imported, **Then** the other lines are promised and this line is reported. Assigning the item through the review creates its promise and, on request, the mapping.
3. **Given** the same number at another customer, **When** that customer's order quotes it, **Then** it resolves only through that customer's own mapping.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII). The quoted number stays as stated on the line even after the mapping changes.
- Numbers match case- and space-insensitively within one customer; one number cannot name two items at the same customer.
- A line that states both our item and a customer number keeps our item, and the number is checked against the mapping.
- Removing a mapping leaves past lines unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A customer MAY have customer item numbers, each naming one item at that customer with the customer's name for it, stated and changed through the review.
- **FR-002**: The order file import and order entry MUST resolve a line by its customer item number. An unknown number in the import keeps the line reported, as in spec 296.
- **FR-003**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-004**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.
- **FR-005**: The stated number MUST stay on the line and be shown with the customer's name on order, delivery and invoice.

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
| FR-001, FR-002, FR-005 | US1 | Business stories and service tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
