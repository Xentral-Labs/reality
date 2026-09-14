# Feature Specification: Canonical Core Catalogs

**Feature Branch**: `spec/core-catalogs`  
**Created**: 2026-08-31  
**Status**: Reviewed  
**Language**: English  
**Input**: "Make Facts, Commands, Business Events, and Projections complete, understandable, machine-readable, drift-checked, and usable as the source for generated product documentation; split the application catalog by concept while preserving one shared view."

## Context and Intent

### Problem

Business Reality has a coherent Source → Evidence → Reality → Business Event →
Projection architecture, but contributors and agents cannot obtain one trustworthy
inventory of its executable vocabulary. The combined application catalog omits some
emitted events, has no Fact predicate catalog, and is not connected to the product
reference. It can therefore appear valid while remaining incomplete.

### Scope

- Give Commands, Business Events, Projections, and Fact predicates separate,
  machine-readable authorities with concept-specific validation.
- Preserve one composed application-catalog view for consumers of the whole system.
- Detect drift against services, emitted events, projection registrations, Fact
  predicates, and database tables.
- Expose the composed catalogs as read-only documentation data and remove the
  hard-coded product Projection list.
- Document how contributors add and prove each cataloged concept.

### Non-Goals

- Generating domain behavior, database models, migrations, or services from catalogs.
- Replacing authoritative Reality records with Events or Projections.
- Adding an event store, broker, worker, infrastructure dependency, or business table.
- Redesigning the complete Help experience beyond serving and consuming its canonical
  reference data.
- Cataloging arbitrary one-off Fact values without stable predicate semantics.

### Existing Contracts

