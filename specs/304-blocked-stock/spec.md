# Feature Specification: Blocked Stock and Best-Before Dates

**Feature Branch**: `304-blocked-stock`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 10. Close the capability gap behind the partial journeys B05, J05, H08, H15 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

There is no blocked-stock state: quality holds, quarantine and expiry only work by moving goods to another location, and expired lots deliberately stay available.

| Journey | Title | Status today |
|---|---|---|
| B05 | Stock exists but is blocked (quality, quarantine, expiry) | partial |
| J05 | Expired stock blocked and scrapped | partial |
| H08 | Damaged goods, part to quarantine | missing |
| H15 | Quality inspection releases days later | missing |

### Scope

- A blocked quantity per item and location with a reason (quality, damage, expiry).
- Blocked stock is excluded from availability and reservation.
- Release or scrap from blocked with a reviewed action.
- Expired lots are reported as today; the finding offers to block them.
- A reviewed receipt may block part or all of what it receives.

### Non-Goals

- Full quality management workflows.
- Blocking expired lots automatically, or any first-expiring-first-out policy.
- Blocking by moving goods to a "blocked" location.
- Minimum remaining shelf life per customer (missing journey B17).
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

- Q: How is stock blocked? → A: As its own record, a stock block. It names the item, location, quantity and reason (quality, damage, expiry, inspection), and optionally the lot, handling unit or serial unit. The goods stay where they are and no movement is created. Available means physical stock less active reservations less active blocks, in every reader that reserves, ships or reports availability.
- Q: What happens to expired lots? → A: They are reported as today. The "Stock expired" finding offers "Block". Whether the company ships first-expiring first stays its own policy; nothing blocks by itself.
- Q: How is a block lifted? → A: Released, wholly or partly, with a reason, or scrapped, wholly or partly. Scrapping records a reasoned stock adjustment out of the location and consumes that part of the block. Both are reviewed actions.
- Q: Can goods be blocked at receipt (H08, H15)? → A: Yes. The reviewed receipt optionally takes a blocked part with its reason, for example 5 of 20 damaged, or all 20 awaiting inspection. The receipt and the block are created in one confirmation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Blocked Stock and Best-Before Dates (Priority: P1)

As a warehouse clerk, I block a damaged batch; it can no longer be reserved until quality releases it.

**Why this priority**: Rank 10 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** 20 in stock, **When** 5 are blocked for quality, **Then** 15 are available and reservable, and the 5 show the reason.
2. **Given** a blocked quantity, **When** quality releases it, **Then** it is available again, and the release names who released it and why.
3. **Given** a receipt of 20 with 5 damaged (H08), **When** it is confirmed with 5 blocked for damage, **Then** 20 are in stock and 15 available, and the 5 can later be scrapped.
4. **Given** a receipt awaiting inspection (H15), **When** all of it is received blocked for inspection, **Then** nothing is available until quality releases it days later.
5. **Given** an expired lot in stock (J05), **When** the finding is read, **Then** it offers to block the lot, and the blocked lot can then be scrapped.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A block cannot exceed what is physically there and not already blocked; stock reserved for an order cannot be blocked until that reservation is released.
- A block on a lot, handling unit or serial unit covers exactly that identity.
- Moving or shipping blocked stock is refused while the block stands.
- Releasing or scrapping more than is blocked is refused.
- A receipt blocks at most what it receives. A movement correction may not take blocked stock, and a scrap is undone by recording the goods again, not by correcting it.
- A block on a lot holds the lot wherever it lies at the location, also on a pallet.
- Recorded limitations:
  - A stock count that finds blocked goods missing needs the block released or scrapped first.
  - Practice companies cannot block yet.
  - The web blocks by lot ID; serial-tracked items are blocked through MCP or the CLI.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A person MUST be able to block a quantity with a reason, and to release or scrap it wholly or partly, through reviewed actions. A reviewed receipt MAY block part or all of what it receives.
- **FR-002**: Blocked quantities MUST be excluded from availability, reservation, shipment and transfer, and every availability reader MUST use the same rule.
- **FR-003**: Blocking and releasing MUST NOT create a stock movement. Scrapping records one reasoned adjustment.
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
| FR-001, FR-003 | US1 1–5 | `tests/test_stock_blocks.py`, `tests/test_stock_block_adapters.py` |
| FR-002 | US1 1, 4 | `tests/test_stock_block_readers.py` |
| FR-004, DR-001, DR-002 | All | `tests/test_stock_block_adapters.py`; diff review (T016) |
| FR-005, SC-001, SC-002 | US1 | stories B05, H08, H15, J05; `tests/test_business_journey_catalog.py` |
