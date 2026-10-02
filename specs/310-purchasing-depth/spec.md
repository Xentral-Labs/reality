# Feature Specification: Supplier Confirmations, Minimum Quantities and Three-Way Match

**Feature Branch**: `310-purchasing-depth`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 16. Close the capability gap behind the partial journeys G09, G06, G12, I01 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

A confirmed quantity or date is a revision, but a confirmed price cannot be stated. Minimum order quantities and pack sizes are not recorded. A cancellation cost cannot be tied to the cancelled purchase. A clean three-way match has no positive answer; it shows only as the absence of findings.

| Journey | Title | Status today |
|---|---|---|
| G09 | Supplier confirms different quantity/price/date | partial |
| G06 | Minimum order quantity / pack size forces more | partial |
| G12 | Purchase cancelled after supplier produced | partial |
| I01 | Three-way match: purchase = receipt = invoice | partial |

### Scope

- **Confirmed price (G09):**
  - A revision of a purchase promise may state a confirmed unit price, in the unit of the order line.
  - From then on it is the agreed price: the guided supplier invoice takes it, and "invoice price differs" compares against it.
  - The order line shows the ordered and the confirmed price.
- **Minimum quantity and order multiple (G06):**
  - Per supplier and item, a reviewed statement names a minimum order quantity and an order multiple (pack size), each in the item's purchase unit. It is kept as a version of one source stream per supplier and item (spec 320 pattern).
  - Order entry and its review name a quantity below the minimum or off the multiple, and the next valid quantity. The order is not refused: the person decides.
  - Surplus becomes stock or is assigned, as today.
- **Cancellation cost (G12):**
  - The supplier's cancellation charge is recorded as a free supplier invoice with a charge line that names the cancelled purchase line.
  - Cancelled promises and charge lines are not reported as billed but not received, and not as an invoice price difference.
  - The purchase line shows its cancellation and the charge billed for it.
- **Three-way match (I01):**
  - A read per purchase order and line answers whether the line is matched: the quantity in force (ordered or confirmed) equals the quantity received net of returns, which equals the quantity billed net of credits, and the billed price equals the agreed or confirmed price.
  - Otherwise the read names the difference. It is derived at read time.

### Non-Goals

- Supplier portals and EDI order responses.
- Matching tolerances.
- Per-supplier lead times and supplier item numbers.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

- Q: How is a confirmed price stated? → A: In the commitment revision. `commitment_revise` takes a confirmed unit price in the order line's unit. It becomes the agreed price for the guided invoice and for "invoice price differs"; ordered and confirmed price are both shown.
- Q: How are minimum quantity and pack size kept, and what happens below them? → A: Per supplier and item, in a reviewed table (spec 320 pattern). The order review names the violation and the next valid quantity but does not block; surplus becomes stock or an assignment as today.
- Q: How is a cancellation cost recorded? → A: As a fee invoice with a reference: the existing free supplier invoice with a charge line naming the cancelled purchase line. Cancelled promises are left out of "billed but not received" and the price difference; the purchase shows cancellation and cost.
- Q: When is a purchase line matched? → A: Quantity and price exactly: quantity in force = received = billed, net of returns and credits, and billed price = agreed or confirmed price. A read per order and line answers "matched" or names the difference, derived at read time.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Supplier Confirmation (Priority: P1)

As a buyer, I record the supplier's confirmed quantity, date and price, and invoice against what was confirmed.

**Why this priority**: Rank 16 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a purchase of 100 at 10.00, **When** the supplier confirms 90 at 10.50 a week later, **Then** the line shows ordered 100 at 10.00 and confirmed 90 at 10.50, and an invoice at 10.50 raises no price difference.
2. **Given** that confirmation, **When** the invoice states 11.00, **Then** "invoice price differs" names 10.50 as agreed.

### User Story 2 - Minimum Quantity and Pack Size (Priority: P2)

As a buyer, I see when an order is below the supplier's minimum or off its pack size.

**Acceptance Scenarios**:

1. **Given** a minimum of 50 and a multiple of 12 for a supplier's item, **When** an order of 30 is reviewed, **Then** the review names the minimum and offers 60. Ordering 60 for a need of 30 leaves 30 as stock.

### User Story 3 - Cancellation Cost (Priority: P2)

As a buyer, I cancel a purchase the supplier had already produced and record their cancellation charge.

**Acceptance Scenarios**:

1. **Given** a cancelled purchase line, **When** the supplier's charge is recorded against it, **Then** it is posted and payable, no "billed but not received" finding appears, and the line shows the cancellation and the charge.

### User Story 4 - Three-Way Match (Priority: P1)

As a buyer, I see which purchase lines are fully matched.

**Acceptance Scenarios**:

1. **Given** a purchase, a receipt and an invoice that agree, **When** read, **Then** the line is matched.
2. **Given** a line received short or billed at another price, **When** read, **Then** it is not matched, and the read names the difference.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII). Confirmed prices and stated minimums are kept as stated.
- A confirmed price applies to invoice lines recorded after it; earlier invoices keep the price they were compared to when recorded. Their finding reads against the price in force at read time.
- A cancelled line with a charge is matched when nothing was received and only the charge was billed.
- Terms are in the item's purchase unit; a line in the stock unit is compared through the item's factor, and a line in another unit is named as not comparable.
- A price may be confirmed after everything arrived; quantity and date may not.
- A charge line billing an order line bills none of its goods, whether the line is cancelled or not.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A supplier confirmation MUST be able to state a price, which becomes the agreed price.
- **FR-002**: A three-way match MUST be answerable positively per purchase line.
- **FR-003**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-004**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.
- **FR-005**: A minimum order quantity and order multiple MAY be stated per supplier and item; order review MUST name a quantity that violates them.
- **FR-006**: A cancellation charge MUST be recordable against the cancelled purchase line without raising purchase findings.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Builds on the capabilities and limitations recorded in `docs/scenarios/coverage.md` for the journeys in scope.
- Builds on commitment revisions, spec 301 units, spec 314 stated prices and the free supplier invoice.

## Open Questions

None; see Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US1 | Story G09 and revision tests (planned) |
| FR-005 | US2 | Story G06 and supplier-terms tests (planned) |
| FR-006 | US3 | Story G12 and exception tests (planned) |
| FR-002 | US4 | Story I01 and match-read tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002 | All | Catalog tests and Guide questions (planned) |
