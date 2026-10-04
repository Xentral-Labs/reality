# Feature Specification: Existing-tool evidence boundaries

**Feature Branch**: `codex/367-tool-evidence-boundaries`
**Created**: 2026-10-04
**Language**: English
**Status**: Accepted scope
**Input**: The owner approved fixing the five observed existing-tool gaps in a new PR after PR 372 merged.

## Context and Intent
### Problem
The daily response mistakes derived readiness conditions for recorded holds, applies inconsistent historical-cause boundaries, invents relationships between independent exceptions, assumes an unobservable external schedule is absent, and accepts provider output cut off by its token limit.
### Scope
Make those distinctions available through the existing shared reads and handle incomplete native provider responses explicitly.
### Non-Goals
No extra daily command or public tool, persisted authority, schema migration, scheduler, business mutation, external-client inspection, automatic continuation or tool replay, or guarantee of arbitrary model prose.
### Existing Contracts
- [MCP reads](../../docs/features/mcp_reads.md)
- [Shared scheduling](../../docs/features/scheduled-jobs.md)

## User Scenarios & Testing
### User Story 1 - Understand current conditions (Priority: P1)
An agent distinguishes recorded holds from derived readiness conditions and does not infer past nonexecution from either.
**Why this priority**: Incorrect causes and hold counts lead to incorrect operational advice.
**Independent Test**: Inspect ready, blocked and completed promises through the existing reads.
**Acceptance Scenarios**:
1. **Given** mixed holds and shortages, **When** read, **Then** each condition has an explicit kind and a projection condition key is not presented as a hold identity.
2. **Given** positive open quantity, **When** queue, readiness or order explanation is read, **Then** the same historical cause is unknown; for completed quantities it is not applicable.
3. **Given** two promises affected by one party hold, **When** counted, **Then** returned condition counts are not asserted to be counts of distinct hold records.
### User Story 2 - Respect visibility and association (Priority: P1)
An agent preserves the actual exception references and distinguishes external configuration unknown from absent.
**Why this priority**: Missing access does not prove a missing configuration or a causal business relationship.
**Independent Test**: Read exceptions and capability discovery with restricted access.
**Acceptance Scenarios**:
1. **Given** separate billing and shipping conditions, **When** listed or explained, **Then** actual references remain and a causal relationship to other conditions is not established by this result.
2. **Given** an external client, **When** capabilities are discovered, **Then** its schedule, mission, checkpoint, next run and pause state are explicitly outside Reality visibility and unknown.
### User Story 3 - Recognize incomplete answers (Priority: P1)
A user sees a clear incomplete-output notice when a native provider reaches its output limit.
**Why this priority**: A terminated transport can still contain an unfinished answer or tool call.
**Independent Test**: Exercise both providers through streamed and ordinary responses.
**Acceptance Scenarios**:
1. **Given** a provider output-limit stop, **When** received, **Then** the incomplete response is replaced by a localized notice and no tool call from that response executes.
2. **Given** streamed partial text followed by an output-limit stop, **When** received, **Then** a reset and notice replace it and the durable response contains the notice.
3. **Given** normal completion, **When** received, **Then** normal text and complete tool execution are preserved; genuine transport errors retain their existing handling.
### Edge Cases
Empty results prove no external completeness; legacy list shapes and page cursors remain compatible. Read-time additions do not create or refresh projection caches. Restricted credentials and tenant isolation remain unchanged. Recorded holds may be system-created; they are not all manual holds.

## Requirements
### Functional Requirements
- **FR-001**: Existing blocker outputs MUST distinguish recorded_hold from derived_readiness_condition without changing readiness rules or using condition keys as hold identities.
- **FR-002**: Queue lines, canonical readiness and exact order lines MUST share unknown versus not_applicable historical-cause semantics.
- **FR-003**: Exception list and explanation MUST preserve actual identities and state that causal relationships to other conditions are not established by this result.
- **FR-004**: Capability index and topic reads MUST mark external agent schedule, mission, checkpoint, next run and pause state unknown and outside Reality visibility, preserving grants.
- **FR-005**: Both native providers MUST detect output-limit stops in streaming and nonstreaming responses, replace incomplete output with a localized notice, and execute no tool calls from that response.
- **FR-006**: Additions MUST be transient shared read semantics, preserve tenant/access/confirmation and legacy container shapes, and add no business authority or external effects.
- **DR-001**: Existing tool descriptions, native guidance and generated references MUST document these boundaries; durable contracts MUST describe verification and limitations.
### Key Entities
Read-time interpretation fields on readiness, blocker conditions, exception evidence and capability discovery; provider stop signals. No new persisted entities.

## Success Criteria
### Measurable Outcomes
- **SC-001**: All covered reads distinguish holds and current conditions from unknown historical causes.
- **SC-002**: All covered discovery reads distinguish external visibility from configuration absence.
- **SC-003**: All four provider/transport combinations detect output limits with zero tool dispatch from incomplete responses.

## Assumptions and Dependencies
Owner acceptance is the explicit instruction to implement these five fixes after PR 372. Existing shared services remain authoritative. External clients must use the returned boundaries; arbitrary prose correctness is observed separately and not guaranteed. Output-limit handling terminates that response without retrying business work.

## Requirement Traceability
| Requirement | Acceptance | Tests | Implementation |
|---|---|---|---|
| FR-001 | US1.1,3 | T003 | T004 |
| FR-002 | US1.2 | T003 | T004 |
| FR-003 | US2.1 | T003 | T004 |
| FR-004 | US2.2 | T003 | T004 |
| FR-005 | US3.1–3 | T005 | T006 |
| FR-006 | Edge cases | T003,T005,T008 | T004,T006 |
| DR-001 | All stories | T007,T008 | T007 |
