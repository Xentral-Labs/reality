# Feature Specification: Safe Proposal Confirmation

**Feature Branch**: `059-safe-proposal-confirmation`
**Created**: 2026-09-03
**Status**: Approved for implementation
**Language**: English
**Input**: "Resolve #80, #81, and #82 as one coherent confirmation contract."

## Context and Intent

### Problem

Atlas can prepare a Reality mutation and a human can confirm it, but the confirmation
contract is not discoverable through `capability_describe`. Confirmation also reads a
`proposed` row before running the mutation and settles it only afterwards, so concurrent
callers can both enter the handler and a caller cannot safely reconcile an interrupted
request. Reservation confirmation returns useful values but lacks an explicitly correlated,
documented receipt and verification path.

### Scope

- Make one proposal a single-use execution boundary under concurrent PostgreSQL requests.
- Give repeated and interrupted callers stable replay/refusal/reconciliation semantics.
- Return a correlated reservation execution receipt and authoritative verification guidance.
- Make the confirmation contract discoverable without exposing confirmation to models.
- Resolve GitHub issues #80, #81, and #82 when the implementation PR is merged.

### Non-Goals

- Automatic or model-selected confirmation.
- A generic workflow engine, distributed transaction coordinator, or Atlas state machine.
- Claiming that a successful reservation proves fulfilment or the final customer outcome.
- Retrying an indeterminate execution automatically.

### Existing Contracts

- `apps/docs/content/concepts/agent-capabilities.md`
- `docs/WEB_SPEC.md`
- `specs/055-decision-attribution/spec.md`
- GitHub issues #80, #81, and #82

## User Scenarios & Testing

### User Story 1 - Confirm exactly once (Priority: P1)

An accountable human confirms one prepared proposal while Reality prevents any concurrent
or repeated request from applying its business mutation twice.

**Why this priority**: Without at-most-once mutation, Atlas cannot safely cross the effect boundary.

**Independent Test**: Two real PostgreSQL sessions concurrently confirm one reservation
proposal; exactly one reservation and one correlated creation event exist afterwards.

**Acceptance Scenarios**:

1. **Given** one proposed reservation, **When** two callers confirm concurrently, **Then** only one caller claims execution and the mutation is applied once.
2. **Given** an executed proposal, **When** confirmation is repeated, **Then** Reality returns the already-settled result without executing again.
3. **Given** an execution already claimed but not settled, **When** another caller confirms, **Then** Reality refuses blind execution and directs the caller to reconciliation.

### User Story 2 - Verify the exact reservation effect (Priority: P1)

Atlas receives a receipt that ties the proposal and capability to the created reservation,
its commitment and quantity, and can re-read those authoritative records.

**Why this priority**: Transport success alone does not prove the intended operational state.

**Independent Test**: Confirm a reservation and compare the receipt against the tenant-scoped
proposal, reservation, commitment, and correlated business event reads.

**Acceptance Scenarios**:

1. **Given** a successful reservation confirmation, **When** its result is read, **Then** it identifies proposal, capability, reservation, commitment, applied quantity, and event.
2. **Given** a mismatched commitment, quantity, unrelated reservation, stale evidence, or missing event, **When** verification is evaluated, **Then** the effect is not reported as verified.
3. **Given** a verified reservation effect, **Then** guidance states that fulfilment and customer outcome remain unproven.

### User Story 3 - Discover confirmation safely (Priority: P2)

Atlas reads the confirmation contract before offering a human the exact action, while the
confirmation tool remains unavailable for model selection.

**Why this priority**: Contract knowledge is necessary for orchestration but is not authority.

**Independent Test**: `capability_describe("proposal_approve_and_execute")` succeeds through a
read-only token while model schemas still omit the confirmation tool.

**Acceptance Scenarios**:

1. **Given** read permission, **When** Atlas describes confirmation, **Then** it receives preconditions, refusals, replay/unknown semantics, receipt shape, and verification reads.
2. **Given** model tool schema generation, **Then** confirmation is absent.
3. **Given** an unknown or internal name, **When** it is described, **Then** the response is a bounded non-disclosing not-found error.

