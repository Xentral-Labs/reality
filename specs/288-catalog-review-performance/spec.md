# Feature Specification: Fast Proposal Review Metadata

**Feature Branch**: `spec/288-catalog-review-performance`
**Created**: 2026-09-27
**Status**: Draft
**Language**: English
**Input**: "Avoid rebuilding deployment metadata for every Proposal Review read so the review dialog opens promptly while preserving current content, tenant isolation and fresh proposal state."

## Context and Intent

### Problem

Opening a pending proposal currently spends most of its response time rebuilding immutable
application-reference metadata. A measured review took 1.54 seconds in the service, of which
1.43 seconds were spent reconstructing that metadata; proposal and attribution reads accounted
for only a small remainder. This makes a simple human decision feel slow even after duplicate
browser reads have been removed.

Reviewers need the exact current proposal, preview, attribution and next-step guidance without
waiting for deployment metadata to be rediscovered for every open or reopen.

### Scope

- Return the existing Proposal Review content without reconstructing unchanged application
  reference metadata for each read.
- Preserve a fresh, tenant-scoped read of mutable proposal and decision-attribution state on every
  request.
- Preserve safe recovery when reference metadata cannot be initialized.
- Add repeatable performance and content-parity evidence for the Proposal Review read path.

### Non-Goals

- Changing proposal content, review classification, next-step guidance or decision authority.
- Caching proposal records, decision attribution, authorization results or review responses.
- Changing confirmation, rejection or any other mutation.
- Optimizing every catalog consumer or introducing cross-process cache infrastructure.
- Changing the compact Chat cards or their in-flight request sharing from spec 276.
- Supporting live catalog-file replacement inside an already-running application process.

### Existing Contracts

- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Spec-driven workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Web UI contract](../../docs/WEB_SPEC.md)
- [Human-readable decision review](../276-human-readable-decision-review/spec.md)

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Open a proposal promptly (Priority: P1)

As an authorized reviewer, I open a proposed action and receive its complete decision review
without a visible delay caused by rebuilding unchanged reference metadata.

**Why this priority**: Human confirmation is a frequent control point. A read-only review should
not feel as slow as performing business work.

**Independent Test**: Read multiple distinct and repeated proposals after application readiness,
assert content parity with the current contract, and measure each completed review.

**Acceptance Scenarios**:

1. **Given** an application process is ready and a tenant has a valid pending proposal, **When** an
   authorized reviewer opens it, **Then** the complete current review is returned within the
   performance target.
2. **Given** two different pending proposals use the same deployed reference vocabulary, **When**
   they are opened sequentially, **Then** both reviews use identical reference meanings without
   repeating the expensive reference-metadata initialization.
3. **Given** a proposal is decided after a prior review read, **When** it is opened again, **Then**
   its latest status, attribution, receipt and available actions are returned rather than a cached
   review response.

### User Story 2 - Preserve safe startup and failure behavior (Priority: P2)

As an operator, I need metadata initialization failures to remain visible and recoverable rather
than becoming a permanently cached partial or failed state.

**Why this priority**: Faster reads must not trade correctness or deployment recovery for speed.

**Independent Test**: Force one metadata initialization attempt to fail, restore the valid
metadata source, and prove that a later review succeeds with complete content.

**Acceptance Scenarios**:

1. **Given** reference metadata cannot be fully initialized, **When** a review needs that metadata,
   **Then** the review fails explicitly and no incomplete metadata snapshot becomes authoritative.
2. **Given** an initialization attempt failed and the underlying deployment issue is corrected,
   **When** a later review is requested, **Then** initialization is retried and the valid review is
   returned.

### Edge Cases

- The first review after process startup may perform one complete metadata initialization.
- Concurrent first reviews must never observe a partially initialized metadata snapshot.
- A missing or cross-tenant proposal continues to behave as not found without disclosing whether
  another tenant owns it.
- Malformed and retired proposals retain their existing safe, non-confirmable presentation.
- A decided proposal must never reuse proposed-state actions from an earlier read.
- Metadata validation failure must not make a later corrected attempt reuse the failure.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: After successful application-reference initialization, Proposal Review reads MUST
  reuse the unchanged deployment reference snapshot rather than rebuilding it for every request.
- **FR-002**: Every Proposal Review request MUST freshly read the tenant-scoped proposal and its
  current decision attribution.
- **FR-003**: The returned review fields and meanings MUST remain identical to the established
  Proposal Review contract for the same stored state.
- **FR-004**: Proposal Review acceleration MUST NOT cache review responses, proposal state,
  authorization outcomes or mutation results.
- **FR-005**: Incomplete or failed reference initialization MUST NOT be retained as a successful
  snapshot, and a later request MUST be able to retry initialization.
- **FR-006**: Concurrent readers MUST receive either the complete validated reference snapshot or
  an explicit failure; none may observe partially initialized metadata.
- **FR-007**: The first completed initialization within one running application process MUST be
  reused by later Proposal Review reads until that process ends.
- **FR-008**: The implementation MUST provide repeatable timing evidence that isolates Proposal
  Review service work from browser rendering and network transport.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality is unchanged because the feature only accelerates a
  read-only presentation of an existing Change Proposal; it creates no new authority or record.
- **DR-002**: The Change Proposal remains the shortest true link for review state. No duplicate
  proposal, source, document or operational relationship may be introduced.
- **DR-003**: Proposal and attribution reads remain tenant-scoped and continue through the shared
  Proposal Review service used by the Web API.
- **DR-004**: Deployment reference metadata remains descriptive vocabulary, never a substitute
  for current proposal or Reality state.

## Success Criteria _(mandatory)_

- **SC-001**: After application readiness, at least 95% of 20 sequential Proposal Review service
  reads complete in 200 milliseconds or less in the documented local benchmark environment.
- **SC-002**: A repeated review after a proposal status change returns the changed status and
  available actions on the first read after that change.
- **SC-003**: Content-parity tests show no field or meaning changes for proposed, decided,
  malformed and retired reviews.
- **SC-004**: Failure-recovery evidence proves that a failed initialization does not prevent a
  later valid initialization in the same process.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Application reference files are deployment artifacts and do not change within a running
  production process; deploying changed files starts a new process.
- The existing process-local validated reference snapshot is eligible for reuse when it provides
  the same content required by Proposal Review.
- The 200-millisecond target applies to service execution after application readiness, excluding
  browser rendering, network transport and the one allowed first-process initialization.
- No schema, migration, new infrastructure or externally shared cache is required.

## Open Questions

None.

## Requirement Traceability

| Requirement            | Scenario(s)                         | Planned test/evidence                                                |
| ---------------------- | ----------------------------------- | -------------------------------------------------------------------- |
| FR-001, FR-007         | US1 scenarios 1–2                   | Initialization-count regression test and sequential review benchmark |
| FR-002, FR-004         | US1 scenario 3                      | Mutable proposal-state regression test                               |
| FR-003                 | US1 scenarios 1–3                   | Proposal Review content-parity tests                                 |
| FR-005                 | US2 scenarios 1–2                   | Failed-initialization retry test                                     |
| FR-006                 | Edge case: concurrent first reviews | Concurrent initialization completeness test                          |
| FR-008                 | US1 scenario 1                      | Documented service-level benchmark                                   |
| DR-001, DR-002, DR-004 | US1 scenarios 1–3                   | Architecture review and no-schema proof                              |
| DR-003                 | US1 scenario 3 and tenant edge case | Tenant-isolation service test                                        |
