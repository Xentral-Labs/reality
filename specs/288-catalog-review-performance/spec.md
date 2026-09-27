# Feature Specification: Shared Runtime Catalog

**Feature Branch**: `spec/288-catalog-review-performance`
**Created**: 2026-09-27
**Status**: Draft
**Language**: English
**Input**: "Provide one elegant central cache for immutable application-reference metadata that is reused by services regardless of whether they are reached through API, MCP, Web, CLI or another adapter."

## Context and Intent

### Problem

Runtime services repeatedly reconstruct the same immutable application-reference metadata. A
measured Proposal Review took 1.54 seconds in the service, of which 1.43 seconds were spent
rebuilding this metadata; proposal and attribution reads accounted for only a small remainder.
The same raw catalog builder is also called from other runtime service and tool paths.

Caching this separately in Web, API or MCP would hide the delay in only one entry point and create
competing behavior. Every adapter must receive the same validated catalog meaning through the
shared application layer, while mutable business records, authorization and decisions remain
fresh.

### Scope

- Establish one shared runtime snapshot for immutable application-reference metadata used by
  application services and tools.
- Ensure API, MCP, Web, CLI and other adapters benefit through their shared service/tool calls,
  without owning transport-specific catalog caches.
- Move runtime consumers that need deployed application-reference metadata away from repeated raw
  reconstruction when doing so preserves their established behavior.
- Preserve fresh, tenant-scoped reads of proposals, attribution and all other mutable business
  state.
- Preserve safe retry when reference metadata cannot be initialized.
- Add content-parity, consumer-coverage and repeatable performance evidence, beginning with the
  measured Proposal Review path.

### Non-Goals

- Caching business records, service responses, authorization outcomes or mutation results.
- Changing proposal content, catalog vocabulary, tool behavior, next-step guidance or decision
  authority.
- Adding cache logic independently to API, MCP, Web, CLI or other transport adapters.
- Introducing shared external cache infrastructure or cross-process coordination.
- Changing confirmation, rejection or any other mutation.
- Changing the compact Chat cards or their in-flight request sharing from spec 276.
- Supporting live catalog-file replacement inside an already-running production process.
- Replacing explicit fresh-build utilities used by catalog validation, generation or tests.

### Existing Contracts

- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Spec-driven workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Architecture](../../docs/ARCHITECTURE.md)
- [Web UI contract](../../docs/WEB_SPEC.md)
- [Human-readable decision review](../276-human-readable-decision-review/spec.md)

## Clarifications

### Session 2026-09-27

- Q: Should optimization be confined to Proposal Review or shared centrally across service entry
  points? → A: Use one central runtime catalog snapshot for services reached through API, MCP,
  Web, CLI or any other adapter; adapters must not implement their own catalog caches.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Open a proposal promptly (Priority: P1)

As an authorized reviewer, I open a proposed action and receive its complete decision review
without a visible delay caused by rebuilding unchanged reference metadata.

**Why this priority**: This is the measured user-facing regression that proved the shared catalog
was being rebuilt during ordinary runtime work.

**Independent Test**: Read multiple distinct and repeated proposals after application readiness,
assert content parity with the current contract, and measure each completed review.

**Acceptance Scenarios**:

1. **Given** an application process is ready and a tenant has a valid pending proposal, **When** an
   authorized reviewer opens it through any supported adapter, **Then** the complete current
   review is returned within the performance target.
2. **Given** two different pending proposals use the same deployed reference vocabulary, **When**
   they are opened sequentially, **Then** both reviews use identical reference meanings without
   repeating reference-metadata initialization.
3. **Given** a proposal is decided after a prior review read, **When** it is opened again, **Then**
   its latest status, attribution, receipt and available actions are returned rather than a cached
   review response.

### User Story 2 - Share catalog meaning across every adapter (Priority: P1)

As a caller using Web, API, MCP, CLI or another supported adapter, I receive the same catalog-backed
service behavior without paying for a separate metadata reconstruction or depending on an
adapter-specific cache.

**Why this priority**: A cache at only one transport would duplicate architecture and leave other
callers slow or semantically inconsistent.

**Independent Test**: Invoke representative catalog-backed services through different adapters
and prove that they use the shared initialized metadata while returning unchanged results.

**Acceptance Scenarios**:

1. **Given** the runtime catalog has been initialized by one supported service path, **When** a
   different adapter calls another migrated catalog-backed service, **Then** it reuses the same
   validated metadata meaning without another raw reconstruction.
2. **Given** two adapters call the same shared application service, **When** their equivalent
   requests are evaluated, **Then** neither adapter owns a separate cache and both receive
   equivalent catalog-backed results.
3. **Given** a validation or generation workflow explicitly requests a fresh catalog build,
   **When** it runs, **Then** it can still rebuild and validate the deployment artifacts rather
   than being forced through runtime reuse.

### User Story 3 - Preserve safe startup and failure behavior (Priority: P2)

As an operator, I need metadata initialization failures to remain visible and recoverable rather
than becoming a permanently cached partial or failed state.

**Why this priority**: Faster reads must not trade correctness or deployment recovery for speed.

**Independent Test**: Force one runtime metadata initialization attempt to fail, restore the valid
metadata source, and prove that a later service call succeeds with complete content.

**Acceptance Scenarios**:

1. **Given** reference metadata cannot be fully initialized, **When** a runtime service needs it,
   **Then** the call fails explicitly and no incomplete metadata snapshot becomes authoritative.
2. **Given** an initialization attempt failed and the underlying deployment issue is corrected,
   **When** a later runtime service call is made, **Then** initialization is retried and valid
   catalog-backed behavior is returned.

