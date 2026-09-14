# Feature Specification: Always Available Storylines and Playground

**Feature Branch**: `fix/always-available-playground`
**Created**: 2026-09-14
**Status**: Scope accepted through the owner's explicit request to remove the switch.
**Language**: English
**Input**: Remove the deployment switch so Storylines and Playground are always available.

## Context and Intent

### Problem

Production lists storylines but rejects their start because an obsolete deployment
switch is absent. Demo setup and Storyline interpret its absence differently.

### Scope

Make Storyline, compact Playground, Sandbox setup and requested free-trial entry
regular product capabilities under their existing account and company policies.
Remove REALITY_PLAYGROUND_ENABLED from supported configuration, including its
explicit false behavior, and stop advertising it in current deployment guidance.

### Non-Goals

No authentication, admission, ownership, confirmation, quota, archive, external-effect
or lesson-boundary relaxation. No new records, UI redesign, scheduler changes,
automatic creation on reads, deployment or merge.

### Existing Contracts

- [Company setup](../../docs/features/company-setup-demo.md) and spec 146.
- [Learning Playground](../../docs/features/learning-playground.md), specs 096 and 182.
- [Free trial](../190-free-playground/spec.md), [Web](../../docs/WEB_SPEC.md).

This feature supersedes only the deployment-switch requirements in these contracts.

## User Scenarios & Testing

### User Story 1 - Start learning without deployment setup (Priority: P1)

An eligible account can use the Storyline library, compact Playground, create an
empty or demo Sandbox, and enter its explicitly requested free-trial demo.

**Why this priority**: A visible supported product action must not need an operator toggle.
**Independent Test**: Exercise shared services and HTTP entry with the retired variable
absent, false, true, blank and malformed, preserving identical eligible behavior.

**Acceptance Scenarios**:

1. **Given** an eligible account, **When** inspecting entry options, **Then** Storyline,
   Playground and Sandbox entry are available without a deployment toggle.
2. **Given** the same account and explicit confirmed request, **When** creating or
   retrying a Sandbox or Storyline, **Then** the same regular services succeed even
   when an old deployment still supplies a false or malformed toggle value.
3. **Given** a new operator following current setup documentation, **When** deploying,
   **Then** no Playground enablement variable is required or advertised.

### User Story 2 - Keep private practice boundaries (Priority: P1)

Availability never grants unauthorized access or executes an unconfirmed action.

**Why this priority**: Removing configuration must preserve business authorization.
**Independent Test**: Run existing ownership, admission, confirmation, quota,
archive, durable-lock and replay tests with no opt-in setup.

**Acceptance Scenarios**:

1. **Given** an unverified, rejected or suspended account or another owner, **When**
   requesting protected practice actions, **Then** existing denials remain.
2. **Given** missing confirmation, exhausted quotas or an archived company, **When**
   requesting creation or mutation, **Then** existing restrictions remain.
3. **Given** a completed or interrupted setup, **When** reading or retrying,
   **Then** reads create nothing, retry reuses the receipt and later source controls
   and archive state are preserved.

### Edge Cases

Old false/blank/malformed environment values; pending accounts keep private Sandbox
eligibility without ordinary-company admission; free-trial entry still needs an
active verified account and recorded consent; owner changes; quota exhaustion;
concurrent retries; initialization interruption; archived or paused demos.

## Requirements

### Functional Requirements

- **FR-001**: Storyline, compact Playground, Sandbox setup and requested free-trial
  entry MUST NOT depend on REALITY_PLAYGROUND_ENABLED, regardless of its value.
- **FR-002**: Existing availability response fields MUST remain compatible and report
  capability availability as true; account eligibility remains separately enforced.
- **FR-003**: Existing account, owner, confirmation, quota, archival, idempotency and
  operation restrictions MUST remain unchanged.
- **FR-004**: Current configuration examples and operator documentation MUST remove
  the obsolete switch and explain regular availability. Historical specs may name
  it only as historical/superseded behavior.

### Domain and Traceability Requirements

- **DR-001**: Existing shared services and Source → Evidence → Reality flows MUST be
  reused, without new authorities, schema, source conversion or direct adapter writes.
- **DR-002**: Tenant isolation, read-only discovery and shortest true links MUST be preserved.

## Success Criteria

- **SC-001**: Eligible users can start each supported practice entry in every retired
  switch state tested, without operator intervention.
- **SC-002**: Existing protected-account and company-boundary scenarios keep their outcomes.
- **SC-003**: Every FR and DR has executable proof or explicit diff-review evidence.

## Assumptions and Dependencies

The owner's request authorizes removal, including explicit false semantics, rather
than a new default. Existing fields remain for client compatibility. Sandbox source
controls and independent capacity settings are retained. Deploying the new code is
separate; old application versions still interpret the retired variable.

## Open Questions

None. Scope review: no additional product decision or schema change is required.

## Requirement Traceability

| Requirement | Scenarios | Planned evidence |
|---|---|---|
| FR-001–002 | US1.1–2 | Service and API parameterized regression tests |
| FR-003 | US2.1–3 | Existing protected entry, lock, replay and quota suites |
| FR-004 | US1.3 | Repository search and documentation/configuration diff review |
| DR-001–002 | US2.1–3 | Service/story/API tests and schema/adapter diff review |