### Edge Cases

- Confirmation with `approved` absent or false.
- Proposal belongs to another tenant, was rejected, or references an invalid mutation.
- Process interruption before mutation, after mutation commit, or before response delivery.
- A reservation allocates zero because no quantity is available.
- The same confirmation arrives after the original response was lost.

## Requirements

### Functional Requirements

- **FR-001**: Reality MUST atomically claim a `proposed` proposal before entering its mutation handler.
- **FR-002**: One proposal MUST apply its operational mutation at most once under concurrent confirmation.
- **FR-003**: Reconfirming an executed proposal MUST return its stable stored result without running the handler.
- **FR-004**: Confirming an in-progress, rejected, invalid, or foreign proposal MUST produce a stable bounded refusal and MUST NOT execute.
- **FR-005**: An indeterminate in-progress execution MUST remain explicit and MUST direct callers to authoritative reconciliation rather than blind retry.
- **FR-006**: A successful reservation receipt MUST identify the proposal, capability, reservation if created, commitment, requested/applied/shortage quantities, and correlated business event.
- **FR-007**: Reservation verification MUST use tenant-scoped authoritative proposal, reservation, commitment, and event reads and distinguish execution from operational state and business outcome.
- **FR-008**: `capability_describe` MUST describe `proposal_approve_and_execute` including preconditions, principal/approval rules, refusals, retry/replay/unknown semantics, effects, receipt, and verification.
- **FR-009**: Confirmation MUST remain excluded from default model-selectable tool schemas.
- **FR-010**: Discovery MUST be read-only and unknown/internal capability names MUST remain non-disclosing.

### Domain and Traceability Requirements

- **DR-001**: The proposal is the authority/decision boundary; the reservation remains the operational Reality record and the business event is its correlated execution evidence.
- **DR-002**: Correlation MUST use existing opaque proposal, reservation, commitment, and event IDs without document-number identity or duplicated state.
- **DR-003**: All claims, receipts, and verification reads MUST remain tenant-scoped and use shared application services for API, MCP, chat, and CLI callers.
- **DR-004**: This feature MUST add no generic workflow infrastructure and no Source/Evidence/Reality duplication.

### Key Entities

- **ChangeProposal**: Prepared, attributable request whose lifecycle establishes whether execution is available, in progress, executed, or rejected.
- **Reservation**: Operational allocation owned by Reality and linked directly to its Commitment.
- **BusinessEvent**: Immutable correlated evidence that the reservation creation was committed.
- **Execution receipt**: Stored public result that correlates the confirmed proposal with the exact effect and its verification reads.

## Success Criteria

- **SC-001**: A repeated concurrency test produces exactly one reservation and one correlated event in 100% of runs.
- **SC-002**: A lost-response replay returns the same stored receipt and creates zero additional business records.
- **SC-003**: All required confirmation guidance fields are machine-readable while confirmation appears in zero default model schemas.
- **SC-004**: Verification tests reject every planted wrong-ID, wrong-quantity, missing-event, and unrelated-state case.
- **SC-005**: Existing backend, tenant-isolation, API, MCP, migration, lint, and spec-policy suites remain green.

## Assumptions and Dependencies

- PostgreSQL is the only supported database and provides the conditional-update concurrency boundary.
- Existing `BusinessEvent.action_id`, `causation_id`, and `correlation_id` fields provide the shortest receipt correlation without schema expansion.
- Current clients can tolerate additional proposal lifecycle values and response fields.

## Open Questions

None. The three linked issues and the approved implementation order fully bound this feature.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-005 | US1 | PostgreSQL concurrency, replay, interruption, and refusal tests |
| FR-006–FR-007, DR-001–DR-003 | US2 | reservation receipt and planted-defect verification tests |
| FR-008–FR-010 | US3 | capability discovery and model-exposure tests |
| DR-004, SC-005 | all | schema review and complete quality gates |
