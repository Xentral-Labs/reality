# Feature Specification: Unit Conversion Between Purchase and Sales Units

**Feature Branch**: `301-unit-conversion`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 7. Close the capability gap behind the partial journeys O05 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Purchase units and conversion factors are compared in exception checks, but receipts and stock are not converted: buying cartons of 12 and selling pieces does not add up.

| Journey | Title | Status today |
|---|---|---|
| O05 | Unit conversion: buy in cartons of 12, sell in pieces | partial |

### Scope

- Receive in the purchase unit and hold stock in the base unit.
- Show purchase quantities in both units.
- Refuse a receipt whose unit has no stated conversion.

### Non-Goals

- Variable conversions (catch weight).
- Unit conversion in pricing.
- A purchase unit per supplier.
- Sales lines in another unit (selling in cartons).
- Converting purchase orders recorded before this feature.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-01

- Q: Where does the conversion from carton to piece happen? → A: The supplier promise and every receipt are held in the item's stock unit. The purchase order line keeps the quantity and unit as stated, for example 5 cartons; its promise is 60 pieces. A receipt stated in cartons is converted when it is recorded, and the movement keeps the stated quantity and unit beside the converted one. Every reader of open, received, stock, valuation and matching then works in one unit.
- Q: Is one purchase unit per item enough, or one per supplier? → A: One per item: the existing `Item.purchase_unit` and `Item.conversion_factor`. A supplier-specific pack size is a later specification.
- Q: What happens to purchase orders already recorded in a purchase unit? → A: Conversion applies to purchase orders recorded from now on. Recorded promises are not changed; open supplier promises stated in a purchase unit before the change are named, not converted.
- Q: Does the conversion apply to sales too? → A: No, purchasing only. Sales lines keep today's behaviour; selling in cartons is its own specification.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unit Conversion Between Purchase and Sales Units (Priority: P1)

As a wholesaler, I receive 5 cartons and see 60 pieces in stock.

**Why this priority**: Rank 7 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** an item bought in cartons of 12, **When** 5 cartons are received, **Then** stock rises by 60 pieces and the purchase shows 5 cartons received.
2. **Given** a receipt in a unit without a conversion, **When** it is recorded, **Then** it is refused with a coded reason.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A purchase order line stated in the item's purchase unit MUST create a supplier promise in the item's stock unit by the item's stated factor. A receipt stated in the purchase unit MUST be recorded in the stock unit by the same factor, so that stock, open quantity, valuation and invoice matching agree.
- **FR-002**: The quantity and unit as stated MUST be kept: on the purchase order line, and on the receipt beside its converted quantity. Reads of a purchase show both.
- **FR-003**: A purchase order line or a receipt in a unit the item states no conversion for MUST be refused with a coded reason. A conversion that leaves a remainder MUST be refused too.
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
| FR-001 | US1 1 | `tests/test_purchase_units.py`, story O05 (planned) |
| FR-002 | US1 1 | `tests/test_purchase_units.py` reads, inspector (planned) |
| FR-003 | US1 2 | refusal tests (planned) |
| FR-004, DR-001, DR-002 | All | `tests/test_purchase_unit_adapters.py`, diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | catalog tests and Guide questions (planned) |
