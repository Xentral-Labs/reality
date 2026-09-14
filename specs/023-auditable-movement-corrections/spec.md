# Feature Specification: Auditable Movement Corrections

**Feature Branch**: `023-auditable-movement-corrections`
**Created**: 2026-08-31
**Status**: Approved by the product owner on 2026-08-31
**Language**: English
**Input**: "Close 009/FR-009 with a supported, auditable compensating-Movement correction workflow."

## Context and Intent

### Problem

Movements are immutable physical observations and the sole authority for stock. When an
operator discovers that a historical Movement has the wrong quantity, direction,
location, commitment, or tracking identity, the system currently offers no focused
correction workflow. Direct updates would destroy history, while an unrelated inventory
adjustment would not reliably correct commitment fulfilment or explain what was wrong.

Operators need one safe correction action that preserves the original Movement, records
an exact compensating Movement, optionally records the intended replacement, and makes
the complete correction chain understandable in every operational view.

### Scope

- Correct one tenant-owned historical Movement without updating or deleting it.
- Record a full compensating Movement that exactly reverses the original physical effect.
- Optionally record one replacement Movement expressing the intended physical event.
- Require a durable correction reason and explicit opaque links between the correction
  records and the original Movement.
- Recalculate stock, commitment fulfilment, tracked-identity location, projections, and
  operational exceptions from the resulting immutable Movement history.
- Provide preview/confirmation for interactive correction actions and explanation in the
  Movement register and Business Reality Inspector.
- Close the documented `009/FR-009` gap with executable tenant, atomicity, retry, and
  business-story proof.

### Non-Goals

- Updating or deleting an existing Movement.
- Editing an immutable SourceRecord or its payload.
- Automatically rewriting or recreating historical Reservations.
- Correcting LedgerEntries, costing, valuation, or financial inventory postings.
- Bulk correction of several unrelated Movements in one request.
- Warehouse task, carrier, picking, packing, or approval-policy orchestration.
- Treating a general stock adjustment as a substitute for a linked correction.

### Existing Contracts

