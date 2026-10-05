# Feature Specification: Executed Decisions by affected order
**Feature Branch**: `codex/369-business-decision-discovery`
**Created**: 2026-10-05
**Language**: English
**Status**: Implemented and verified; optional external Claude round blocked by Mac lock
**Input**: After merging PR 374, the owner approved the next product point: discover executed Decisions through the affected order without supplying a proposal ID beforehand.

## Context and Intent
### Problem
Exact review and execution reads require a proposal ID. Pending approval discovery cannot find already executed order Decisions, although their effects and receipts are retained.
### Scope
Extend existing business discovery with executed Decision metadata and exact affected-order filtering. Follow established execution evidence and existing exact review/verification reads.
### Non-Goals
No extra report or daily command, new schema, business mutation, guessed associations, complete historical reconstruction, pending/failed Decision association, external scheduling or automatic approval.
### Existing Contracts
[MCP reads](../../docs/features/mcp_reads.md), specs 145, 323 and 366 retain pagination, service, grant, review and confirmation boundaries.

## User Scenarios & Testing
### User Story 1 - Find and verify an executed order Decision (Priority: P1)
An agent finds the affected order and discovers its executed Decision without advance knowledge of the proposal ID.
**Why this priority**: The agent must reconcile a past action without repeating it.
**Independent Test**: Discover a retained order, discover its executed reservation Decision, then read its existing exact execution status.
**Acceptance Scenarios**:
1. **Given** an executed reservation with retained execution evidence, **When** its order is selected, **Then** its opaque Decision ID and callable review/verification tools are returned.
2. **Given** several effects of one Decision, **When** discovered, **Then** it appears once.
3. **Given** unrelated orders sharing numbers, items or parties, **When** one order is selected, **Then** only explicitly linked executions are returned.
4. **Given** missing execution evidence or pending/rejected/failed Decisions, **When** selected by order, **Then** no executed association is invented and limited coverage is explicit.
### User Story 2 - Traverse safely (Priority: P1)
An agent traverses bounded results without obtaining payloads or new authority.
**Why this priority**: Audit metadata must preserve company and grant boundaries.
**Independent Test**: Compare page and legacy reads, cursor scopes, foreign references and unchanged storage.
**Acceptance Scenarios**:
1. **Given** multiple matching Decisions, **When** paginated, **Then** each appears once under the same filter; another order's cursor is refused.
2. **Given** a foreign order or Decision reference, **When** read, **Then** it behaves as not found without disclosure.
3. **Given** a restricted reader, **When** discovery is called, **Then** existing tool grants remain enforced; raw input/output, tokens and private contents are absent.
### Edge Cases
A commitment's explicit line membership takes precedence over its document fallback. Events with no action do not invent Decisions. Exact IDs remain opaque. Empty and final cursor pages retain normal selection-count boundaries. Unsupported document scoping on other families remains refused.

## Requirements
### Functional Requirements
- **FR-001**: Existing business discovery MUST support executed Decision metadata including opaque ID, tool, status, creation/decision times and existing review/verification read names, without raw inputs, outputs or credentials.
- **FR-002**: An exact order filter MUST select executed Decisions only through retained execution events for the order, its lines, commitments, reservations or movements, with shortest explicit membership and tenant scope on every selection. Duplicate effects MUST yield one Decision.
- **FR-003**: Page and bounded legacy formats MUST preserve their shapes and filters; cursor scope MUST bind the order; reads MUST perform no business/projection writes and retain authorization.
- **FR-004**: Discovery MUST describe retained execution-evidence coverage; absence MUST NOT claim absence of all historical actions. Existing exact review and status reads MUST accept the discovered ID without replay.
- **DR-001**: Durable and generated MCP guidance MUST explain the existing-tool flow and its coverage; focused tests, full CI, diff review and a fresh read-only live acceptance MUST be recorded separately from free-form model observations.
### Key Entities
Retained order, explicit commitment membership, effect record, execution event and existing Decision. No new stored entity or relationship.

## Success Criteria
### Measurable Outcomes
- **SC-001**: The reservation acceptance case discovers and verifies its executed Decision with zero advance proposal IDs and zero repeated effects.
- **SC-002**: Every tested unrelated or foreign reference is excluded, and every tested multi-event execution appears once.
- **SC-003**: Every tested response omits raw payloads and states retained coverage while preserving storage and grants.

## Assumptions and Dependencies
Scope acceptance is the owner's explicit request after the proposed next product point. Only stored executed status and retained event associations establish this search result. Existing exact review and execution tools remain authoritative for details. Historical events may be missing; no receipt-text or source co-occurrence inference is permitted.

## Requirement Traceability
| Requirement | Tests | Implementation |
|---|---|---|
| FR-001,FR-004 | T003,T007 | T004,T005 |
| FR-002 | T003 | T004 |
| FR-003 | T003,T006 | T004,T005 |
| DR-001 | T006,T007 | T005,T007 |
