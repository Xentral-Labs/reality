# Feature Specification: Explain and Projections Baseline

**Baseline ID**: `013-explain-projections`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline tenant-scoped explanation, derived exceptions, business events, and rebuildable operational projections."

## Context and Intent

### Problem

Operators need fast operational views without losing the ability to explain every
number and exception from authoritative records. This baseline defines explanation,
derived exception, event, and projection behavior while keeping projections disposable.

### Scope

- Structured Commitment and Document explanation through opaque links.
- Derived operational exceptions and exact exception explanation.
- Tenant-scoped ordered BusinessEvents emitted transactionally with domain changes.
- Rebuildable materialized fulfillment, blocker, supply/demand, inventory, issue,
  commitment-register, and tenant-usage projections.
- Projection checkpoints, refresh, stale-row removal, and authoritative fallback trace.
- Web/CLI/tool/MCP read paths over shared services.

### Non-Goals

- Making BusinessEvent or Projection the authority for stock, fulfilment, or finance.
- Editable/acknowledgeable exception tickets, assignment, or manual closure.
- A general event-sourcing architecture or external broker.
- Persisting exception lifecycle before a proven use case.
- Linking records by document number or other human identifier.

### Existing Contracts

- [`docs/features/explain.md`](../../docs/features/explain.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

Explanation traverses tenant-scoped opaque relationships from Reality through Evidence
to Source and explicitly reports absent Source/Evidence. BusinessEvents announce domain
changes in transaction order but do not replace changed records. Materialized
projections are derived per tenant, checkpointed against event sequence, refreshed from
authoritative services, and remove stale rows.

Operational exceptions are derived conditions with direct explanation, not mutable
tickets. Current executable coverage strongly proves commitment shortage/risk flows;
the complete documented initial exception-class list does not yet have one focused
proof per class and remains a visible coverage gap.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explain One Operational Record (Priority: P1)

As an operator, I can inspect a Commitment or Document and trace its values through
Reality, Evidence, and Source.

**Why this priority**: Explainability is the product's trust boundary.

**Independent Test**: Explain sourced and manual Commitments plus a sourced Document,
then attempt the same opaque ID from another tenant.

**Acceptance Scenarios**:

1. **Given** a sourced Commitment, **When** explained, **Then** promise, parties, item,
   location, Reservations, Movements, quantities, Evidence, and raw Source are returned.
2. **Given** no Document/Source, **When** explained, **Then** absence is explicit and the
   operational record remains explainable.
3. **Given** a foreign-tenant ID, **When** explained, **Then** it returns not found.

### User Story 2 - Work a Derived Exception (Priority: P1)

As Head of Operations, I can read a prioritized derived queue and explain the exact
records causing an issue.

**Why this priority**: Exceptions are actionable only when their cause is reproducible.

**Independent Test**: Create uncovered customer demand, read exceptions, explain its
record ID, remediate through a normal action, and verify it disappears.

**Acceptance Scenarios**:

1. **Given** insufficient Reservation, **When** exceptions load, **Then** a derived issue
   identifies the affected Commitment and uncovered amount.
2. **Given** an exception ID, **When** explained, **Then** underlying Reality/Evidence is
   returned without manual ticket state.
3. **Given** the cause is remediated, **When** refreshed, **Then** the exception clears by derivation.

### User Story 3 - Read Rebuildable Operational Views (Priority: P1)

As an operator, I can use fast registers that stay consistent with authoritative Reality.

**Why this priority**: Performance views must never become competing truth.

**Independent Test**: Create, reserve, release, and cancel a Commitment; read every
projection and compare rows/checkpoints with authoritative values.

**Acceptance Scenarios**:

1. **Given** new domain events, **When** a projection is read/refreshed, **Then** its
   checkpoint reaches the latest tenant event sequence.
2. **Given** Reservation changes, **When** refreshed, **Then** readiness/blocker rows change accordingly.
3. **Given** cancellation removes a record from a view, **When** refreshed, **Then** the
   stale projection row is deleted without deleting authoritative history.

### User Story 4 - Audit Domain Change Announcements (Priority: P2)

As a reviewer, I can inspect ordered tenant-scoped BusinessEvents that commit or roll
back with the business transaction.

**Why this priority**: Projection refresh and activity views need reliable announcements.

**Independent Test**: Execute successful and failing domain changes and compare records,
event order, payload subjects, and rollback behavior.

**Acceptance Scenarios**:

1. **Given** successful changes, **When** committed, **Then** ordered tenant-scoped events
   identify their subjects and actions.
2. **Given** a transaction rolls back, **When** inspected, **Then** neither domain change
   nor its event remains.
3. **Given** another tenant, **When** events/projections are read, **Then** no foreign data appears.

### Edge Cases

- Explanation reaches a deleted/stale optional link.
- No Source/Evidence chain exists.
- Projection checkpoint is behind, missing, or has stale rows.
- Several events share a transaction and must retain deterministic order.
- An exception cause changes between list and explain.
- A documented exception class has no current derivation implementation/proof.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Explanation MUST traverse opaque tenant-scoped links and expose inputs,
  derived quantities, applicable Evidence, Source metadata, and raw payload.
- **FR-002**: Records without Source/Evidence MUST remain explainable and explicitly
  report that absence; foreign IDs MUST return not found.
- **FR-003**: Operational exceptions MUST derive from authoritative Reality and MUST NOT
  require manual acknowledgement, closure, or ticket state.
- **FR-004**: Exception list and detail MUST identify the exact underlying records and
  available remediation through normal application actions.
- **FR-005**: Every documented initial exception class MUST have a deterministic
  derivation and focused executable proof.
- **FR-006**: BusinessEvents MUST be tenant-scoped, ordered, descriptive announcements
  and MUST commit/rollback atomically with their domain change.
- **FR-007**: BusinessEvents MUST NOT replace Source, Evidence, or Reality authority.
- **FR-008**: Materialized projections MUST be rebuildable from authoritative services,
  tenant-scoped, checkpointed, and disposable.
- **FR-009**: Projection refresh MUST incorporate new events and remove rows no longer
  present in authoritative results.
- **FR-010**: Operational views MUST share canonical projection/service calculations and
  MUST expose links back to authoritative records.
- **FR-011**: Read tools MAY execute immediately and all interfaces MUST use the same
  tenant-scoped explanation/projection services.

### Domain and Traceability Requirements

- **DR-001**: Source/Evidence/Reality remain authority; Event, Exception, and Projection
  are derived announcements/views.
- **DR-002**: Explanation MUST use shortest true opaque links, never human numbers.
- **DR-003**: Projection rows MUST retain authoritative record keys sufficient for Inspect.
- **DR-004**: Remediation MUST call owning mutation services and never edit exception/projection rows.

### Key Entities

- **BusinessEvent**: Ordered tenant-scoped announcement of a committed domain change.
- **ProjectionCheckpoint/ProjectionRow**: Rebuildable progress and materialized read data.
- **Operational Exception**: Derived condition identified by authoritative record ID.

## Reality Applicability

- **Source/Evidence/Reality**: Explained records remain authoritative at their own stages.
- **Derived layer**: Events announce; exceptions classify; projections accelerate reads.
- **Shortest links**: Projection/exception record key → authoritative Reality → Evidence → Source.
- **Stored/derived**: Events/checkpoints/rows may be stored; their business meaning is derived.
- **Shared boundary**: Web, CLI, tools, Chat, and MCP use tenant-scoped read services.
- **Web explanation**: Every important number/exception exposes Inspect and its derivation trail.

## Success Criteria *(mandatory)*

- **SC-001**: Sourced and manual commitments produce complete explanations with no foreign leakage.
- **SC-002**: Remediating an exception cause removes it without editing exception state.
- **SC-003**: Every projection checkpoint reaches the latest processed tenant event sequence.
- **SC-004**: Projection values equal authoritative service results in every covered story.
- **SC-005**: Cancellation removes stale rows while preserving authoritative history.
- **SC-006**: Rolled-back changes leave zero committed domain events.
- **SC-007**: Every documented exception class has focused proof or a visible gap.

## Assumptions and Dependencies

- Projection refresh may be synchronous in V0; infrastructure scheduling is separate.
- A persisted exception lifecycle requires a future proven use case.
- Owning domain baselines define authoritative calculations.

## Open Questions

The product owner approved this baseline on 2026-08-31. Spec 020 subsequently verified
FR-005 through the closed five-class/one-cause taxonomy, shared derivation and explanation
service, focused PostgreSQL evidence, adapter parity, and deterministic drift validation.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-002 | Verified as-is | Explain/Web contracts | explain and Inspector services | Shopify explain and master-data API tests | — |
| FR-003–FR-004 | Verified as-is | Operational Exceptions contract | exception read/explain tools | `tests/test_application_tools.py` | — |
| FR-005 | Verified as-is | Operational Exceptions contract; Spec 020 | shared exception derivation/explanation service | `tests/operational_exceptions/`; projection, tool, API, and MCP parity tests | — |
| FR-006–FR-007 | Verified as-is | Architecture; operational fields | transactional event emission | `tests/test_business_events.py` | — |
| FR-008–FR-010 | Verified as-is | Architecture; Web contract | projection services | `tests/test_materialized_projections.py` | — |
| FR-011 | Verified as-is | Constitution; Chat/Exception contracts | shared read tools/API/MCP | application-tool, API, and MCP tests | — |
| DR-001–DR-004 | Verified as-is | Constitution; Architecture | explanation/projection boundaries | explain, event, projection, tenancy tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-002 | US1 | Explain and Inspector tests |
| FR-003–FR-005 | US2 | Exception list/explain tests and coverage gap |
| FR-008–FR-010 | US3 | Materialized projection tests |
| FR-006–FR-007 | US4 | Transactional BusinessEvent tests |
| FR-011, DR-001–DR-004 | All | Shared-service and trace review |
