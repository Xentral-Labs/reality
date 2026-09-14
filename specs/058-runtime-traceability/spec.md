# Feature Specification: Packaged Runtime Traceability

**Feature Branch**: `058-runtime-traceability`  
**Created**: 2026-09-03  
**Status**: Approved for implementation  
**Language**: English  
**Input**: "Repair packaged migration-health detection and expose the shortest SourceRecord version link through public reads."

## Context and Intent

### Problem

The deployed API applies migrations but reports an unknown expected revision because its health
code cannot locate migrations in the packaged container. Agents can discover SourceRecord versions
but cannot traverse a version directly to its predecessor through public API/MCP reads.

### Scope

- Make packaged and source-checkout runtimes derive the same migration head.
- Expose `supersedes_source_record_id` in tenant SourceRecord API and agent discovery reads.
- Prove the transient interpretation-failure exception and its state-derived resolution.

### Non-Goals

- Changing migration execution, SourceRecord immutability, version selection, payload visibility,
  exception persistence, or adding schema.
- Exposing successor lists or copying the whole version chain into each record.

## User Scenarios & Testing

### User Story 1 — Trust deployment health (Priority: P1)

An operator sees the applied and expected migration revisions agree in a packaged deployment.

**Acceptance Scenario**: Given migrations ship beside the application, when deployment posture is
read, then the single migration head is reported and `migrations_current` is true when it equals the database revision.

### User Story 2 — Traverse source history (Priority: P1)

An agent follows a changed SourceRecord directly to the immutable version it supersedes.

**Acceptance Scenario**: Given version two supersedes version one, API and MCP discovery return
version two with `supersedes_source_record_id` equal to version one's opaque ID; version one returns null.

### User Story 3 — Observe transient intake failure (Priority: P2)

An operator can observe a failed interpretation as a derived exception and sees it disappear after a successful retry.

**Acceptance Scenario**: Given a failed ImportJob, the exception read exposes its source/job cause;
after the same job succeeds, the exception is absent without a mutable ticket update.

### Edge Cases

- A packaged runtime has no migration directory or multiple heads.
- A first SourceRecord has no predecessor.
- A stale/conflicting record is preserved without becoming the current stream head.

## Requirements

- **FR-001**: Runtime posture MUST derive the expected migration head in source and packaged layouts.
- **FR-002**: Missing or ambiguous migration heads MUST remain explicit unknowns.
- **FR-003**: Public SourceRecord API reads MUST return nullable `supersedes_source_record_id`.
- **FR-004**: `business_records_discover` MUST return the same predecessor field without payloads.
- **FR-005**: Cross-tenant SourceRecord discovery MUST remain not found.
- **FR-006**: A failed interpretation exception and its disappearance after successful retry MUST have executable proof.
- **DR-001**: The predecessor is the shortest true SourceRecord-to-SourceRecord relationship.
- **DR-002**: No schema or duplicated Source/Evidence/Reality state may be added.

## Success Criteria

- **SC-001**: Packaged-runtime and source-checkout head detection return the same single revision.
- **SC-002**: 100% of tested first and subsequent SourceRecord reads expose the correct nullable predecessor.
- **SC-003**: Failure and recovery tests show one derived exception before retry and none after success.
- **SC-004**: Existing backend, migration, tenant, API, MCP, lint, and spec-policy suites remain green.

## Assumptions and Dependencies

- Migration files remain shipped in the Docker image and Python distribution.
- Existing SourceRecord persistence already owns `supersedes_source_record_id`.
- The user's instruction to implement the test findings approves this bounded scope.

## Requirement Traceability

| Requirement | Evidence |
| --- | --- |
| FR-001–FR-002 | packaged migration-head unit/contract tests |
| FR-003–FR-005, DR-001 | API and MCP SourceRecord version tests |
| FR-006 | operational exception failure/retry test |
| DR-002, SC-004 | schema diff and full quality gates |
