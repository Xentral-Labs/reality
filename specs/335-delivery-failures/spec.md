# Feature Specification: Undeliverable, Refused and Lost Parcels

**Feature Branch**: `335-delivery-failures`

**Created**: 2026-10-02

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), round 2. Close the capability gap behind the journeys D07, D08, D09 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

A return never reopens a kept promise, so an undeliverable or refused parcel cannot be told from a customer return, and a lost parcel still counts as delivered; there is no carrier claim.

| Journey | Title | Status today |
|---|---|---|
| D07 | Parcel lost, carrier insurance pays | missing |
| D08 | Parcel undeliverable, returns | missing |
| D09 | Delivery refused | missing |

### Scope

- A failed delivery (undeliverable, refused) that brings the goods back and reopens the delivery promise.
- A lost parcel that reverses the delivery and records a claim against the carrier or insurer.
- The claim's settlement as a payment from the carrier.

### Non-Goals

- Carrier API integrations.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Undeliverable, Refused and Lost Parcels (Priority: P1)

As a customer service agent, I record that a parcel came back undeliverable and send it again.

**Why this priority**: Round 2 of the sales-gap roadmap: a structural gap that several journeys share.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a shipped parcel that comes back undeliverable, **When** recorded, **Then** the promise is open again and the stock is back.
2. **Given** a lost parcel, **When** recorded, **Then** it no longer counts as delivered and a carrier claim is open.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A failed delivery MUST be distinct from a customer return and reopen the delivery promise.
- **FR-002**: A lost parcel MUST reverse the delivery and record a claim against the carrier.
- **FR-003**: A claim's payment MUST settle it.
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

- [NEEDS CLARIFICATION: Does a failed delivery reopen the promise automatically, or does a person decide between reship and cancel?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