- [`specs/009-inventory-execution/spec.md`](../009-inventory-execution/spec.md)
- [`docs/features/movements.md`](../../docs/features/movements.md)
- [`docs/features/inventory.md`](../../docs/features/inventory.md)
- [`docs/features/reservations.md`](../../docs/features/reservations.md)
- [`docs/features/commitments.md`](../../docs/features/commitments.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Void an Incorrect Movement (Priority: P1)

As an inventory operator, I can reverse an incorrect historical Movement so that its
physical and operational effects no longer count while the original record remains.

**Why this priority**: Stock cannot be trustworthy when a known error can only be hidden,
mutated, or offset by an unexplained adjustment.

**Independent Test**: Record each supported Movement type, correct it without a
replacement, and verify the original plus exact compensation, derived quantities, audit
reason, and immutable history.

**Acceptance Scenarios**:

1. **Given** an uncorrected receipt of 10 into location A, **When** an operator confirms
   a correction with a reason and no replacement, **Then** the original receipt remains,
   one linked compensation removes 10 from A, and net physical stock returns to its
   pre-receipt quantity.
2. **Given** an uncorrected shipment of 4 linked to a customer Commitment, **When** it is
   corrected without replacement, **Then** stock and fulfilled quantity both return to
   their pre-shipment values without deleting the shipment or its Reservation history.
3. **Given** a Movement that is already corrected, **When** a different second correction
   is requested for that same original, **Then** it is rejected and creates no record.
4. **Given** a Movement owned by another tenant, **When** correction is requested, **Then**
   it behaves as not found and discloses no record details.

### User Story 2 - Replace a Movement with the Intended Reality (Priority: P1)

As an inventory operator, I can correct a wrong quantity, location, commitment, or
tracking identity by atomically reversing the original and recording the intended
replacement.

**Why this priority**: Most operational errors require a corrected observation, not only
removal of the wrong one.

**Independent Test**: Correct a Movement with a replacement that changes each supported
business dimension and verify final stock, fulfilment, identity, validation, and all-or-
nothing behavior.

**Acceptance Scenarios**:

1. **Given** a receipt of 10 that should have been 7, **When** it is corrected with a
   replacement receipt of 7, **Then** the correction chain has net inbound quantity 7 and
   all inventory views agree.
2. **Given** a transfer recorded from A to B that should have gone from A to C, **When**
   the replacement is confirmed, **Then** the compensation restores A and removes the
   effect on B, the replacement moves the quantity from A to C, and total stock is
   unchanged.
3. **Given** a commitment-linked receipt or shipment with a wrong quantity or Commitment,
   **When** it is replaced, **Then** fulfilment excludes the reversed original and includes
   only the valid replacement.
4. **Given** an invalid replacement, **When** any location, stock, hold, commitment, lot,
   serial, handling-unit, quantity, or tenant rule fails, **Then** neither compensation nor
   replacement is created and the original effects remain authoritative.

### User Story 3 - Review and Explain the Correction Chain (Priority: P2)

As an operator or auditor, I can identify corrected Movements and follow the original,
compensation, optional replacement, reason, actor context, events, and source evidence.

**Why this priority**: A mathematically correct stock result is insufficient unless users
can understand why history changed and who confirmed it.

**Independent Test**: Complete a correction through an interactive surface, then inspect
all members of the chain through shared read surfaces and reproduce the net outcome.

**Acceptance Scenarios**:

1. **Given** a correctable Movement, **When** an interactive user opens the correction
   action, **Then** a preview shows the immutable original, exact compensation, optional
   replacement, resulting net effect, and required reason before confirmation.
2. **Given** a completed correction, **When** any chain member is inspected, **Then** the
   original, compensation, replacement if present, reason, timestamps, actor context,
   business events, and available SourceRecord evidence are reachable through opaque IDs.
3. **Given** a stale or repeated identical submission after a successful correction,
   **When** it is retried, **Then** the existing correction result is returned without a
   second stock, fulfilment, audit, or event effect.
4. **Given** a read-only integration, **When** it lists or inspects Movements, **Then** it
   can distinguish normal, corrected, compensating, and replacement records without
   implementing separate correction rules.

### Edge Cases

- The original is an opening stock, receipt, shipment, transfer, return, or adjustment.
- Reversing an inbound Movement would require stock that has since been consumed.
- The original or replacement is linked to a fulfilled, cancelled, or held Commitment.
- A correction changes lot, serial, or handling-unit identity after later identity moves.
- The original has immutable external SourceRecord evidence.
- A correction request contains an empty or whitespace-only reason.
- Two operators concurrently attempt to correct the same original Movement.
- A client loses the successful response and retries the identical request.
- Event or audit recording fails after validation but before completion.
- A replacement itself is later found to be wrong.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A correction MUST preserve the original Movement unchanged and MUST express
  its physical correction only through new immutable Movement records.
- **FR-002**: Every correction MUST create exactly one compensating Movement whose item,
  quantity, locations, and tracking identities exactly reverse the complete physical
  effect of the selected original Movement. The compensation MUST use the explicit
  `correction` type and inverse-specific direction rules rather than masquerading as the
  original receipt, shipment, transfer, return, opening-stock, or adjustment type.
- **FR-003**: A correction MAY atomically create one replacement Movement containing the
  intended type, quantity, locations, Commitment, SourceRecord, tracking identities, and
  occurrence time; omission of a replacement means the original is voided.
- **FR-004**: The original, compensation, and optional replacement MUST have explicit,
  durable, tenant-scoped relationships that identify their roles without relying on
  human numbers, timestamps, text matching, or event payloads.
- **FR-005**: Every correction MUST require a non-empty durable reason and MUST retain the
  correction time plus available actor context for audit and explanation.
- **FR-006**: Compensation, optional replacement, correction audit, and business events
  MUST succeed as one operation or leave no new effect.
- **FR-007**: The same original Movement MUST have at most one successful direct
  correction; a replacement is a normal immutable Movement that MAY later be corrected
  through its own correction chain, while a compensating Movement MUST NOT be directly
  correctable.
- **FR-008**: An identical retry after success MUST return the existing correction result
  without creating another Movement, event, audit record, or derived-state effect; a
  divergent or concurrent second request MUST be rejected.
- **FR-009**: A replacement MUST enforce the same tenant, item, location, stock
  eligibility, Commitment, hold, quantity, lot, serial, and handling-unit rules as normal
  physical execution. A compensation MUST enforce tenant, item, positive quantity,
  location eligibility, stock feasibility, tracking identity, exact inverse, and
  correction-role rules, all evaluated against the atomic correction outcome.
- **FR-010**: A correction MUST be rejected when its compensation would make physical
  stock or tracked-identity state impossible because later execution has consumed or
  moved the affected quantity; the rejection MUST guide the operator to correct later
  dependent Movements first.
- **FR-011**: Derived physical stock, Commitment fulfilment, tracked-identity location,
  projections, and operational exceptions MUST exclude the reversed effect and include
  the optional replacement exactly once.
- **FR-012**: Correcting a commitment-linked shipment MUST NOT recreate, delete, or
  reactivate historical Reservations; any subsequent allocation remains an explicit
  operational action.
- **FR-013**: Correcting a Movement backed by a SourceRecord MUST preserve that source and
  payload unchanged; the correction MAY reference separate direct evidence but MUST NOT
  imply that original source truth was rewritten.
- **FR-014**: Cross-tenant original, replacement, relationship, SourceRecord, Commitment,
  location, or tracking-identity references MUST fail without disclosure and create no
  record.
- **FR-015**: Interactive correction through Web, CLI, Chat, or MCP MUST present a preview
  and require explicit confirmation; transport layers MUST delegate mutation to the same
  tenant-scoped application behavior.
- **FR-016**: Movement registers and the Business Reality Inspector MUST identify
  correction role and status and expose the complete correction chain, reason, actor,
  events, derived effects, and available source evidence.
- **FR-017**: The correction capability MUST emit a distinct correction business event
  exactly once so shared projections and consumers can invalidate affected inventory,
  fulfilment, exception, register, and timeline views.

### Domain and Traceability Requirements

- **DR-001**: Movement remains the append-only physical authority; neither a mutable
  balance nor an audit/event record may substitute for the compensating Movement.
- **DR-002**: The approved shortest correction relationship is one tenant-scoped ternary
  relation whose only business-record links are direct opaque FKs to the original,
  compensating, and optional replacement Movements. It MUST NOT add or duplicate
  Document, DocumentLine, Commitment, or SourceRecord provenance.
- **DR-003**: Source → Evidence → Reality traceability MUST remain lossless: original
  SourceRecords remain immutable and each correction record exposes only its direct
  evidence links.
- **DR-004**: The durable correction relationship and reason are justified typed domain
  data because validation, idempotency, derivation, filtering, and explanation repeatedly
  act on them; other external details remain in SourceRecord payloads.
- **DR-005**: All business-table access, correction-chain traversal, validation, and
  derived calculations MUST enforce tenant scope through shared application behavior.

### Key Entities

- **Original Movement**: The immutable physical observation selected for correction.
- **Compensating Movement**: The immutable exact inverse that removes the original's
  physical and fulfilment effect and links directly to it.
- **Replacement Movement**: Optional immutable intended observation created in the same
  correction operation; it may later become the original of its own correction.
- **Correction context**: Durable reason, correction time, and available actor context
  that explain why the linked records were created.
- **Commitment**: Optional promise whose derived fulfilment reflects valid Movements net
  of compensation.
- **SourceRecord**: Optional immutable direct evidence retained without rewriting.

## Success Criteria *(mandatory)*

- **SC-001**: For every supported Movement type, a void correction restores stock and
  applicable Commitment fulfilment exactly to their values immediately before the
  original Movement.
- **SC-002**: For replacement corrections, every inventory, fulfilment, projection, and
  tracked-identity view reports exactly the net effect of the intended replacement.
- **SC-003**: 100% of successful corrections expose the original, compensation, optional
  replacement, reason, timestamps, actor context when supplied, events, and direct source
  evidence through one inspectable chain.
- **SC-004**: Invalid, cross-tenant, stale, dependent-history, and concurrent correction
  attempts create zero new Movements and zero partial audit or event effects.
- **SC-005**: Repeating an identical successful request any number of times produces one
  correction chain and one correction event.
- **SC-006**: An operator can preview, confirm, and then locate the completed correction
  from the Movement register in under two minutes without editing the original record.
- **SC-007**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- A correction reverses the complete selected Movement; partial correction is expressed
  as full compensation plus an optional replacement with the intended smaller quantity.
- Corrections apply to both manual and externally evidenced Movements because they amend
  interpreted physical Reality, not immutable source truth.
- Later dependent physical execution is corrected from newest to oldest when exact
  compensation cannot be applied safely.
- Historical Reservations remain evidence of allocation actions and are not silently
  rebuilt by inventory correction.
- Correction permissions use the product's existing authenticated tenant/operator model;
  defining new role administration is outside this feature.
- Financial consequences, when needed, are handled by the separate Ledger reversal
  workflow and are not implicitly created here.

## Open Questions

No unresolved product-scope questions remain for specification review. The full reversal
plus optional replacement model is the default because it keeps arithmetic, audit, retry,
and correction-chain semantics deterministic.

The product owner approved this specification on 2026-08-31.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-002 | US1 scenarios 1–2; US2 scenarios 1–2 | Immutable original and exact inverse stories for all Movement types |
| FR-003–FR-005 | US2 scenarios 1–3; US3 scenarios 1–2 | Void/replacement, relationship, reason, time, and actor-context proof |
| FR-006 | US2 scenario 4; event-failure edge case | Transaction rollback proof across Movements, audit, and events |
| FR-007–FR-008 | US1 scenario 3; US3 scenario 3 | Single-correction, correction-chain, retry, and concurrency proof |
| FR-009–FR-010 | US2 scenario 4; dependency edge cases | Shared invariant and newest-to-oldest dependency validation stories |
| FR-011–FR-012 | US1 scenario 2; US2 scenarios 1–3 | Stock, fulfilment, identity, projection, exception, and Reservation-history proof |
| FR-013–FR-014 | US1 scenario 4; source and tenant edge cases | Lossless source and two-tenant non-disclosure proof |
| FR-015–FR-017 | US3 scenarios 1–4 | Shared adapter, confirmation, Inspector, register, and exact-event proof |
| DR-001–DR-005 | All stories | Constitution, schema-justification, relationship, and service-boundary review |
