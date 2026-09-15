# Feature Specification: Delete Empty Chat Sessions

**Feature Branch**: `feat/delete-empty-chat`
**Created**: 2026-09-15
**Status**: Approved
**Language**: English
**Input**: "An empty chat should be deleted instead of moving into the archive."

## Context and Intent

### Problem

Starting a conversation creates a durable Chat Session before a person sends a message. Removing
an abandoned empty session currently archives it, filling the archive with untitled, content-free
containers that carry no conversation history.

### Scope

- Permanently remove a tenant-owned Chat Session when it has no messages.
- Continue to archive every Chat Session containing at least one durable message.
- Describe the consequence truthfully as delete for an empty session and archive otherwise.
- Preserve tenant isolation and the shared application-service boundary.

### Non-Goals

- Permanently deleting any session containing a message.
- Deleting or changing Change Proposals, business records, or source evidence.
- Adding retention schedules, bulk cleanup, or administrator deletion tools.
- Treating a default title such as "New conversation" as proof that a session is empty.

### Existing Contracts

- `specs/040-copilot-decision-queue/spec.md`
- `specs/040-copilot-decision-queue/contracts/http-api.md`
- `docs/features/chat.md`
- `docs/WEB_SPEC.md`
- `.specify/memory/constitution.md`

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Remove an abandoned empty conversation (Priority: P1)

An operator starts a conversation but sends no message. Removing that entry permanently removes
the empty container instead of adding noise to the archive.

**Why this priority**: Empty artifacts make the archive misleading and retain no useful history.

**Independent Test**: Create a Chat Session without messages, remove it, and verify that it appears
in neither active nor archived sessions and cannot be restored.

**Acceptance Scenarios**:

1. **Given** an active Chat Session with zero durable messages, **When** its removal is confirmed,
   **Then** it is permanently removed and does not appear in the archive.
2. **Given** an active Chat Session with at least one durable message, **When** its removal is
   confirmed, **Then** the session and every message remain retained in the archive.
3. **Given** a foreign-tenant or unknown session identifier, **When** removal is requested, **Then**
   the operation behaves as not found and discloses no session state.

### User Story 2 - Understand the consequence before confirming (Priority: P2)

An operator can distinguish deletion of an empty session from archiving of a conversation before
confirming the action.

**Why this priority**: A destructive label must describe its consequence accurately.

**Independent Test**: Render one empty and one non-empty session and verify that the actions and
confirmations say delete for the empty session and archive for the non-empty session.

**Acceptance Scenarios**:

1. **Given** an empty session, **When** its options are opened, **Then** the action is labelled
   `Delete chat` and an in-product confirmation dialog describes permanent removal.
2. **Given** a session containing messages, **When** its options are opened, **Then** the action
   remains `Archive chat` and an in-product confirmation dialog describes reversible archiving.

### Edge Cases

- Emptiness is determined from durable messages, not title, age, UI state, or model output.
- A session with any assistant, system, failed-attempt, or user message is not empty.
- Repeating removal of a permanently deleted session behaves as not found.
- Removing an empty session does not mutate any tenant Change Proposal.
- The selected empty session transitions to the normal no-session state after deletion.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Removing a tenant-owned Chat Session with zero durable messages MUST permanently
  delete that session rather than archive it.
- **FR-002**: Removing a Chat Session with one or more durable messages MUST continue to archive
  the session and retain every message.
- **FR-003**: The conversation list MUST identify whether each session is empty using server-owned
  session state rather than title or browser inference.
- **FR-004**: The empty-session action and confirmation MUST communicate permanent deletion; the
  non-empty-session action and confirmation MUST communicate reversible archiving. Confirmation
  MUST use an accessible Reality-styled in-product dialog, not a browser-native confirmation box.
- **FR-005**: Permanent empty-session deletion MUST leave no restorable or archived Chat Session.
- **FR-006**: Removal MUST NOT mutate Change Proposals or any business Reality record.
- **FR-007**: Unknown and cross-tenant removal MUST behave as not found.

### Domain and Traceability Requirements

- **DR-001**: Emptiness MUST be derived from tenant-scoped durable Chat Messages; no stored flag or
  duplicated count is introduced.
- **DR-002**: API, Web, Chat, CLI, and MCP callers MUST share the same tenant-scoped removal service;
  the browser MUST NOT decide whether database deletion is allowed.
- **DR-003**: Source → Evidence → Reality is not applicable because deletion is restricted to a
  message-free conversation container and MUST NOT affect source, evidence, or Reality records.
- **DR-004**: A session containing any durable message remains governed by Spec 040 archive state.

### Key Entities

- **Chat Session**: Tenant-owned conversation container safe to delete only with no Chat Messages.
- **Chat Message**: Durable content whose existence changes removal from deletion to archiving.

## Success Criteria _(mandatory)_

- **SC-001**: 100% of removed zero-message test sessions appear in neither list and cannot restore.
- **SC-002**: 100% of removed sessions with messages remain restorable with every message intact.
- **SC-003**: Operators see the correct delete or archive consequence before every removal.
- **SC-004**: Cross-tenant and unknown-session tests disclose no session state.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Creating a Chat Session before its first message remains existing behavior.
- Chat Messages are the sole durable proof that a conversation contains retainable history.
- An empty Chat Session has no independent audit or business value requiring retention.
- Existing archive and restore behavior for non-empty sessions remains authoritative.

## Open Questions

No unresolved product questions remain.

## Requirement Traceability

| Requirement    | Scenario(s)                   | Planned test/evidence                       |
| -------------- | ----------------------------- | ------------------------------------------- |
| FR-001, FR-005 | US1 scenario 1                | Service and API deletion tests              |
| FR-002         | US1 scenario 2                | Service and API archive-retention tests     |
| FR-003, FR-004 | US2 scenarios 1–2             | API payload and Web contract tests          |
| FR-006         | US1 scenarios 1–2; edge cases | Proposal-state regression test              |
| FR-007         | US1 scenario 3                | Tenant-isolation tests                      |
| DR-001–DR-004  | All scenarios                 | Service-boundary and schema-review evidence |
