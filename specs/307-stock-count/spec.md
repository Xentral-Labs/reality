# Feature Specification: Stock Count Sessions

**Feature Branch**: `307-stock-count`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 13. Close the capability gap behind the partial journeys J02, R07, J03 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Gains and losses are recorded as reasoned adjustments, but no count record compares counted and book quantity. A gain from a count is not proven, and a count during operation cannot be shown. Since spec 304, a loss that touches blocked stock is refused.

| Journey | Title | Status today |
|---|---|---|
| J02 | Stock count with gains and losses | partial |
| R07 | Month-end count difference uncovers three reservations | partial |
| J03 | Cycle count of single bins during operation | missing |

### Scope

- A count of one location, in one or more lines. Each line is an item and, for a lot-tracked item, its lot, with the counted quantity and when it was counted.
- One reviewed confirmation records the count and posts every difference as an adjustment linked to its count line.
- The book quantity is what the movements up to the counting time hold, read at read time. Movements after it carry on unchanged, so stock is never frozen.
- A loss is taken from free stock first. What free stock does not cover is scrapped from the location's blocks, with the count as the reason.
- The review names the reservations at the location that the loss leaves uncovered. Nothing is released by itself.

### Non-Goals

- Cycle-count planning, mobile scanning, counting by pallet or serial unit.
- Freezing a location during a count.
- Choosing which reservation gives way; that stays a person's decision, as `reservation_exceeds_stock` intends.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

- Q: Is stock frozen during a count, or does operation carry on (J03)? → A: Operation carries on, with a counting time per line. Each line keeps when it was counted. The book quantity at that time is read from the movements up to it, and only the difference at that time is posted.
- Q: What is counted? → A: Items per location, and the lot where the item is lot-tracked. Pallets and serial units are out of scope.
- Q: What if a loss touches blocked stock (spec 304)? → A: The loss is taken from free stock first. Any rest is scrapped from the location's blocks with the count as the reason, and the review shows this before confirming.
- Q: How are reservations treated that a loss leaves uncovered (R07)? → A: They are named, and nothing happens by itself. The review names the reservations at the location that would no longer be covered. Afterwards `reservation_exceeds_stock` names them, and a person decides who is postponed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Count and Post (Priority: P1)

As a warehouse clerk, I count a shelf and post the differences with one confirmation.

**Why this priority**: Rank 13 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** 20 of an item and 8 of another at a location (J02), **When** 17 and 9 are counted and confirmed, **Then** an adjustment of −3 and one of +1 are recorded, each linked to its count line, and the review showed book 20/8, counted 17/9.
2. **Given** a line counted at 10:00 and a shipment of 2 at 10:30 (J03), **When** the count is confirmed at 11:00, **Then** the difference is taken against the book at 10:00, and the shipment stays as it was.
3. **Given** three reservations of 4, 4 and 4 against 12 in stock (R07), **When** a count finds 9, **Then** the review names the reservations no longer covered. After confirming, `reservation_exceeds_stock` names them, and none is released by itself.
4. **Given** 10 in stock with 4 blocked, **When** a count finds 3, **Then** 6 come off free stock and 1 is scrapped from the block, citing the count.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII). The counted quantity and counting time are kept as stated, and the book quantity is never stored.
- A line equal to the book posts nothing, but stays in the count.
- A lot-tracked item needs its lot; an untracked item names none.
- A counting time in the future is refused, and so is one before the item's first movement at the location.
- A loss that would take stock below zero now, because goods left after the count, is refused with its code.
- The same item and lot twice in one count is refused.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A count MUST record, per line, the item, the lot where tracked, the counted quantity and the counting time. The book quantity at that time is read from the movements.
- **FR-002**: Confirming a count MUST post each difference as an adjustment linked to its line. A loss is taken from free stock first, then scrapped from the location's blocks.
- **FR-005**: The count review MUST name the reservations at the location that the loss leaves uncovered.
- **FR-003**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-004**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

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
