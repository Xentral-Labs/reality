# Feature Specification: Agent Interaction Baseline

**Baseline ID**: `014-agent-interaction`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline tenant-scoped Chat, application tools, proposals, confirmation, AI settings, and remote MCP access."

## Context and Intent

### Problem

Users and external agents need natural-language and tool access without bypassing
business services or mutating Reality unexpectedly. This baseline defines one tool
boundary, immediate safe reads, proposed mutations, explicit authorization, persistent
tenant conversations, and scoped remote MCP access.

### Scope

- Registered application read and mutation tools shared by Chat, MCP, Web, and CLI.
- Typed ChangeProposal lifecycle: proposed, confirmed/executed, rejected, non-replayable.
- Tenant-scoped persistent Chat sessions/messages and contextual prompt library.
- Deterministic no-network provider for automated tests.
- Tenant AI-provider settings with encrypted/revocable secrets.
- Hashed, tenant-scoped, revocable MCP bearer tokens with explicit tool allowlists.
- MCP read tools, mutation proposals, pending review, and separately authorized execution.

### Non-Goals

- Direct ORM access by a provider, Chat, MCP, or browser.
- Unconfirmed interactive mutations or autonomous approval.
- Treating model output as business truth.
- Provider-specific business logic; external model adapters remain replaceable.
- Broad MCP tokens unconstrained by tenant and tool permissions.

### Existing Contracts

