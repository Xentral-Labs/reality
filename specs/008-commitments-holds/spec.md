# Feature Specification: Commitments and Holds Baseline

**Baseline ID**: `008-commitments-holds`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline directional promises, derived fulfilment, cancellation, and execution holds."

## Context and Intent

### Problem

Operators need one authority for what the business promised and what may currently be
executed. This baseline separates directional Commitments from optional Evidence,
derives fulfilment from physical execution, and models temporary holds without turning
Documents into operational state.

### Scope

- Customer- and supplier-delivery Commitments with parties, item, location, promised
  quantity or amount, due time, priority, and optional Evidence links.
- Fulfilled/open quantity derived from linked Movements; open, fulfilled, and cancelled
  Commitment lifecycle; cancellation with Reservation release.
- CommitmentHold for promise-specific execution control.
- PartyHold for customer-delivery control without blocking unrelated flows.
- Document hold/release as convenience over linked open Commitments.
- Tenant-scoped registers, commands, and explanation paths.

### Non-Goals

- Document-owned delivery, reservation, fulfilment, or hold status.
- Deleting fulfilled, cancelled, or released operational history.
- General workflow approvals, credit scoring, or automatic hold decisions.
- Party holds for purchasing, invoicing, payment, or non-delivery operations.
- Defining stock calculation, tracking identities, or financial settlement.

### Existing Contracts

