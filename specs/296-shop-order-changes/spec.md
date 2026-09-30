# Feature Specification: Shop Order Changes and Refunds

**Feature Branch**: `296-shop-order-changes`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 2. Close the capability gap behind the partial journeys L04, L05, A16, A09, F12, A17 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Every changed, refunded or cancelled Shopify order version is held for manual review, and an order with an unknown item is not interpreted at all. Busy shops turn this into daily manual work.

| Journey | Title | Status today |
|---|---|---|
| L04 | Shopify order partially refunded in the shop | partial |
| L05 | Shopify order edited after import | partial |
| A16 | Shop sends a new version of the same order | partial |
| A09 | "Cancelled" after shipment | partial |
| F12 | Marketplace refunds first, goods later or never | partial |
| A17 | Shop order contains an unknown item | partial |

### Scope

- Apply a new Shopify order version automatically only where it reduces open, unshipped quantity: a lower quantity on an open line, a removed open line, or the cancellation of an order nothing of which has shipped.
- Hold every other change for review with a coded reason: a higher quantity, a new line, a price or address change, and anything touching shipped quantity.
- Record a Shopify refund as evidence on the order with its amount and refunded positions, without a ledger posting. A refunded position that has not shipped is reduced like an automatic change; a refunded position that has shipped and does not come back is reported as refunded but not returned.
- Hold a cancellation after shipment for review with the reason `cancelled_after_shipment` and offer the return announcement a person confirms; nothing is cancelled.
- Interpret an order with an unknown item: known lines become the order and its delivery promises; the unknown line is kept as a document line without an item and reported until a person assigns an item.

### Non-Goals

- Marketplaces other than Shopify.
- Automatic refunds of money.
- Changing lines that already shipped.
- Anything that requires a document status field (Constitution II).
- Invoices, payments or credit notes for Shopify orders; a refund stays evidence without a posting until shop orders are billed in Reality.
- Automatic increases, new lines, price or address changes.
- Creating items automatically from an unknown SKU.

## Clarifications

### Session 2026-09-29

- Q: Which Shopify changes are applied automatically? → A: Only reductions of open, unshipped quantity: a lower quantity, a removed open line, a full cancellation while nothing has shipped. Increases, new lines, price or address changes and anything on shipped quantity stay held for review.
- Q: How does a shop refund arrive while shop orders have no invoice in Reality? → A: As evidence on the order with amount and positions, without a posting. An unshipped refunded position is reduced; a shipped one that does not come back is reported as refunded but not returned.
- Q: What happens when the shop cancels an order that has shipped? → A: It is held for review with the reason `cancelled_after_shipment`, and a return announcement is offered for a person to confirm.
- Q: How is an order with an unknown item handled? → A: Known lines are interpreted; the unknown line stays as a document line without an item and is reported until a person assigns one.
- Default taken without asking: automatic interpretation applies to every Shopify source; nothing is opt-in, because only reductions of unshipped quantity are applied and everything else still waits.
- Default taken without asking: a version that changes only fields Reality does not interpret (note, tags, timestamps) is recorded without effect instead of waiting for review.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Shop Order Changes and Refunds (Priority: P1)

As a shop operator, I see edits, cancellations and refunds from the shop reflected in Reality without reviewing each one by hand, and only ambiguous changes wait for me.

**Why this priority**: Rank 2 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** an interpreted order, **When** the shop lowers an open line's quantity, **Then** the delivery promise is revised to the new quantity from the new source version, reservations above it are released, and the old version stays as evidence.
2. **Given** an interpreted order, **When** the shop removes an open line or cancels the whole order before anything shipped, **Then** the affected promises are cancelled citing the new source version.
3. **Given** a partially refunded order, **When** the refund arrives, **Then** the refund is recorded as evidence on the order with its amount and positions, nothing is posted, an unshipped refunded position is reduced, and a shipped refunded position that does not come back is reported as refunded but not returned.
4. **Given** a shipped order, **When** the shop cancels it, **Then** nothing is cancelled, the change waits with the reason `cancelled_after_shipment`, and a person can confirm a return announcement for the shipped quantity.
5. **Given** an order with one unknown SKU, **When** it arrives, **Then** the known lines become the order and its promises, the unknown line is kept without an item and reported, and assigning an item later creates its promise.
6. **Given** a change Reality does not apply (higher quantity, new line, price or address change, shipped quantity), **When** it arrives, **Then** it is held for review with a coded reason and nothing changes.
7. **Given** the same version delivered twice, or an older version after a newer one, **When** it is processed, **Then** nothing is applied twice and nothing is undone.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).
- A version that both lowers one line and raises another applies nothing and is held for review as a whole, so an order is never half applied.
- A lower quantity below what already shipped is held for review (`reduces_shipped_quantity`).
- A partly shipped line lowered to exactly what shipped closes its open rest.
- A refund with a shipping or other non-item amount records the amount as stated; only item positions affect promises.
- Two refunds on the same order are recorded once each by their Shopify identity.
- A refund arriving before the order was interpreted waits with the order.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A new Shopify order version MUST apply only reductions of open, unshipped quantity (lower quantity, removed open line, cancellation with nothing shipped), citing the new source version, and MUST keep every previous version as evidence.
- **FR-002**: A shop refund MUST be recorded as evidence on its order with the stated amount and positions, idempotent by its Shopify identity, and MUST NOT create a ledger posting or imply a return of goods.
- **FR-003**: A cancellation after shipment MUST NOT cancel the delivery promise; it MUST be held with the reason `cancelled_after_shipment`, and a person MUST be able to confirm a return announcement for the shipped quantity through the existing reviewed tool.
- **FR-004**: Every change that is not applied MUST stay held for review with coded reasons naming what was not applied; the changes of one version to delivery promises are applied completely or not at all. Refunds are separate source records and are recorded even when their order version is held.
- **FR-007**: A refunded position that has shipped and for which the shop states a return (restock type `return`) MUST be announced as an expected customer return citing the refund, so it is reported until the goods arrive or a person withdraws the announcement; a refund stating no restock records no expectation.
- **FR-008**: An order with an unknown SKU MUST be interpreted for its known lines; the unknown line MUST be kept as a document line without an item and reported, and a person MUST be able to assign an item to it, which creates its delivery promise.
- **FR-009**: Replayed or out-of-order versions MUST NOT apply a change twice or undo a later one.
- **FR-005**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-006**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.
- **DR-003**: Applied reductions MUST go through the existing commitment revision and cancellation services, so reservations, events and decision trail behave as for a person's revision.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Created as a short draft from the sales-gap roadmap; clarified with the owner on 2026-09-29.
- Builds on spec 081 (Shopify update guard), which this feature narrows rather than removes.
- Limitation: the first version of an order promises the stated `quantity`; an order first seen after an edit or a cancellation (a missed create webhook) is not corrected from `current_quantity` or `cancelled_at`.
- Builds on the capabilities and limitations recorded in `docs/scenarios/coverage.md` for the journeys in scope.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-004, FR-009 | US1 1, 2, 6, 7 | Interpretation tests and the A16/L05 stories (planned) |
| FR-002, FR-007 | US1 3 | Refund tests and the L04/F12 stories (planned) |
| FR-003 | US1 4 | The A09 story (planned) |
| FR-008 | US1 5 | The A17 story (planned) |
| FR-005, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-006, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
