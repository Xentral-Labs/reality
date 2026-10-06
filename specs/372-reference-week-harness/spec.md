# Feature Specification: Reality Reference Week Harness

**Language**: English
**Created**: 2026-10-05
**Status**: Scope accepted by the owner in this conversation ("Ok mach").

## Context and Intent

### Problem
The authored Reality Referenzwoche needs a repeatable execution and an independent
quantity oracle to distinguish incorrect bookings from incorrect operator choices.

### Scope
A local developer rehearsal, using existing application services and PostgreSQL,
with a reusable clock/barrier controller, simulator adapter, observer and reports.
Implement the reference day first, then its deterministic seven-day continuation.
The owner explicitly approved this scope and the proposed source layout.

### Non-Goals
No Shopify implementation, agent mandate, AI operator, external email transport,
web UI, new business rules, schema, scheduler, production deployment or automatic
financial posting. No live account provisioning or permission bypass.

## User Scenarios & Testing

### User Story 1 — Repeat the reference day (P1)
Given an eligible existing local owner and a migrated local test database, a
confirmed run creates a fresh empty Sandbox, executes exact approved manual-source
orders and physical events, and stops at the first mismatching barrier. Its final
stock is A/B/C 0/6/0, with A4 customer quantity and A20/C10 supplier quantity open.
A second run creates a different company with the same quantities.

### User Story 2 — Explain a failure (P1)
Given a deliberately wrong expected quantity, the run retains the first event,
expected/actual/delta and affected opaque record IDs, exits unsuccessfully and
emits no later fixture event. An uncertain mutation outcome is never retried.

### User Story 3 — Continue the week (P2)
Given the same fixture selected with week scope, partial receipts, returns, count
loss and transfer result in global A/B/C 7/4/4 and W1 4/4/4, W2 3/0/0, without
active allocations or open delivery promises. Returns do not reopen fulfillment.

### Edge Cases
Unconfirmed execution, unsupported fixture action, invalid event ordering, duplicate
event IDs, stale/missing references, wrong company and unauthorized owner fail closed.
No SQLite substitute. Reports must not disclose database passwords. Replaying an
executed proposal has no new business effect.

## Requirements

- **FR-001**: One versioned fixture supplies explicit inputs and independent exact
  checkpoint expectations; day is the first 24-hour subset of week.
- **FR-002**: Execution requires explicit confirmation and an existing eligible owner,
  creates a fresh empty Sandbox through company setup, and uses existing services
  and proposal confirmation without direct ORM business writes.
- **FR-003**: The simulator resolves labels to opaque IDs, records actual source and
  evidence IDs, and retains order preparation snapshots proving no accepted effect.
- **FR-004**: The observer reads all company records in scope, verifies stock,
  reservations, live open promises, outstanding announced returns, master/order/commitment counts, lineage and
  absence of ledger entries. Reports retain per-line and per-location observations.
- **FR-005**: The synchronous compressed controller observes after every event, blocks
  at explicit milestones, stops at first failure and never automatically retries.
  Scenario time is distinct from real time; no claim of virtual application time.
- **FR-006**: Each run writes manifest, JSONL event/checkpoint logs and JSON/Markdown
  results under an exclusive run directory, recording fixture hash, revision,
  company, owner, returned IDs, input hashes and first failure. No credentials.
- **FR-007**: Tests prove day and week arithmetic, independent mismatch detection,
  no later effects after failure, run isolation, replay, and confirmation refusal.
- **FR-008**: Shared orchestration/reporting has no Shopify or reference-week rules;
  unsupported source adapters are explicit. This first implementation uses manual
  source proposals and authoritative reads, not external intake or projection proof.

## Assumptions and Dependencies
Existing PostgreSQL, Python environment, eligible user, company setup, application
proposal tools and read services. Execution is local trusted developer tooling;
not exposed as a remote authentication boundary. The first adapter receives a local
human's exact authored fixture approval, not unattended agent authority. Runtime
reports belong in ignored artifacts, not business tables. Financial correctness and
external raw-intake duplicate admission remain separate coverage.

## Success Criteria
Day and week repeat with exact documented quantities and complete lineage.
Deliberately wrong expectation produces an attributable failure and stops progression.
No new core business behavior, schema, transport or agent access is introduced.

## Requirement Traceability

| Requirement | Tasks | Evidence |
| --- | --- | --- |
| FR-001 | T001, T002 | Fixture validation and day/week scenario tests |
| FR-002 | T002, T003 | Confirmation refusal, fresh Sandbox and repeat-run tests |
| FR-003 | T002, T003 | No-effect proposal snapshots and evidence chain checks |
| FR-004 | T002, T004 | Day/week snapshots, injected mismatch test |
| FR-005 | T002, T005 | Stop-before-next-event test |
| FR-006 | T002, T005 | Manifest/log/report artifact assertions |
| FR-007 | T002, T006 | Automated acceptance and regression tests |
| FR-008 | T001, T005, T006 | Structure and documented adapter limitations |