### Edge Cases

- The first catalog-backed service call after process startup may perform one complete metadata
  initialization.
- Concurrent first callers must never observe a partially initialized metadata snapshot.
- Multiple application processes may each hold their own validated snapshot without sharing
  runtime memory.
- A missing or cross-tenant proposal continues to behave as not found without disclosing whether
  another tenant owns it.
- Malformed and retired proposals retain their existing safe, non-confirmable presentation.
- Mutable business state changed after an earlier call must be visible on the next call.
- Metadata validation failure must not make a later corrected attempt reuse the failure.
- Explicit catalog validation and generation continue to obtain a fresh build when requested.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Runtime application services and tools that need unchanged deployment
  application-reference metadata MUST obtain it from one shared validated runtime snapshot.
- **FR-002**: Supported transport adapters, including API, MCP, Web and CLI, MUST benefit through
  shared services/tools and MUST NOT own separate application-reference cache behavior.
- **FR-003**: Runtime consumers migrated by this feature MUST return the same catalog-backed fields
  and meanings for the same deployed metadata as before migration.
- **FR-004**: Shared catalog reuse MUST NOT cache business records, service responses,
  authorization outcomes, tenant state or mutation results.
- **FR-005**: Proposal Review MUST freshly read the tenant-scoped proposal and current decision
  attribution on every request.
- **FR-006**: Incomplete or failed runtime catalog initialization MUST NOT be retained as a
  successful snapshot, and a later call MUST be able to retry initialization.
- **FR-007**: Concurrent readers MUST receive either a complete validated snapshot or an explicit
  failure; none may observe partially initialized metadata.
- **FR-008**: The first completed runtime initialization within one application process MUST be
  reusable by later migrated service/tool calls until that process ends.
- **FR-009**: Catalog validation, generation and tests that explicitly require a fresh build MUST
  retain a supported uncached path.
- **FR-010**: Verification MUST inventory the runtime raw-build callers and either migrate each
  eligible caller or record why it requires fresh construction.
- **FR-011**: Verification MUST include repeatable timing evidence that isolates service work from
  browser rendering and network transport.
- **FR-012**: The shared runtime snapshot MUST remain process-local and MUST NOT require new
  infrastructure or persistence.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality is unchanged because the feature reuses descriptive
  deployment metadata and creates no business authority or record.
- **DR-002**: Existing business records and their shortest true relationships remain authoritative;
  the runtime snapshot may describe them but may never replace or duplicate them.
- **DR-003**: Tenant-scoped services remain responsible for tenant isolation regardless of which
  adapter invokes them; the shared catalog contains no tenant business state.
- **DR-004**: API, MCP, Web, CLI and other adapters continue to call the same application
  services/tools and do not implement alternative catalog or business rules.

## Success Criteria _(mandatory)_

- **SC-001**: After runtime readiness, at least 95% of 20 sequential Proposal Review service reads
  complete in 200 milliseconds or less in the documented local benchmark environment.
- **SC-002**: Across representative API, MCP and direct service/CLI paths, migrated consumers do not
  trigger more than one successful runtime metadata initialization per application process.
- **SC-003**: Content-parity tests show no field or meaning changes for every migrated runtime
  consumer, including proposed, decided, malformed and retired Proposal Reviews.
- **SC-004**: A repeated service read after mutable business state changes returns that changed
  state on the first subsequent call.
- **SC-005**: Failure-recovery evidence proves that a failed initialization does not prevent a
  later valid initialization in the same process.
- **SC-006**: The runtime-caller inventory accounts for 100% of direct raw catalog construction
  calls in production service/tool paths.
- **SC-007**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Application reference files are deployment artifacts and do not change within a running
  production process; deploying changed files starts a new process.
- One process-local snapshot is the appropriate consistency boundary; separate API, MCP and worker
  processes may initialize equivalent snapshots independently.
- The existing validated runtime catalog boundary is the preferred reuse point if planning proves
  it satisfies content, concurrency and failure-retry requirements.
- The 200-millisecond target applies to service execution after runtime readiness, excluding
  browser rendering, network transport and the one allowed first-process initialization.
- No schema, migration, new infrastructure or externally shared cache is required.

## Open Questions

None.

## Requirement Traceability

| Requirement            | Scenario(s)                             | Planned test/evidence                                        |
| ---------------------- | --------------------------------------- | ------------------------------------------------------------ |
| FR-001, FR-008, FR-012 | US1 scenario 2; US2 scenario 1          | Initialization-count regression test and architecture review |
| FR-002, DR-004         | US1 scenario 1; US2 scenarios 1–2       | Cross-adapter service parity and no-adapter-cache proof      |
| FR-003                 | US1 scenarios 1–3; US2 scenarios 1–2    | Catalog-backed content-parity tests                          |
| FR-004, FR-005         | US1 scenario 3; mutable-state edge case | Fresh business-state and tenant-isolation tests              |
| FR-006                 | US3 scenarios 1–2                       | Failed-initialization retry test                             |
| FR-007                 | Concurrent-first-caller edge case       | Concurrent initialization completeness test                  |
| FR-009                 | US2 scenario 3                          | Fresh-build validation/generation test                       |
| FR-010                 | US2 scenarios 1–3                       | Reviewed production caller inventory                         |
| FR-011                 | US1 scenario 1                          | Documented service-level benchmark                           |
| DR-001, DR-002         | US1 and US2                             | Architecture review and no-schema proof                      |
| DR-003                 | US1 scenario 3 and tenant edge case     | Tenant-isolation service test                                |
