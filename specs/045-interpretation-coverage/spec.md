# Feature Specification: Interpretation Coverage

**Feature Branch**: `045-interpretation-coverage`
**Created**: 2026-09-03
**Status**: Approved for implementation
**Language**: English
**Input**: "Make every source interpretation explicit and explainable, beginning with Shopify orders, so agents can see produced Reality records or a bounded reason why human review or retry is required."

## Context and Intent

### Problem

Reality stores source payloads losslessly and tracks a mutable import-job status, but
it does not preserve an explicit outcome for each processing attempt or identify the
records produced by a successful interpretation. Agents and operators therefore
cannot reliably distinguish understood sources from silent gaps or explain what one
attempt changed.

### Scope

- Preserve an append-only interpretation outcome for every attempted processing run.
- Classify outcomes as interpreted, needs review, unsupported, stale, conflict, or failed.
- Identify the interpreter and attempt and reference produced Reality records by opaque ID.
- Expose tenant-scoped interpretation coverage through the shared read-tool boundary.
- Cover the existing Shopify order interpreter plus unmapped, stale, conflicting, failed, and retried sources.

### Non-Goals

- Making interpretation outcomes part of canonical business Reality.
- Adding mapping-language, workflow, policy-learning, or autonomous remediation systems.
- Automatically creating Facts for every source field.
- Changing Shopify order semantics or supporting additional connectors.
- Building a new web page or Atlas-specific operational store.

### Existing Contracts

- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Interpretation coverage idea](../../docs/ideas/interpretation-coverage.md)
- [Source ingestion](../../docs/features/source_ingestion.md)
- [Data model](../../docs/DATA_MODEL.md)
- [Agent capability guidance](../044-agent-capability-guidance/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explain successful interpretation (Priority: P1)

An agent reads a Shopify source's coverage and sees the successful attempt, its
interpreter identity, and the opaque IDs and types of the Document, DocumentLines, and
Commitments produced.

**Why this priority**: A completed job is useful only when its resulting Reality can be
located and independently inspected.

**Independent Test**: Process one Shopify order and verify that its outcome is
append-only, complete, source-linked, and resolvable to the records returned by the
existing interpreter.

**Acceptance Scenarios**:

1. **Given** a valid Shopify order, **When** its first import attempt completes, **Then** one interpreted outcome names the source, job, attempt, interpreter, and every produced record.
2. **Given** the same completed job is read again, **When** no new processing attempt occurs, **Then** no duplicate outcome is created.

### User Story 2 - Surface unresolved sources (Priority: P2)

An operator can see why a source has not become Reality and whether it needs review,
is unsupported, is stale or conflicting, or failed and may be retried.

**Why this priority**: Missing interpretation must become visible work instead of an
implicit absence of records.

**Independent Test**: Exercise unsupported, stale, conflict, and interpreter failure
paths and verify each has a bounded terminal classification and safe reason.

**Acceptance Scenarios**:

1. **Given** no interpreter exists for a source type, **When** it is accepted, **Then** coverage records an unsupported outcome without fabricated Reality references.
2. **Given** an interpreter fails and is retried, **When** both attempts finish, **Then** both immutable outcomes remain ordered and distinguishable.
3. **Given** a stale or conflicting source version, **When** intake classifies it, **Then** coverage exposes that classification without interpreting it as current Reality.

### User Story 3 - Give agents one safe coverage read (Priority: P3)

Chat and MCP agents use the same read-only application capability to list coverage or
inspect one source without direct database access.

**Why this priority**: Coverage is operationally useful only through the governed,
tenant-scoped boundary agents already use.

**Independent Test**: Read coverage through the application tool and MCP catalog and
verify stable fields, no mutation, and cross-tenant not-found behavior.

**Acceptance Scenarios**:

1. **Given** a tenant has interpreted and unresolved sources, **When** an agent lists coverage, **Then** both are returned with explicit classifications and no source payload disclosure.
2. **Given** another tenant's source ID, **When** an agent requests its coverage, **Then** the result behaves as not found and discloses no metadata.

### Edge Cases

- A processing transaction rolls back after some in-memory records were allocated IDs.
- A retry succeeds after a failed attempt.
- An interpreter returns no business records intentionally.
- Existing sources predate this feature and have no historical attempt outcome.
- Source payloads or failure text contain sensitive content.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preserve exactly one immutable outcome for every terminal interpretation attempt.
- **FR-002**: Each outcome MUST identify its tenant, source, import job, attempt number, classification, interpreter identity/version, completion time, and a bounded reason code and summary.
- **FR-003**: An interpreted outcome MUST reference every produced record using a controlled record type and opaque ID; unresolved outcomes MUST NOT claim produced Reality.
- **FR-004**: Failed transactional work MUST NOT leave an interpreted outcome or references to rolled-back records.
- **FR-005**: Retries MUST append outcomes and MUST NOT overwrite prior attempts.
- **FR-006**: Unsupported, stale, and conflict intake paths MUST produce explicit outcomes even when no interpreter executes.
- **FR-007**: A read-only coverage capability MUST list tenant coverage and inspect one source through shared application services, without exposing raw source payloads.
- **FR-008**: Chat and MCP discovery MUST expose the same coverage read contract and MUST NOT bypass tenant or service boundaries.
- **FR-009**: Sources created before this feature without an outcome MUST appear as `not_recorded`, rather than being silently counted as interpreted.
- **FR-010**: Classification MUST follow one deterministic taxonomy: `pending` and `processing` are non-terminal job states and create no outcomes; `interpreted` means an interpreter completed and identified its produced records; `needs_review` means it completed safely but explicitly declined to create Reality because business meaning remains ambiguous; `unsupported` means no interpreter exists; `stale` and `conflict` reflect source-version dispositions; and `failed` means execution raised an error and rolled back. `not_recorded` is only a computed label for historical sources without preserved outcomes.

### Domain and Traceability Requirements

- **DR-001**: InterpretationOutcome MUST link directly to SourceRecord and ImportJob; produced-record references describe results but do not replace Source → Evidence → Reality links.
- **DR-002**: InterpretationOutcome is operational audit metadata and MUST NOT become business authority or duplicate business-state fields.
- **DR-003**: Every outcome and query MUST be tenant-scoped; cross-tenant access behaves as not found.
- **DR-004**: SourceRecord remains immutable and lossless; outcome reasons MUST use safe summaries rather than copying payloads or secrets.
- **DR-005**: The schema expansion is justified because attempts and their produced-record set must remain append-only, queryable, and independently explainable after ImportJob changes.

### Key Entities *(when data is involved)*

- **InterpretationOutcome**: Immutable result of one terminal interpretation attempt, linked to its SourceRecord and ImportJob.
- **Produced Record Reference**: Controlled type and opaque identity of a record created or recognized by an interpreted attempt.
- **Interpretation Coverage View**: Tenant-scoped read model combining all sources with their ordered outcomes and current attention classification.

## Success Criteria *(mandatory)*

- **SC-001**: 100% of newly accepted test sources have an explicit terminal outcome or a visible pending/processing state.
- **SC-002**: A reviewer can navigate from a successful Shopify source to every produced Document, line, and Commitment identity without inspecting logs or model reasoning.
- **SC-003**: Retry tests retain 100% of prior terminal outcomes and identify the current attempt unambiguously.
- **SC-004**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The existing SourceRecord, ImportJob, Shopify interpreter, tool registry, and MCP adapter remain the execution boundaries.
- One ImportJob belongs to one SourceRecord; attempt number plus job identity uniquely identifies an outcome.
- Produced references are audit links, while each target record retains its existing authoritative source/evidence relationship.
- The owner's "ja mach" approves this bounded first slice and its append-only schema addition.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-002, FR-003, DR-001 | US1.1 | Shopify outcome service test |
| FR-004 | Edge rollback | Failed interpreter transaction test |
| FR-005 | US2.2 | Retry history test |
| FR-006 | US2.1, US2.3 | Intake classification tests |
| FR-007, FR-009, DR-002, DR-004 | US3.1 | Coverage application-tool test |
| FR-008, DR-003 | US3.2 | MCP parity and tenant-isolation tests |
| FR-010 | US1.1, US2.1–US2.3, edge cases | Classification decision-table test |
| DR-005 | Architecture review | Migration and data-model review |
