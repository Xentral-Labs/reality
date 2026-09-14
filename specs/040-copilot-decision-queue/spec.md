# Feature Specification: Copilot Decision Queue and Chat Archiving

**Feature Branch**: `040-copilot-decision-queue`
**Created**: 2026-09-02
**Status**: Approved
**Language**: English for all repository artifacts and recorded decisions.
**Input**: "Keep proposal approvals available independently of chat, archive chats instead of deleting them, and provide a central decision queue alongside operational exceptions."

## Context and Intent

### Problem

Deleting a Copilot conversation currently removes its messages while tenant-wide pending
Change Proposals remain. The Copilot then renders those proposals in an empty conversation,
which hides their origin and makes the product appear inconsistent. Operators also have no
complete Web view for pending and decided proposals; Home exposes only a count.

### Scope

- Replace ordinary chat deletion with reversible archiving.
- Keep archived conversations and their messages available through an explicit archive view.
- Add a tenant-wide decision queue beside Exceptions for pending proposals and decision history.
- Keep proposal approval and rejection independent from whether a conversation is open.
- Prevent tenant-wide proposals from appearing inside an empty conversation.
- Leave the onboarding/example Home as soon as an exception or any proposal history exists.

### Non-Goals

- Requiring an operator to approve or reject before leaving or archiving a conversation.
- Automatically approving, rejecting, or deleting proposals when a conversation is archived.
- Adding workflow approvals to Documents or operational records.
- Reconstructing proposal-to-chat provenance that was never stored.
- Changing mutation execution semantics or application tools.

### Existing Contracts

- `docs/WEB_SPEC.md`
- `docs/features/chat.md`
- `docs/features/operational_exceptions.md`
- `.specify/memory/constitution.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review all decisions centrally (Priority: P1)

An operator opens Exceptions and can switch to a decision queue containing every pending
proposal for the active company, then approve or reject an exact proposal through the existing
confirmation boundary.

**Independent Test**: Create proposals through different mutation tools, open the decision
queue, and verify all pending proposals are visible and one can be reviewed and decided.

**Acceptance Scenarios**:

1. **Given** pending proposals from Chat or another application adapter, **When** the operator
   opens Pending approvals, **Then** every tenant-owned pending proposal is listed once.
2. **Given** a pending proposal, **When** the operator reviews and explicitly approves it,
   **Then** the existing approval-and-execution service runs the exact proposal.
3. **Given** a pending proposal, **When** the operator explicitly rejects it, **Then** it leaves
   the pending queue without executing business state.
4. **Given** decided proposals, **When** Decision history is selected, **Then** executed and
   rejected decisions are shown read-only with their status and proposal details.
5. **Given** a company without imported business records but with an exception or any pending,
   executed, or rejected proposal, **When** Home opens, **Then** the operational cockpit replaces
   the onboarding example and exposes the pending-decision count.

### User Story 2 - Archive conversations without losing history (Priority: P2)

An operator archives a conversation to remove it from the active list without deleting its
messages or changing any proposal.

**Independent Test**: Archive a conversation, verify it leaves the active list, appears in the
archive, can be restored, and retains every message.

**Acceptance Scenarios**:

1. **Given** an active conversation, **When** it is archived, **Then** it disappears from the
   active list while its messages remain stored.
2. **Given** an archived conversation, **When** the archive is opened, **Then** the conversation
   can be read and restored.
3. **Given** a conversation while tenant proposals are pending, **When** it is archived, **Then**
   no proposal is approved, rejected, executed, or deleted.
4. **Given** no active conversation, **When** Copilot opens, **Then** the empty state contains no
   tenant-wide proposal cards and directs decision work to Pending approvals.

### Edge Cases

- Archiving or restoring a foreign-tenant conversation behaves as not found.
- Repeating archive or restore does not lose messages or mutate proposals.
- An empty pending queue and an empty decision history each have a truthful empty state.
- Historic proposals may have no conversation provenance and remain valid tenant decisions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Exceptions MUST provide distinct `Exceptions`, `Pending approvals`, and
  `Decision history` views with visible counts where available.
- **FR-002**: Pending approvals MUST list all and only tenant-owned proposals with status
  `proposed`, independently of Chat session state.
- **FR-003**: Decision history MUST list tenant-owned executed and rejected proposals read-only.
- **FR-004**: Approval and rejection MUST continue through the existing explicit confirmation
  and shared application boundary.
- **FR-005**: Ordinary Chat removal MUST archive rather than delete the conversation or messages.
- **FR-006**: Operators MUST be able to view archived conversations and restore one.
- **FR-007**: Archiving or restoring a conversation MUST NOT change any Change Proposal state.
- **FR-008**: Copilot MUST NOT render tenant-wide proposal cards when there is no active session.
- **FR-009**: Proposal inputs containing arrays or objects MUST render as readable structured
  values rather than implicit object strings.
- **FR-010**: Home MUST show onboarding/example content only while the company has no operational
  records, no derived exceptions, and no pending or historic Change Proposals.

### Domain and Traceability Requirements

- **DR-001**: Operational Exceptions remain derived observations and MUST NOT become approval
  records or manually closable tickets.
- **DR-002**: Change Proposals remain the single tenant-scoped audit representation for prepared,
  rejected, and executed mutations across Chat, Web, CLI, and MCP.
- **DR-003**: Web endpoints MUST use tenant-scoped services and existing proposal execution tools;
  browser code MUST NOT contain alternative business rules.
- **DR-004**: Chat archive state MUST be stored explicitly and must not remove audit history.

### Key Entities

- **Chat Session**: A tenant-owned conversation with an active or archived presentation state.
- **Chat Message**: Durable conversation content retained when its session is archived.
- **Change Proposal**: The tenant-wide auditable decision record with proposed, rejected, or
  executed status.
- **Operational Exception**: A derived current risk, displayed separately from decisions.

## Success Criteria *(mandatory)*

- **SC-001**: Every pending proposal is reachable from the decision queue without opening Chat.
- **SC-002**: Archiving and restoring representative conversations retains 100% of their messages.
- **SC-003**: Tests observe zero proposal status changes caused by archive or restore operations.
- **SC-004**: Empty Copilot screens contain zero orphaned approval cards.
- **SC-005**: Every requirement has an executable test or documented verification task.
- **SC-006**: A company with proposal or exception activity reaches the operational Home in every
  representative acceptance case, even when source and business-record counts are zero.

## Assumptions and Dependencies

- Closing or navigating away from Chat never requires an immediate decision.
- The existing approve-and-execute and reject services remain authoritative.
- Proposal-to-chat provenance is deferred because existing proposals do not carry that link.
- Archived conversations are retained until a separately specified retention policy exists.

## Open Questions

No unresolved product questions remain.

## Requirement Traceability

| Requirement | Scenario(s) | Planned evidence |
|---|---|---|
| FR-001–FR-004 | US1 scenarios 1–4 | API/service and Web decision-queue tests |
| FR-005–FR-007 | US2 scenarios 1–3 | Archive/restore service and API tests |
| FR-008–FR-010 | US1 scenario 5; US2 scenario 4; edge cases | Home-state and Web rendering contract tests |
| DR-001–DR-004 | All scenarios | Domain review, tenant tests, schema migration test |