- [`docs/features/chat.md`](../../docs/features/chat.md)
- [`docs/features/chat_sessions.md`](../../docs/features/chat_sessions.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

Providers return text and structured tool calls but never receive persistence access.
Read tools execute immediately through tenant-scoped services. Mutation tools store a
typed proposal and cause no business change until explicit confirmation; rejection,
tenant mismatch, replay, or unknown proposal prevents mutation. Chat sessions/messages
persist per tenant and Actions retain resulting identifiers.

Remote MCP authenticates with a hashed revocable token bound to one tenant and an
explicit tool allowlist. Mutation-oriented MCP tools create proposals; a separately
authorized approval tool executes the exact stored proposal. AI provider secrets are
encrypted at rest and never returned to the UI.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask a Tenant-Scoped Read Question (Priority: P1)

As a user or authorized MCP client, I can query inventory, exceptions, and explanations
without creating a proposal or business mutation.

**Why this priority**: Safe reads are the primary agent interaction.

**Independent Test**: Run equivalent read tools through application tool, Chat, and MCP
contexts and verify result, tenant scope, and unchanged business state.

**Acceptance Scenarios**:

1. **Given** an allowed read tool, **When** called, **Then** it executes immediately
   through the shared service with no ChangeProposal.
2. **Given** another tenant's opaque ID, **When** read/explained, **Then** it returns not found.
3. **Given** a Chat session, **When** messages are listed after tenant switch, **Then**
   only the selected tenant's sessions/messages appear.

### User Story 2 - Confirm a Mutation Deliberately (Priority: P1)

As a user, I can inspect a typed proposed action before any business mutation and then
confirm or reject exactly that action.

**Why this priority**: Human confirmation is the non-negotiable mutation boundary.

**Independent Test**: Propose Reservation, verify no allocation, confirm once, then
attempt replay, tenant change, and a rejected proposal.

**Acceptance Scenarios**:

1. **Given** a mutation tool call, **When** prepared, **Then** stored arguments and a
   human summary are visible while Reality remains unchanged.
2. **Given** explicit confirmation, **When** executed, **Then** the owning service runs
   once and output/action identifiers are audited.
3. **Given** rejection, replay, tenant mismatch, or tampering, **When** execution is
   attempted, **Then** no business mutation occurs.

### User Story 3 - Use Persistent Chat Safely (Priority: P2)

As a user, I can keep multiple tenant conversations, use contextual suggestions, and
see structured proposal/result cards.

**Why this priority**: Conversation is useful only when history and actions remain attributable.

**Independent Test**: Create sessions in two tenants, send read/mutation suggestions,
confirm one proposal, and inspect messages/actions after switching tenants.

**Acceptance Scenarios**:

1. **Given** one tenant, **When** conversations are created, **Then** sessions, titles,
   messages, and action results persist only there.
2. **Given** a contextual suggestion, **When** selected, **Then** it sends a normal
   message through the same provider/tool flow.
3. **Given** an empty tenant demo suggestion, **When** selected, **Then** it creates a
   proposal and requires confirmation before seeding.

### User Story 4 - Authorize a Remote MCP Client (Priority: P1)

As a tenant administrator, I can issue a one-time visible, hashed, revocable token with
an explicit tool allowlist and every call enforces it.

**Why this priority**: Remote agent access expands the security boundary.

**Independent Test**: Create a token, verify storage/one-time secret, call allowed and
disallowed tools, revoke it, and retry authentication.

**Acceptance Scenarios**:

1. **Given** a new token, **When** created, **Then** clear text is shown once while only
   its hash and tenant/tool authority persist.
2. **Given** an authenticated token, **When** allowed tool is called, **Then** it runs in
   that tenant; a non-allowlisted tool is rejected on every call.
3. **Given** revocation, **When** reused, **Then** authentication fails.
4. **Given** an MCP mutation proposal, **When** created, **Then** it requires separately
   authorized explicit approval before execution.

### Edge Cases

- Provider emits unknown tool, malformed arguments, or an error.
- Proposal arguments are changed after presentation.
- Proposal is confirmed twice, rejected after execution, or used under another tenant.
- Session belongs to another tenant or is removed mid-request.
- MCP token is absent, malformed, revoked, or lacks one requested tool.
- AI secret is replaced/cleared and old ciphertext/token must be revoked.
- External provider is unavailable; deterministic local behavior remains usable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Providers and interfaces MUST call registered application tools/services
  and MUST NOT receive ORM write access or implement business rules.
- **FR-002**: Read tools MUST execute immediately, remain tenant-scoped, and create no proposal.
- **FR-003**: Mutation tools MUST create a typed proposal with exact arguments and human
  summary and MUST NOT mutate business state before confirmation.
- **FR-004**: Explicit confirmation MUST execute the stored proposal at most once through
  its owning service; rejection MUST create no business mutation.
- **FR-005**: Tenant mismatch, replay, missing proposal, and argument tampering MUST prevent execution.
- **FR-006**: Chat sessions/messages/actions MUST belong to exactly one tenant and remain persistent.
- **FR-007**: Contextual suggestions MUST enter the normal Chat/tool path and MUST NOT
  provide a separate mutation implementation.
- **FR-008**: Automated tests MUST have a deterministic no-network provider covering
  reads, proposals, confirmation, rejection, and errors.
- **FR-009**: AI API secrets MUST be encrypted, replaceable/revocable, tenant-scoped,
  and never rendered back after entry.
- **FR-010**: MCP tokens MUST be hashed, tenant-scoped, revocable, and bound to explicit tools.
- **FR-011**: Every remote MCP call MUST authenticate and enforce the token's tool permission.
- **FR-012**: MCP mutation tools MUST propose first; execution MUST require an explicit
  approval tool authorized for that proposal.
- **FR-013**: Mutation execution and resulting business IDs MUST be retained as auditable Actions.

### Domain and Traceability Requirements

- **DR-001**: ChangeProposal/Action are interaction audit records, not substitutes for Reality.
- **DR-002**: Tool arguments MUST use opaque tenant-scoped IDs for relationships.
- **DR-003**: Chat/MCP explanation MUST preserve Source → Evidence → Reality trace from shared services.
- **DR-004**: Provider choice MUST NOT change business semantics or confirmation rules.

### Key Entities

- **ChatSession/ChatMessage**: Tenant-scoped persistent conversation and message.
- **ChangeProposal**: Exact proposed mutation and lifecycle state.
- **Action**: Auditable execution and result identifiers.
- **Secret**: Encrypted tenant provider credential with revocation lifecycle.
- **MCPAccessToken**: Hashed remote credential with tenant/tool authority and revocation.

## Reality Applicability

- **Source/Evidence/Reality**: Read/explain results retain canonical domain stages.
- **Interaction records**: Sessions, proposals, actions, secrets, and tokens are control/audit state.
- **Shortest links**: Proposal → exact tool arguments; Action → proposal/result IDs; tools
  resolve domain records through opaque IDs.
- **Stored/derived**: Conversations/authority/audit stored; tool results derive from domain truth.
- **Shared boundary**: Chat, MCP, Web, and CLI use the same registered tools/services.
- **Web explanation**: Proposal cards show exact action/summary before confirmation and
  link executed results to Inspect.

## Success Criteria *(mandatory)*

- **SC-001**: Read calls create zero proposals and zero business mutations.
- **SC-002**: Every tested mutation changes Reality only after one explicit confirmation.
- **SC-003**: Rejection, replay, tenant mismatch, and unauthorized tool calls produce zero mutation.
- **SC-004**: Switching tenants exposes zero foreign sessions, messages, proposals, or tool results.
- **SC-005**: Stored provider/MCP credentials never equal or render their clear text.
- **SC-006**: Revoked tokens/secrets cannot authorize subsequent use.
- **SC-007**: Local deterministic provider produces repeatable test outcomes without network.

## Assumptions and Dependencies

- External providers may be configured, but business semantics remain tool-defined.
- The human approving an MCP proposal is separately authorized for its tenant/tool.
- Full conversational model quality evaluation is outside this behavioral baseline.

## Open Questions

The product owner approved this baseline on 2026-08-31. Additional providers and
broader tool catalogs require future specs but must retain these confirmation and
service boundaries.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-005 | Verified as-is | Chat/Constitution contracts | application tool/proposal services | `tests/test_application_tools.py`; chat confirmation tests | — |
| FR-006–FR-008 | Verified as-is | Chat Sessions/Chat contracts | Chat services and DummyProvider | `tests/test_chat_confirmation.py` | — |
| FR-009 | Verified as-is | Web agent settings contract | secret/settings services | `tests/test_ai_mcp.py` secret tests and React API coverage | — |
| FR-010–FR-012 | Verified as-is | Web/MCP boundary | MCP auth/server/tools | `tests/test_ai_mcp.py` async token/tool tests | — |
| FR-013 | Verified as-is | Chat contract | proposal confirmation/action audit | application-tool, chat, and MCP tests | — |
| DR-001–DR-004 | Verified as-is | Constitution; Architecture | tool/service boundaries | agent, tenancy, explain tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-002 | US1 | Read tool, Chat, MCP, and tenant tests |
| FR-003–FR-005, FR-013 | US2 | Proposal/confirmation/rejection/replay tests |
| FR-006–FR-008 | US3 | Session, suggestion, and DummyProvider tests |
| FR-009–FR-012 | US4 | Secret, token, permission, revocation, MCP tests |
| DR-001–DR-004 | All | Boundary and trace review |
