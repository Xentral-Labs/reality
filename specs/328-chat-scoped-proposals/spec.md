# Feature Specification: Chat-Scoped Proposals

**Language**: English
**Created**: 2026-10-02
**Status**: Scope approved by owner (2026-10-02); ready for planning
**Input**: Proposals currently appear in every chat and sit below every conversation. A chat should show only
the proposals it created, at the point in its history where they were created, and keep them there once decided.

## Context and Intent

### Problem
`copilots_payload` returns `proposals_awaiting_approval(session, tenant_id)` for every active conversation:
every pending Change Proposal of the company, whoever or whatever created it. That includes proposals from other
chats, from MCP clients and from the CLI. The web renders that list fixed below the last message
(`ChatDecisionList` and `GraphReportProposal` in `ChatPage.tsx`). The result:

- A new or unrelated chat shows decisions that have nothing to do with it, and they look like a blocker.
- A proposal disappears from its chat when it is decided, so the history no longer shows what was proposed or
  what became of it.
- A Change Proposal stores no link to the conversation that created it. The chat cannot be filtered today, and
  "No timestamp-based attribution" (Storyline Free Play, `docs/features/chat.md`) rules out guessing the link.

The company-wide list of pending decisions already exists in the Decisions page (Pending approvals and Decision
history), and its count is already in the Inbox (spec 253).

### Scope
- Record which chat conversation created a proposal, when a chat turn creates it.
- Show a conversation's proposals in that conversation only, placed in its history where they were created.
- Keep decided proposals in their conversation with their outcome.
- In a conversation, point to company-wide pending decisions with a count and a link, not with a list.

### Non-Goals
- No change to who may approve or reject, to the exact review/confirmation token, to replay protection or to
  the decision policy (specs 263, 323, 325).
- No change to the Decisions page, the Inbox count, MCP proposal tools or CLI behavior.
- No backfill of proposals created before this feature. No conversation link is inferred from timestamps.
- No per-user chat ownership. Chat sessions stay company-scoped, as they are now.
- No redesign of the proposal review dialogs.

## User Scenarios & Testing

### User Story 1 — A chat shows only its own proposals (Priority: P1)
A person asks the chat to reserve stock. The chat creates a proposal. In that chat the proposal shows up under the
answer that proposed it. In a new chat, or in any other chat, it does not show up.

**Independent Test**: Create a proposal through a chat turn in session A and another through MCP. Read session A,
session B and a new empty session.

**Acceptance Scenarios**:
1. Given a proposal created by a turn in session A, when session A is read, then the proposal is returned with
   session A's messages.
2. Given the same proposal, when session B or a new session is read, then it is not returned.
3. Given a proposal created through MCP, the CLI or another non-chat path, when any chat session is read, then it
   is not returned as part of that conversation.
4. Given a proposal created before this feature, when any chat session is read, then it is not returned, and it
   stays reachable in the Decisions page.

### User Story 2 — Proposals stay where they happened (Priority: P1)
A conversation goes on after a proposal. The proposal stays at the place where it was made, between the turn that
created it and the turns that came later, instead of moving to the bottom. Once it is approved, rejected or fails,
it stays there with its outcome.

**Independent Test**: Create a proposal in turn 1, send turns 2 and 3, then approve it. Reload the conversation and
check the order and the outcome. Repeat with rejection.

**Acceptance Scenarios**:
1. Given a proposal created during turn 1, when later turns follow, then it is shown after the turn-1 answer and
   before turn 2.
2. Given a pending proposal, when it is shown, then its review can be opened as today.
3. Given an approved, rejected or failed proposal, when the conversation is read, then it is still shown at the
   same place with its outcome and decision time, and it no longer offers approval.
4. Given an archived conversation, when it is opened, then its proposals are shown with their current state.
   Archiving or restoring never changes a proposal.

### User Story 3 — Other pending decisions are a hint, not a block (Priority: P2)
A person in a chat can see that the company has pending decisions elsewhere and can get to them in one step.
Those decisions do not take up the conversation.

**Independent Test**: With two pending proposals outside the open conversation and one inside it, read the
conversation and follow the hint.

**Acceptance Scenarios**:
1. Given pending proposals that do not belong to the open conversation, when the chat is shown, then a compact
   count is visible outside the message history and opens the Decisions page on Pending approvals.
2. Given no such proposals, then no hint is shown.
3. Given a pending proposal of the open conversation, then it is not counted in the hint.

