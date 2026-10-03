# Feature Specification: Undeliverable, Refused and Lost Parcels

**Feature Branch**: `335-delivery-failures`

**Created**: 2026-10-02

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), round 2. Close the capability gap behind the journeys D07, D08, D09 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

- A return never reopens a kept promise (spec 079). So an undeliverable or refused parcel cannot be told from a customer return.
- A lost parcel still counts as delivered.
- There is no claim against the carrier.

| Journey | Title | Status today |
|---|---|---|
| D07 | Parcel lost, carrier insurance pays | missing |
| D08 | Parcel undeliverable, returns | missing |
| D09 | Delivery refused | missing |

### Scope

- A failed delivery of an outbound customer shipment. Its kind is undeliverable, refused or lost, and it carries a stated reason and time.
  - It reverses the shipment's movements through the existing movement correction.
  - The delivery promise is open again.
  - An undeliverable or refused parcel brings the goods back to where they left from.
  - A lost parcel writes them off there.
- For a lost parcel, an optional claim against the carrier or its insurer, as a receivable of the business partner named. An ordinary incoming payment settles it.

### Non-Goals

- Carrier API integrations and automatic tracking-status interpretation.
- A failure of one package of a multi-package shipment; the failure covers the whole shipment.
- Automatic reshipment or cancellation; a person decides with the existing tools.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

The owner delegated these decisions to the recommended options.

- Q: Does a failed delivery reopen the promise automatically, or does a person decide between reship and cancel? → A: Both, in sequence:
  - Recording the failure reopens the promise automatically. The goods did not reach the customer, so the promise is not kept.
  - The reservation is not restored. A person then reserves and ships again, or cancels the rest, with the existing tools.
- Q: How is a failed delivery told apart from a customer return? → A: It is not a return. It reverses the shipment through the movement correction that every reader already honours, so fulfilment, open quantity, billing and costing all agree. A customer return stays a return and keeps the promise kept.
- Q: Where do the goods of an undeliverable or refused parcel go? → A: Back to the location they were shipped from, in the same reviewed action. A lost parcel's goods are written off at that location in the same correction, as an adjustment with the stated reason.
- Q: Is a reason required? → A: Yes, for every kind. A refusal's reason is what D09 asks for.
- Q: How is the carrier claim recorded and settled? → A: As a receivable document `carrier_claim` of the stated business partner, the carrier or its insurer:
  - It is posted to accounts receivable against a new account role, *Carrier and insurance claims*.
  - Like a fee claim, it is an open item without a due date that is never dunned.
  - An ordinary incoming payment through the settlement flow settles it.
  - A claim is allowed for a lost parcel only.
- Q: What happens to an invoice that was already issued? → A: Nothing changes on it. The existing *Invoiced and not shipped* reports it until the order is shipped again or credited.
- Q: Is a new exception class needed? → A: No. The reopened promise appears in the existing delivery queues, and the claim in open items and party balances.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Undeliverable or Refused Parcel (Priority: P1)

As a customer service agent, I record that a parcel came back undeliverable or was refused, and send it again.

**Why this priority**: Round 2 of the sales-gap roadmap: a structural gap that several journeys share.

**Independent Test**: A business story per journey through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a shipped parcel that comes back undeliverable, **When** recorded, **Then** the promise is open again and the stock is back.
2. **Given** that reopened promise, **When** it is reserved and shipped again, **Then** it is fulfilled.
3. **Given** a refused parcel, **When** recorded with the refusal reason, **Then** the shipment shows it was refused and why, and the promise is open again.

### User Story 2 - Lost Parcel and Carrier Claim (Priority: P1)

As a bookkeeper, I record that a parcel was lost, claim it from the carrier, and see the claim settled when the carrier pays.

**Acceptance Scenarios**:

1. **Given** a lost parcel, **When** recorded with a claim, **Then** it no longer counts as delivered, the stock stays gone, and the claim is open against the carrier.
2. **Given** that claim, **When** the carrier pays it, **Then** it is settled.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII): kind, reason, time and claim amount.
- A shipment fails once. A second failure is refused, and so is a shipment with nothing left standing.
- Only an outbound customer delivery can fail. A failure time cannot lie in the future.
- A claim is refused for an undeliverable or refused parcel, and a claim without a business partner or a positive amount is refused.
- A promise that was invoiced and then failed is reported as invoiced and not shipped until it is shipped again.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A failed delivery MUST be distinct from a customer return and reopen the delivery promise.
- **FR-002**: A lost parcel MUST reverse the delivery and MAY record a claim against the carrier.
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

- Builds on shipments, movement corrections (one reversal path), fee claims (spec 318) and the settlement flow.

## Open Questions

None; see Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US1 | `tests/test_delivery_failures.py`, stories D08 and D09 |
| FR-002, FR-003 | US2 | `tests/test_delivery_failures.py`, story D07 |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review |
| FR-005, SC-001, SC-002 | All | Catalog tests and Guide questions |
