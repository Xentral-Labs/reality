# Feature Specification: Shopify Update Guard

**Created**: 2026-09-05
**Language**: English
**Status**: Approved scope
**Input**: Preserve Shopify source updates without automatically replacing operational
Reality; expose unsupported changes as requiring review until real connector work.

## Context and Intent

The existing interpreter replaces promises on every changed payload, releasing
reservations and reopening quantities already shipped. This narrow guard stops that
behavior before a live connector is built. The user approved this bounded scope in
the conversation on 2026-09-05; no additional product decision is outstanding.

### Non-Goals

No connector, semantic diff, automatic amendment, review-approval execution, schema
change, initial-order cancellation interpretation, historical repair, or new UI.
The review result is not a proposal that a user can approve to bypass the guard.

## User Scenarios & Testing

### User Story 1 - Preserve Operational Reality (Priority: P1)

An operator receives a changed Shopify order without losing allocations or creating
new demand for previously shipped goods.

**Independent Test**: Interpret an initial order, reserve it, optionally ship part or
all, then process a changed payload. Existing records and quantities remain intact.

**Acceptance Scenarios**:

1. Given an interpreted order, when a note, quantity, or cancellation changes, the
   new source is stored but no replacement Evidence or operational records are created.
2. Given zero, partial, or full shipment, the update preserves all commitments,
   reservations, movements, document states, and remaining quantities.
3. Given two consecutive changed versions, both require review and neither replaces
   the original interpretation, even when the immediate predecessor has no Document.

### User Story 2 - Explain Review and Retry Safely (Priority: P1)

The operator can distinguish retained data from successfully interpreted Reality.

**Independent Test**: Read interpretation coverage through services and the review
reason through HTTP import-job reads; repeat processing and explicitly retry it.

**Acceptance Scenarios**:

1. The changed source has a `needs_review` outcome with a clear explanation that
   Shopify updates are unsupported and previous operational records remain unchanged.
2. Reprocessing a completed review returns no interpretation and creates no extra
   outcome; an explicit retry records another review attempt without business effects.
3. The synchronous Shopify helper reports review, not stale delivery or success.
4. A batch continues to process an unrelated first order after encountering review.

### User Story 3 - Preserve Existing Intake Guarantees (Priority: P2)

**Independent Test**: Existing first-import, duplicate, failure-retry, stale/conflict,
and tenant-isolation tests remain green alongside the new guard cases.

**Acceptance Scenarios**:

1. A first version still interprets normally and an identical replay returns its
   existing interpretation. Fixing missing reference data permits retry of that version.
2. An identical reviewed payload retains the same SourceRecord and ImportJob.
3. Stale/conflicting deliveries retain their existing classification and never apply.
4. A changed version after a failed first version also requires review; repairing
   reference data does not bypass the guard for a changed source.
5. Other tenants cannot process or inspect the reviewed source; their own first order
   with the same external ID remains independent.

### Edge Cases

Metadata-only changes are intentionally held. Already interpreted historical versions
remain readable and are not repaired. Multiple queued versions and retries cannot
use an uninterpreted predecessor to bypass the source-version guard. Generic review
exceptions must not disclose raw payload details in their public explanation.

## Requirements

- **FR-001**: Preserve immutable source versioning, hashes, source identity, and
  latest-source tracking for every accepted payload.
- **FR-002**: Any Shopify order source version greater than one without an existing
  interpretation MUST require review before any business mutation, including when a
  prior version failed or remains pending.
- **FR-003**: Review MUST leave previous Evidence, commitments, reservations,
  movements and financial records unchanged, and produce no new business records.
- **FR-004**: Persist a clear, non-sensitive review reason and expose it through
  existing interpretation coverage and import-job reads; no automatic retry is due.
- **FR-005**: Completed review processing and identical intake MUST be idempotent;
  explicit retries MUST preserve the guard and record their attempt history.
- **FR-006**: Keep first-version processing, first-version retry, successful replay,
  stale/conflict dispositions and tenant isolation intact.
- **FR-007**: Synchronous and batch processing MUST handle review truthfully without
  treating it as successful interpretation or preventing unrelated work.
- **DR-001**: Use existing Source, Evidence, Reality and interpretation-outcome
  relationships, opaque identities and shared application services; add no schema.
- **DR-002**: Every new repository query MUST be tenant-scoped; no new permissions,
  agent confirmation bypass, source mutation, or operational document fields.

## Success Criteria

- **SC-001**: All supported guard scenarios preserve the exact pre-update operational
  quantities and identities with zero duplicate demand or released allocations.
- **SC-002**: Every processed unsupported update has an inspectable review outcome;
  repeated processing creates zero duplicate outcomes or business effects.
- **SC-003**: Existing first-import, isolation and stale/conflict guarantees pass,
  and the complete required verification suite is green before completion.

## Assumptions and Dependencies

Version greater than one is deliberately conservative; semantic interpretation of
changes waits for real Shopify/Xentral integration. `SourceStream` continues to point
to the latest accepted source, which is not necessarily the last interpreted source.
Existing `needs_review` coverage is the operator surface. Existing historical damage
is not repaired. The existing initial-order interpreter's other limitations remain.

## Requirement Traceability

| Requirements | Stories | Planned evidence |
|---|---|---|
| FR-001, FR-002, FR-003, DR-001 | US1, US3 | Guard service stories and unchanged record snapshots |
| FR-004, DR-002 | US2, US3 | Coverage, HTTP and tenant isolation tests |
| FR-005 | US2, US3 | Duplicate and explicit retry tests |
| FR-006 | US3 | First-version retry, successful replay, stale/conflict tests |
| FR-007 | US2 | Helper error and batch continuation tests |