- [`docs/features/commitments.md`](../../docs/features/commitments.md)
- [`docs/features/commitment_holds.md`](../../docs/features/commitment_holds.md)
- [`docs/features/party_delivery_holds.md`](../../docs/features/party_delivery_holds.md)
- [`docs/features/operational_fields.md`](../../docs/features/operational_fields.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

A Commitment is a tenant-scoped directional promise. Customer and supplier delivery
share one primitive with opposite parties/direction. It may link to Document or
DocumentLine Evidence or exist independently. Fulfilled quantity is calculated from
valid linked Movements; open quantity and lifecycle follow from that calculation.

A CommitmentHold links only to its Commitment and blocks Reservation and physical
Movement while active. A PartyHold links directly to a customer and blocks only
shipment against that customer's delivery Commitment. Holds remain after release for
audit. Document hold commands act over linked Commitments and do not modify Documents.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record a Directional Promise (Priority: P1)

As an operator, I can record an incoming or outgoing promise using tenant-owned
references, with or without supporting Document Evidence.

**Why this priority**: Commitments are the operational authority for future obligations.

**Independent Test**: Create customer and supplier Commitments with duplicate human
references across tenants and inspect direction, parties, due value, links, and IDs.

**Acceptance Scenarios**:

1. **Given** tenant-owned references, **When** a customer-delivery promise is created,
   **Then** it records an outgoing obligation under an opaque ID.
2. **Given** inverse parties, **When** a supplier-delivery promise is created, **Then**
   it records an incoming obligation using the same primitive.
3. **Given** no supporting Document, **When** created, **Then** the Commitment remains
   valid without fabricated Evidence.
4. **Given** a foreign-tenant reference, **When** creation is attempted, **Then** it
   fails without disclosure or linkage.

### User Story 2 - Derive Fulfilment and Cancellation (Priority: P1)

As an operator, I see partial/complete fulfilment from physical execution and can
cancel an open remainder without deleting history.

**Why this priority**: Promise state must reflect what physically happened.

**Independent Test**: Link partial/final Movements to a Commitment, then cancel a
separate reserved Commitment and inspect quantities, states, and retained records.

**Acceptance Scenarios**:

1. **Given** a promise of 30 and linked execution of 10, **When** read, **Then**
   fulfilled is 10, open is 20, and state remains open.
2. **Given** linked execution reaches promised quantity, **When** read, **Then** open is
   zero and state is fulfilled.
3. **Given** an open reserved Commitment, **When** cancelled, **Then** it is retained,
   open execution stops, and active Reservations release without changing stock.
4. **Given** historical Movements, **When** cancellation occurs, **Then** their history
   and fulfilled quantity remain intact.

### User Story 3 - Hold One Commitment (Priority: P1)

As an operator, I can temporarily stop Reservation and physical execution of one
promise for an explicit reason without cancelling it.

**Why this priority**: Operational risk needs a reversible execution block.

**Independent Test**: Hold a Commitment, attempt Reservation and Movement, release the
hold, and retry while inspecting retained hold history.

**Acceptance Scenarios**:

1. **Given** an open Commitment, **When** an allowed hold is recorded, **Then** one
   auditable CommitmentHold links only to it.
2. **Given** an active hold, **When** Reservation or linked Movement is attempted,
   **Then** execution is rejected without changing Commitment or Document status.
3. **Given** an active hold, **When** released, **Then** release time remains recorded
   and eligible execution becomes possible.
4. **Given** a Document with open Commitments, **When** document hold is invoked,
   **Then** each is held and the Document remains unchanged.

### User Story 4 - Hold Customer Delivery Only (Priority: P2)

As an operator, I can stop physical delivery to one customer while allowing Reservation
and unrelated operations to continue.

**Why this priority**: A customer delivery block must remain narrower than a promise hold.

**Independent Test**: Place a PartyHold, reserve stock, attempt linked shipment, execute
unrelated work, release the hold, and complete shipment.

**Acceptance Scenarios**:

1. **Given** an active delivery hold, **When** stock is reserved, **Then** Reservation is
   allowed.
2. **Given** a shipment linked to that customer's delivery Commitment, **When** attempted,
   **Then** it is rejected.
3. **Given** unrelated parties or a Movement without a customer Commitment, **When**
   executed, **Then** the hold does not block it.
4. **Given** release, **When** shipment retries, **Then** it may proceed and hold history
   remains.

### Edge Cases

- Execution exceeds promised quantity or uses the wrong Movement direction.
- Evidence belongs to another Document or tenant.
- Cancellation repeats or follows full fulfilment.
- Multiple active/released holds exist for one Commitment or Party.
- An unsupported reason is submitted or document hold finds no open Commitments.
- A PartyHold exists but a Movement has no Commitment identifying the customer.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Commitment MUST represent incoming supplier and outgoing customer delivery
  using one tenant-scoped primitive and opaque identity.
- **FR-002**: Parties, item, location, and optional Evidence references MUST belong to
  the same tenant.
- **FR-003**: Commitment MAY exist without Document or DocumentLine Evidence.
- **FR-004**: Fulfilled quantity MUST equal applicable linked Movements; open quantity
  MUST equal promised minus fulfilled and MUST NOT become negative.
- **FR-005**: Partial execution MUST remain open; complete execution MUST fulfil the
  Commitment without writing fulfilment state to a Document.
- **FR-006**: Cancellation MUST retain Commitment/history, stop its open execution, and
  release active Reservations.
- **FR-007**: CommitmentHold MUST link only to Commitment and retain reason, note,
  creator, creation time, and optional release time.
- **FR-008**: Active CommitmentHold MUST block Reservation and physical Movement for its
  Commitment without changing Commitment or Document state.
- **FR-009**: Document hold/release MUST be only a convenience over open linked
  Commitments and their holds.
- **FR-010**: PartyHold MUST link directly to Party and active delivery hold MUST block
  only shipment linked to that customer's delivery Commitment.
- **FR-011**: Party delivery hold MUST NOT block Reservation, purchasing, invoicing,
  payment, unrelated customers, or Movements without an identified customer Commitment.
- **FR-012**: Releasing a hold MUST preserve audit history and re-enable eligible execution.
- **FR-013**: Web/agent hold mutations MUST require confirmation; all interfaces MUST
  call shared tenant-scoped services.
- **FR-014**: Commitment views MUST derive open, fulfilled, reserved, and risk values
  from Reality and expose Evidence/Source trace.

### Domain and Traceability Requirements

- **DR-001**: Commitment is Reality and Document is optional Evidence, never lifecycle authority.
- **DR-002**: Commitment → optional DocumentLine/Document is the shortest Evidence link;
  human numbers MUST NOT be joins.
- **DR-003**: CommitmentHold → Commitment and PartyHold → Party are the shortest true
  hold links and MUST NOT duplicate provenance.
- **DR-004**: Reservation and Movement MUST enforce holds through their owning services.
- **DR-005**: Every Commitment/hold operation and aggregate MUST enforce tenant scope.

### Key Entities

- **Commitment**: Directional promise and optional Evidence provenance.
- **CommitmentHold**: Auditable temporary execution block for one Commitment.
- **PartyHold**: Auditable customer-delivery block for one Party.
- **Movement**: Append-only physical execution used to derive fulfilment.
- **Reservation**: Allocation released on cancellation and blocked by CommitmentHold.

## Reality Applicability

- **Source**: Reached through optional sourced Document Evidence; manual Commitments need
  no fabricated SourceRecord.
- **Evidence**: Optional Document/DocumentLine supports but does not own the promise.
- **Reality**: Commitment, holds, Reservation, and Movement are operational Reality.
- **Shortest links**: Commitment → optional DocumentLine/Document; CommitmentHold →
  Commitment; PartyHold → Party; Movement/Reservation → Commitment when applicable.
- **Stored/derived**: Promise, cancellation, and hold records are stored. Fulfilled,
  open, reserved, risk, and projected values are derived.
- **Shared boundary**: CLI, API, Web, Chat, and MCP use tenant-scoped services;
  interactive mutations require confirmation.
- **Web explanation**: Detail shows promise, parties, due time, holds, Reservation,
  fulfilment Movements, projections, and Source/Evidence trail.

## Success Criteria *(mandatory)*

- **SC-001**: Incoming/outgoing promises work with and without Evidence while all
  foreign-tenant relationships are rejected.
- **SC-002**: In every tested sequence, fulfilled plus open equals promised exactly.
- **SC-003**: Cancellation preserves all Commitment/Movement history and leaves zero
  active Reservations for the cancelled remainder.
- **SC-004**: Active CommitmentHolds block all tested Reservation/Movement attempts and
  permit eligible work after release.
- **SC-005**: Party delivery holds block only targeted linked shipments and do not block
  Reservation or unrelated operations.
- **SC-006**: No lifecycle or hold scenario requires Document-owned operational status.
- **SC-007**: Every displayed Commitment value is reproducible from promise, holds,
  Reservations, and linked Movements.

## Assumptions and Dependencies

- Quantities are positive Decimal values; amount-only promises need not have physical fulfilment.
- Inventory Execution owns stock, Reservation, Movement, and tracking validity.
- Risk/overdue classifications are projections over underlying Reality.
- Allowed hold reasons remain the bounded vocabulary in existing contracts.

## Open Questions

The product owner approved this baseline on 2026-08-31. Automatic credit decisions,
general approvals, and broader PartyHold types remain future change-spec scope.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-003 | Verified as-is | Commitments and Data Model contracts | `services/core.py:create_commitment` | commitment, operational-field, tenancy, and scenario tests | — |
| FR-004–FR-006 | Verified as-is | Commitments contract | fulfilment/open/cancellation services | `tests/test_inventory_and_fulfillment.py` | — |
| FR-007–FR-009 | Verified as-is | Commitment Holds contract | commitment/document hold services | `tests/test_commitment_holds.py` | — |
| FR-010–FR-012 | Verified as-is | Party Delivery Holds contract | party hold and Movement validation | `tests/test_party_delivery_holds.py` | — |
| FR-013 | Verified as-is | Holds/Web contracts; Constitution | shared services, tools, and API | hold API/tool tests | — |
| FR-014 | Verified as-is | `docs/WEB_SPEC.md:Commitments` | read models and Inspector | API, projection, and explain tests | — |
| DR-001–DR-005 | Verified as-is | Constitution; Architecture; Data Model | relationships and services | holds, tenancy, fulfilment, and Inspector tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Creation, operational-field, and tenancy tests |
| FR-004–FR-006 | US2 | Partial fulfilment and cancellation tests |
| FR-007–FR-009 | US3 | Commitment and document hold tests |
| FR-010–FR-012 | US4 | Party delivery hold tests |
| FR-013–FR-014 | US3–US4 | Confirmation, register, and Inspector tests |
| DR-001–DR-005 | All stories | Constitution and relationship review |
