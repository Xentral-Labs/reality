# Feature Specification: Shop Order Changes and Refunds

**Feature Branch**: `296-shop-order-changes`

**Created**: 2026-09-29

**Status**: Draft

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

- Interpret a new Shopify order version into revisions of the affected order lines where the change is unambiguous (quantity, cancellation of an open line).
- Interpret Shopify refunds into credit evidence linked to the order, independent of the goods coming back.
- Classify a cancellation after shipment as a return expectation instead of a cancellation.
- Keep known lines of an order with an unknown item and report only the unknown one.

### Non-Goals

- Marketplaces other than Shopify.
- Automatic refunds of money.
- Changing lines that already shipped.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Shop Order Changes and Refunds (Priority: P1)

As a shop operator, I see edits, cancellations and refunds from the shop reflected in Reality without reviewing each one by hand, and only ambiguous changes wait for me.

**Why this priority**: Rank 2 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** an interpreted order, **When** the shop lowers an open line's quantity, **Then** the line is revised from the new source version and the old version stays as evidence.
2. **Given** a partially refunded order, **When** the refund arrives, **Then** credit evidence for the refunded amount is recorded and linked, and no goods movement is implied.
3. **Given** a change Reality cannot interpret safely, **When** it arrives, **Then** it is held for review as today, with the reason named.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A new source version MUST revise only what it unambiguously changes and MUST keep the previous version as evidence.
- **FR-002**: A shop refund MUST be recorded as credit evidence linked to its order and MUST NOT imply a return of goods.
- **FR-003**: A cancellation of already shipped goods MUST NOT cancel the delivery promise.
- **FR-004**: Every change that is not interpreted MUST stay held for review with a coded reason.
- **FR-005**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-006**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

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

- [NEEDS CLARIFICATION: Which Shopify changes count as unambiguous for automatic revision (quantity down, line removed, address)?]
- [NEEDS CLARIFICATION: Should shop refunds create a credit note document or only credit evidence awaiting a person?]
- [NEEDS CLARIFICATION: Is automatic interpretation opt-in per source or on for every Shopify connection?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-004 | US1 | Business stories and service tests (planned) |
| FR-005, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-006, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
