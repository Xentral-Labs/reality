# Feature Specification: Controlled Fact Observation

**Feature Branch**: `042-observe-facts`
**Created**: 2026-09-02
**Status**: Approved — product scope approved by the owner on 2026-09-02
**Language**: English
**Input**: "Keep Reality low-level while giving agents and developers one safe, explicit way to record source-supported Facts."

## Context and Intent

### Problem

Reality stores Facts and can display them, but its production application tools, Chat, MCP, and source interpretation paths cannot record one. Developers therefore lack an enforceable distinction between an observed statement, typed operational Reality, and an event describing a mutation. Agents could only bypass the shared tool boundary or leave the Facts register empty.

### Scope

- Define a Fact as an immutable, source-supported observation about one existing Reality subject.
- Provide one tenant-scoped, idempotent Fact-observation operation through the shared application tool boundary.
- Let Chat and MCP propose an observation and require explicit human confirmation before it is recorded.
- Restrict observations to a small machine-readable predicate vocabulary with subject and value contracts.
- Preserve an explainable Fact → SourceRecord → original payload path.
- Document when developers and agents use Facts instead of typed Reality records or Business Events.
- Publish public product guidance with a complete example of deciding, proposing, recording, tracing, and using a Fact.

### Non-Goals

- Automatically copying Party, Item, Commitment, Reservation, Movement, or LedgerEntry state into Facts.
- Treating model output, interpretation proposals, organizational claims, policies, or calculations as Facts.
- Automatically promoting a Fact into a Commitment or other typed Reality record.
- Building a generic workflow, confidence model, ontology, policy engine, or automatic source interpreter.
- Rewriting or deleting historical Facts.
- Adding arbitrary predicates without a reviewed business use case.

### Existing Contracts

- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/features/chat.md`](../../docs/features/chat.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record a source-supported observation (Priority: P1)

An application component has retained an immutable source and identified one relevant observation about an existing tenant subject. It submits the observation once and receives a stable Fact that remains traceable to the source.

**Why this priority**: This is the missing write boundary that makes the existing Fact model useful without widening the core into source-specific interpretation logic.

**Independent Test**: Record an allowed observation against an existing subject and tenant-owned SourceRecord, then verify one immutable Fact, one `fact.observed` event, and the complete source trace.

**Acceptance Scenarios**:

1. **Given** a tenant-owned SourceRecord, an existing tenant subject, and a cataloged predicate whose value is valid, **When** the observation is recorded, **Then** exactly one Fact and one `fact.observed` event persist with the shortest source link.
2. **Given** the same observation request and idempotency identity is submitted again, **When** it is processed, **Then** the original Fact is returned and no duplicate Fact or event is created.
3. **Given** a source or subject from another tenant, **When** an observation is attempted, **Then** it is rejected without disclosing the foreign record.
4. **Given** an unknown predicate, incompatible subject type, invalid value, or absent source, **When** an observation is attempted, **Then** nothing is persisted and the caller receives a specific validation failure.

### User Story 2 - Propose a Fact through an agent (Priority: P1)

An authenticated user asks Chat or an external MCP agent to retain a statement found in existing source evidence. The agent prepares a structured preview, but Reality changes only after explicit confirmation.

**Why this priority**: Agents must use the same safe application boundary as every other adapter and must not turn model output into truth.

**Independent Test**: Propose one valid observation through MCP, verify no Fact exists before confirmation, approve it, and verify the same canonical operation created the Fact exactly once.

**Acceptance Scenarios**:

1. **Given** a valid observation request, **When** Chat or MCP proposes it, **Then** a confirmation-required ChangeProposal exposes the source, subject, predicate, and value without recording a Fact.
2. **Given** an approved current proposal, **When** a human confirms it, **Then** the canonical observation operation records the Fact and event exactly once.
3. **Given** an unconfirmed, rejected, invalid, or cross-tenant proposal, **When** processing ends, **Then** no Fact is recorded.

### User Story 3 - Apply the Fact boundary consistently (Priority: P2)

A developer can determine from durable project guidance and executable catalogs whether information belongs in a Fact, a typed Reality record, a Business Event, or only the lossless SourceRecord.

**Why this priority**: A safe write command is insufficient if new adapters duplicate authoritative operational state in Facts.

**Independent Test**: Validate the application catalog and documentation examples, and verify representative operational commands continue to create their typed records and events without creating Facts.

**Acceptance Scenarios**:

1. **Given** a reservation, movement, ledger, or commitment mutation, **When** it succeeds, **Then** it creates the appropriate typed Reality and Business Event but no mirror Fact.
2. **Given** an unneeded upstream field, model hypothesis, calculated status, or process rule, **When** a developer follows the documented decision rule, **Then** it is not recorded as a Fact.

### Edge Cases

- Concurrent requests carry the same idempotency identity.
- A reused idempotency identity carries different observation content.
- A predicate value uses a semantically equivalent but noncanonical representation.
- The referenced source or subject is removed or becomes unavailable between proposal and confirmation.
- Legacy Facts without source provenance remain readable but cannot be created through the new operation.
- A source contains repeated observations with different observation times; each intentional observation uses a distinct idempotency identity.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide one canonical operation to record an immutable Fact about one existing tenant subject.
- **FR-002**: Every newly observed Fact MUST reference an existing SourceRecord owned by the same tenant.
- **FR-003**: Every observation MUST use a reviewed predicate whose contract permits the subject type and validates a canonical value type.
- **FR-004**: Every observation MUST identify its subject with an opaque tenant-scoped ID; human-readable numbers MUST NOT become identity.
- **FR-005**: Repeating an observation with the same tenant-scoped idempotency identity and identical content MUST return the original result without an additional Fact or event.
- **FR-006**: Reusing an idempotency identity with different content MUST fail without changing stored state.
- **FR-007**: A successful observation MUST append exactly one `fact.observed` Business Event in the same transaction as the Fact.
- **FR-008**: Chat and MCP MUST expose a typed Fact-observation proposal that requires explicit human confirmation before execution.
- **FR-009**: Proposal preview MUST identify the source, subject, predicate, canonical value, and observation time.
- **FR-010**: Invalid, rejected, unconfirmed, stale, or cross-tenant requests MUST persist no Fact and no successful observation event.
- **FR-011**: The Facts register and Inspector MUST show the recorded observation and retain traversal to the original SourceRecord payload.
- **FR-012**: The application reference MUST expose the supported observation command, event, and predicate vocabulary without describing unavailable behavior.
- **FR-013**: Normal typed-domain mutations MUST NOT create mirror Facts; they continue to record typed Reality and Business Events.
- **FR-014**: Public documentation MUST explain when a Fact is appropriate, when another record owns the information, how an agent proposes one, and how a user traces a confirmed example to its source.

### Domain and Traceability Requirements

- **DR-001**: The required storage chain is SourceRecord → Fact; Document/DocumentLine remain optional Evidence stages when a source was normalized into a document.
- **DR-002**: Fact links directly to SourceRecord and its subject; it MUST NOT duplicate Document, DocumentLine, or other ancestor foreign keys.
- **DR-003**: Fact is append-only observation evidence, not authority for current operational state; Commitment, Reservation, Movement, and LedgerEntry retain their existing authority.
- **DR-004**: Agent, MCP, API, CLI, and future interpreter callers MUST use the same tenant-scoped application operation and MUST NOT write Facts through the ORM.
- **DR-005**: The core validates storage invariants and vocabulary contracts; source-specific extraction, interpretation, confidence, and promotion decisions remain outside the core.

### Key Entities *(when data is involved)*

- **Fact**: An immutable tenant-scoped observation with a cataloged predicate, canonical value, observation time, source provenance, and idempotency identity.
- **SourceRecord**: The immutable, lossless source supporting the observation.
- **Fact Predicate**: A reviewed vocabulary entry defining the allowed subject type and value contract.
- **ChangeProposal**: A confirmation-required preview used by Chat and MCP before a Fact mutation.
- **Business Event**: The immutable event appended atomically when a Fact is first recorded.

## Success Criteria *(mandatory)*

- **SC-001**: A valid source-supported observation can be proposed, confirmed, displayed, and traced to its original payload in one acceptance scenario.
- **SC-002**: Across repeated and concurrent acceptance tests, one idempotency identity produces exactly one Fact and one event.
- **SC-003**: All tested missing-source, invalid-vocabulary, incompatible-subject, invalid-value, stale, and cross-tenant cases persist zero Facts and zero successful events.
- **SC-004**: Representative typed operational commands produce zero additional Facts while retaining their expected typed records and events.
- **SC-005**: Every supported predicate is discoverable in the application reference with its subject and value rules.
- **SC-006**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Existing historical Facts remain readable even if they do not satisfy the stricter new-write contract.
- The first vocabulary is deliberately small and uses existing Reality subject types; new vocabulary requires a demonstrated business scenario and catalog review.
- The existing ChangeProposal confirmation boundary is reused for Chat and MCP.
- Interpretation and automatic promotion are separate future features.

## Open Questions

None. The product scope above reflects the owner's approved low-level boundary.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-007 | US1 scenarios 1–4 | Fact service, idempotency, event, rollback, and tenant tests |
| FR-008–FR-010 | US2 scenarios 1–3 | MCP catalog, proposal, confirmation, and Chat orchestration tests |
| FR-011–FR-014 | US3 scenarios 1–2; US1 scenario 1 | API Inspector, reference catalog, public documentation contract, and regression tests |
| DR-001–DR-005 | US1–US3 and Edge Cases | Provenance, shortest-link, adapter-boundary, and domain-isolation tests |