### Edge Cases
A turn that creates several proposals; a turn that fails after a proposal was created and flushed; a turn on the
deterministic local provider; graph report change proposals (`graph.reports.change`), which render with their own
card; the chat agent settling its own proposal in a later tool call; a proposal decided through MCP or the Decisions
page while the chat is open; removal of an empty conversation; a conversation archived while its proposal is
pending; foreign-tenant session ids; private (sealed) report proposals, whose readability rules from spec 325 stay
unchanged; company archive/deletion and account deletion; rolling deployment where the web is older or newer
than the API.

## Requirements

### Functional Requirements
- **FR-001**: A Change Proposal created during a chat turn MUST record the chat session that ran the turn. This
  applies to every provider, including the deterministic local provider, and to every proposal tool reached from
  that turn.
- **FR-002**: Proposals created outside a chat turn (MCP, CLI, web forms, services, demo data) MUST record no chat
  session.
- **FR-003**: The conversation read MUST return only proposals linked to the requested session, in every state
  (proposed, executed, rejected, failed), for active and archived conversations.
- **FR-004**: The conversation read MUST name, for each proposal, the message it follows: the last message of that
  session before the first user message sent after the proposal was created (the answer of the turn that created
  it), or the last message when no later user message exists. It is derived at read time and never stored. A user
  message MUST carry the time it was sent, so a proposal made during a turn falls between that turn's question and
  any later question.
- **FR-005**: A settled proposal shown in a conversation MUST show its outcome and decision time and MUST NOT offer
  approval. A pending one MUST open the existing review.
- **FR-006**: The conversation read MUST include the number of pending proposals of the company that are not
  linked to that session. The web MUST show it as a compact link to Pending approvals, outside the message history,
  and MUST hide it when the number is zero.
- **FR-007**: Archiving, restoring or removing a conversation MUST NOT change, delete or settle a proposal. A
  conversation that holds a proposal is not empty: removing it archives it.
- **FR-008**: Tenant scope, approval rights, exact confirmation, replay protection, decision attribution and the
  private-review rules of spec 325 MUST stay unchanged.
- **FR-009**: New web text MUST be translated into all four existing languages.

### Data Requirements
- **DR-001**: Change Proposal gains one optional, tenant-scoped reference to the Chat Session that created it.
  This is the shortest true link. Proposals do not reference a chat message, and messages do not reference
  proposals.
- **DR-002**: Existing proposals keep a null reference. No migration infers one.
- **DR-003**: The reference is set once at creation and never changed.
- **DR-004**: Placement in the history and the "elsewhere" count are read-time derivations and are not stored.

### Key Entities
Change Proposal (existing, gains the chat session reference); Chat Session and Chat Message (existing, unchanged).

## Success Criteria
- **SC-001**: Service and API tests show that a session returns only its own proposals, in every state, and that
  MCP, CLI and legacy proposals appear in no conversation.
- **SC-002**: Service tests show the link is recorded for the model-backed and the local provider path, and is
  absent outside a chat turn.
- **SC-003**: A browser proof shows a proposal in its conversation between the right turns, still there with its
  outcome after approval and after rejection, absent from a new chat, and the hint opening Pending approvals.
- **SC-004**: Required backend, web, i18n, lint, docs-catalog and spec checks pass; failures are recorded honestly.

## Assumptions and Dependencies
- The chat turn already runs inside one service call (`send_chat_message`), so the creating session is known
  where proposals are made. The plan decides how it reaches `create_change_proposal`.
- The Decisions page stays the company-wide place to review pending decisions.
- Existing browser scripts that expect `[data-chat-decision-list]` to show proposals created outside the chat need
  their fixtures moved to a chat-created proposal or to the Decisions page.
- The schema change is justified by FR-001/FR-003: the chat must filter and place proposals by conversation, and
  no existing record holds that link (the Storyline recorder holds it only inside a storyline).
- Docs to update: `docs/features/chat.md`, `docs/features/chat_sessions.md`, `docs/DATA_MODEL.md`.

## Requirement Traceability

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-001, FR-002, DR-001–DR-003 | Story 1.1–1.3 | Service tests for chat turn (model and local provider), MCP and CLI proposal creation |
| FR-003, FR-007, DR-002 | Story 1, Story 2.4 | Copilot payload tests per session, archived session, legacy null proposals |
| FR-004, FR-005, DR-004 | Story 2 | Payload placement test; browser proof for order and outcome |
| FR-006 | Story 3 | Payload count test; browser proof for the hint |
| FR-008 | Edge cases | Existing decision, replay, attribution and private-review suites stay green |
| FR-009 | Story 3 | `npm run test:i18n` |