- [`AGENTS.md`](../../AGENTS.md)
- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Architecture](../../docs/ARCHITECTURE.md)
- [Data model](../../docs/DATA_MODEL.md)
- [Web specification](../../docs/WEB_SPEC.md)
- [Operational fields](../../docs/features/operational_fields.md)
- [Production storage and projections ADR](../../docs/decisions/0004-production-storage-and-projections.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find the Complete Executable Vocabulary (Priority: P1)

As a contributor or coding agent, I can inspect one composed reference and find every
public Command, Business Event, materialized Projection, and stable Fact predicate,
including its business meaning and implementation relationship.

**Why this priority**: Safe agent-first development requires a complete vocabulary.

**Independent Test**: Load the composed reference and verify every category is present,
uniquely named, and linked to applicable services or registrations.

**Acceptance Scenarios**:

1. **Given** the current implementation, **When** the composed catalog is loaded,
   **Then** Commands, Events, Projections, and Fact predicates are separately grouped.
2. **Given** a catalog entry, **When** it is inspected, **Then** its business meaning,
   implementation relationship, and applicable reads, writes, producers, consumers,
   or value contract are visible.
3. **Given** no stable Fact predicate, **When** the Fact catalog is loaded, **Then** the
   empty vocabulary is explicit rather than invented from stored values.

### User Story 2 - Stop Catalog Drift Before Completion (Priority: P1)

As a reviewer, I receive an executable failure when implementation and catalog
authority diverge, so incomplete architecture documentation cannot silently ship.

**Why this priority**: Omission must be detected as strongly as a stale entry.

**Independent Test**: Use isolated missing, duplicate, stale, and invalid fixtures for
each category and verify exact failures without a live business database.

**Acceptance Scenarios**:

1. **Given** an emitted Event absent from its catalog, **When** validation runs, **Then**
   it fails and names the missing event.
2. **Given** a Projection, public Command, or stable Fact predicate that is missing,
   duplicated, or stale, **When** validation runs, **Then** it fails by category.
3. **Given** a nonexistent service, table, producer, Projection, or undocumented input,
   **When** validation runs, **Then** it fails before reference data is served.
4. **Given** a normal automated test run, **When** catalogs are validated, **Then** no
   external service or populated tenant is required.

### User Story 3 - Render Reference Data Without Duplication (Priority: P2)

As a product user or developer, I can retrieve current architecture reference data
instead of relying on a hard-coded frontend inventory.

**Why this priority**: Full explainability includes the implemented vocabulary.

**Independent Test**: Request the reference as an authorized tenant member and verify
the UI consumes it without maintaining a second Projection list.

**Acceptance Scenarios**:

1. **Given** an authenticated tenant member, **When** reference data is requested,
   **Then** validated categories and counts are returned without tenant business rows.
2. **Given** an unauthenticated caller, **When** reference data is requested, **Then**
   existing access rules deny the request.
3. **Given** a cataloged Projection rename, **When** reference data is rendered, **Then**
   no separate frontend list must change.

### Edge Cases

- A Command composes multiple related services under one public business name.
- A service produces multiple Event types; an Event may invalidate no Projection.
- A Projection has distinct display and materialized names.
- Fact predicates may be explicitly empty or emitted through an explicit registry.
- Compatibility aliases must not become duplicate canonical entries.
- Validation must inspect metadata without connecting to PostgreSQL.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain separate canonical catalogs for public Commands,
  Business Events, Projections, and stable Fact predicates.
- **FR-002**: The system MUST compose one read-only application reference preserving
  category boundaries and counts.
- **FR-003**: Every Command MUST define business name, service, mode, adapters,
  authoritative reads/writes, effect, and any related services.
- **FR-004**: Every Business Event MUST define exact type, producer, subject, and
  affected Projections, including an explicit empty set.
- **FR-005**: Every Projection MUST define display and materialized names, service,
  authoritative inputs, calculation, consumers, and output contract.
- **FR-006**: Every stable Fact predicate MUST define exact predicate, subject type,
  value contract, meaning, producer, and consumers; the catalog MAY be empty.
- **FR-007**: Validation MUST reject duplicates, missing fields, nonexistent services,
  unknown tables/Projections, and undocumented public service inputs.
- **FR-008**: Validation MUST reject literal emitted Events absent from the catalog and
  stale catalog Events no longer emitted by their declared producer.
- **FR-009**: Validation MUST reject registered Projections absent from the catalog and
  stale materialized names, excluding declared compatibility aliases.
- **FR-010**: The system MUST explicitly register public Commands so internal mutating
  helpers are distinguishable from adapter-facing use cases.
- **FR-011**: Catalog and data-model validation MUST run in automated tests without a
  live PostgreSQL connection or tenant data.
- **FR-012**: The authenticated product reference MUST consume the composed catalog and
  MUST NOT keep a second hard-coded Projection inventory.
- **FR-013**: Contributor documentation MUST explain how to add and prove each catalog
  concept.
- **FR-014**: Splitting the catalog MUST preserve parameter descriptions and all prior
  entries while adding known omissions.

### Domain and Traceability Requirements

- **DR-001**: Catalogs describe Source → Evidence → Reality but MUST NOT become
  authoritative state or an alternative write path.
- **DR-002**: Commands enforce invariants from authoritative tenant-scoped records;
  Projections remain disposable Event-progress-driven read models.
- **DR-003**: Reference access preserves tenant and shared-service boundaries and never
  exposes cross-tenant business data.
- **DR-004**: Business Events remain immutable announcements and do not replace Reality
  records.
- **DR-005**: Catalog separation introduces no schema field, foreign key, or new
  infrastructure dependency.

### Key Entities *(when data is involved)*

- **Command definition**: Public operation and its adapter, access, and effect contract.
- **Business Event definition**: Stable event name and Projection impact.
- **Projection definition**: Rebuildable read-model registration and explanation.
- **Fact predicate definition**: Stable observation vocabulary, not individual Facts.
- **Application reference**: Validated composition and category counts.

## Success Criteria *(mandatory)*

- **SC-001**: One load returns 100% of public Commands, emitted literal Events,
  registered Projections, and stable Fact predicates without duplicate names.
- **SC-002**: Tests detect missing, stale, duplicate, and invalid-reference cases with
  category-specific messages.
- **SC-003**: The product Projection reference has zero names maintained in frontend
  source outside the catalog response.
- **SC-004**: A contributor identifies any Event producer and affected Projection set
  from one reference in under two minutes.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- YAML remains suitable for reviewed, deterministic machine-readable catalogs.
- A public Command is explicitly registered for at least one adapter; it is not every
  mutating helper.
- Static completeness applies to literal event/predicate names; dynamic names require
  an explicit registry.
- Existing authenticated Web/API access is reused.
- The owner's implementation instruction constitutes product-scope approval.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-002 | US1.1 | Composition unit test |
| FR-003–FR-006 | US1.2–US1.3 | Category contract tests |
| FR-007–FR-011 | US2.1–US2.4 | Offline drift validation tests |
| FR-012 | US3.1–US3.3 | API and frontend tests/build |
| FR-013, FR-014 | US1.1, US2.4 | Documentation and migration regression |
| DR-001–DR-005 | US2.3–US3.2 | Constitution review and regression suite |

