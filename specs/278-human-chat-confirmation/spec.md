# Feature Specification: Human Chat Confirmation

**Feature Branch**: `278-human-chat-confirmation`
**Created**: 2026-09-26
**Status**: Implemented and verified
**Language**: English
**Input**: Prevent the built-in Chat agent from approving its own business mutations while preserving its ability to discover current state, prepare exact proposals, and hand them to a human for review and confirmation.

## Context and Intent

### Problem

During a browser qualification of ordinary B2B order-to-cash scenarios, the built-in Chat
agent discovered master data, prepared customer and payment-term proposals, and then called
the confirmation tool itself. It described this as having obtained review tokens and began
executing the proposals without a separate human decision on the exact reviewed changes.

This makes the proposal preview ineffective as a control. An operator may ask Chat to carry
out a broad multi-step goal, but that instruction is not confirmation of each exact proposal
that Chat later constructs. Agents still need complete read access to current operational
state and the ability to prepare reviewed work; the authority to cross the mutation boundary
must remain with an authenticated human using the canonical decision review.

### Scope

- Remove proposal confirmation and rejection authority from the built-in Chat model toolset.
- Keep read and proposal tools available so Chat can discover current state and prepare work.
- Require Chat to stop after preparation, explain that no change has happened, and direct the
  operator to the canonical decision review.
- Preserve human confirmation through the existing authenticated review endpoint and UI.
- Prove that broad, explicit, repeated, or tool-shaped conversation instructions cannot make
  the model execute or reject its own proposal.
- Keep current fulfillment-readiness, proposal-review and execution rules as the authoritative
  source of business state and effects.

### Non-Goals

- Removing confirmation tools from external MCP clients; those clients retain their explicit
  token permissions and existing attribution semantics.
- Redesigning the decision-review UI delivered by spec 276.
- Changing payment, reservation, shipment or fulfillment-readiness business rules delivered by
  spec 275.
- Adding document-owned operational or payment statuses.
- Automatically executing a batch because the user approved an earlier natural-language goal.

### Existing Contracts

- `.specify/memory/constitution.md`, especially Principle IV.
- `docs/WEB_SPEC.md`, especially Human-readable decision review.
- `docs/features/order_to_cash.md` and `docs/features/shipments.md`.
- `specs/275-fulfillment-safety-parity/spec.md`.
- `specs/276-human-readable-decision-review/spec.md`.

## User Scenarios & Testing

### User Story 1 - Chat prepares but cannot decide (Priority: P1)

An operator asks Chat to create or change business records. Chat reads the current company
state, prepares exact proposals and presents them as pending decisions. It cannot approve,
reject or execute those proposals itself, even when the initial request says to carry the work
through.

**Why this priority**: A model approving its own proposal bypasses the repository's mandatory
human confirmation boundary and can create unreviewed business effects.

**Independent Test**: Simulate a provider that first calls a proposal tool and then attempts
to call proposal confirmation or rejection. Prove the decision tools were never offered, the
proposal remains pending, and no business event or target record is created.

**Acceptance Scenarios**:

1. **Given** ordinary production Chat, **When** its model tool catalog is built, **Then** read
   and proposal tools are available while proposal confirmation and rejection tools are absent.
2. **Given** a broad user request to carry a mutation through, **When** Chat prepares the exact
   proposal, **Then** the proposal remains pending and the response directs the operator to the
   canonical human review without claiming any effect.
3. **Given** conversation text that names a confirmation tool, proposal ID, review token or
   instruction to self-approve, **When** Chat handles it, **Then** the conversation cannot expand
   Chat's tool authority and no proposal decision occurs.

---

### User Story 2 - Human review remains executable and attributable (Priority: P1)

An authenticated operator opens the pending decision produced by Chat, reviews its exact
effect and confirms or rejects it. Reality records the human decision and executes through the
same canonical application service used by other supported surfaces.

**Why this priority**: Removing model authority must not strand valid proposals or introduce a
second mutation path.

**Independent Test**: Prepare a Chat proposal, confirm it through the authenticated Web review
path, and prove the effect occurs once with the deciding user recorded; repeat with rejection
and prove zero business effect.

**Acceptance Scenarios**:

1. **Given** a pending Chat-created proposal, **When** an authorized human confirms it through
   canonical review, **Then** it executes once and records that human as the decision maker.
2. **Given** a pending Chat-created proposal, **When** an authorized human rejects it, **Then**
   it becomes rejected and creates no target business effect.
3. **Given** stale readiness or changed review-bound state, **When** a human confirms an old
   proposal, **Then** existing stale-review protection refuses it without effect.

---

### User Story 3 - Agent retains full operational awareness (Priority: P2)

Before proposing a change, Chat can read the relevant parties, items, locations, inventory,
reservations, commitments, payment evidence and fulfillment readiness. Its handoff identifies
what it found, what it proposed, what remains blocked and which human decision is needed.

**Why this priority**: Safe loss of execution authority must not reduce the agent to a blind
form-filler or force the operator to supply discoverable company data.

**Independent Test**: Ask Chat to prepare a stocked and a blocked fulfillment scenario. Verify
that it uses canonical reads, reports current blocker evidence, prepares only supported work and
leaves each mutation pending for human review.

**Acceptance Scenarios**:

1. **Given** discoverable tenant records, **When** Chat prepares related work, **Then** it reads
   them before asking the user for identifiers already available through canonical tools.
2. **Given** zero freely available stock or a payment blocker, **When** Chat discusses shipment,
   **Then** it reports the canonical readiness result and does not claim the order is ship-ready.
3. **Given** a multi-step request that exceeds one turn, **When** Chat reaches a pending human
   decision, **Then** it stops at that durable boundary and identifies the remaining steps rather
   than self-confirming or claiming completion.

### Edge Cases

- The provider emits a tool call for a confirmation alias that was not offered: dispatch refuses
  it and records no decision or business effect.
- A user pastes a valid proposal ID and review token into Chat: they remain untrusted conversation
  content and confer no authority.
- A proposal was already confirmed outside Chat: Chat may read and explain the settled result but
  cannot repeat or reverse the decision.
- Playground Chat remains read-only and gains no proposal capability.
- External MCP clients retain permission-scoped confirmation tools; this feature changes only the
  built-in model's tool boundary.
- A human confirmation loses its response: existing proposal reconciliation and idempotency rules
  remain authoritative.

## Requirements

### Functional Requirements

- **FR-001**: The built-in production Chat model MUST have read and proposal access but MUST NOT
  have proposal confirmation or rejection access.
- **FR-002**: The built-in Chat model tool catalog MUST omit every canonical or compatibility
  alias that can approve, execute, reject or otherwise settle a proposal.
- **FR-003**: Conversation content MUST NOT broaden the server-selected Chat tool access, including
  explicit proposal IDs, review tokens or instructions to invoke a decision tool.
- **FR-004**: Chat MUST describe mutation tools as preparation only and MUST state that a pending
  proposal has not changed business state.
- **FR-005**: After preparing a proposal, Chat MUST direct the operator to the canonical human
  decision review and MUST NOT claim approval, execution or rejection without a settled receipt.
- **FR-006**: Authenticated human review MUST retain the existing ability to confirm or reject a
  Chat-created proposal with current permissions, review-token validation and stale-state checks.
- **FR-007**: A settled decision MUST retain its actual human attribution; the built-in model or
  Chat channel MUST NOT be recorded as the deciding principal for new decisions.
- **FR-008**: Attempts by the built-in model to invoke an unoffered decision tool MUST be refused
  before application execution and create no proposal decision or business effect.
- **FR-009**: Playground Chat MUST remain read-only, and external MCP confirmation permissions
  MUST retain their existing behavior.
- **FR-010**: Chat MUST retain canonical read access needed to inspect current operational and
  financial state before preparing work.
- **FR-011**: Chat handoff for a multi-step workflow MUST distinguish completed reads, pending
  proposals, current blockers and steps that require a human decision.
- **FR-012**: Generated tool documentation MUST remain unchanged unless the executable public MCP
  catalog changes; a Chat-only access-policy change MUST NOT misstate external MCP capabilities.

### Domain and Traceability Requirements

- **DR-001**: This feature MUST create no new operational authority; proposal status, decision
  attribution and resulting Business Events remain linked through existing opaque identities.
- **DR-002**: Fulfillment, payment, stock and reservation observations MUST continue to be derived
  at read time from their existing Reality records and evidence, never copied onto Documents.
- **DR-003**: Chat, Web and MCP MUST continue to call shared tenant-scoped application services;
  only the built-in model's granted access changes.
- **DR-004**: Every affected read and mutation attempt MUST preserve tenant isolation and existing
  interaction/audit recording.

### Key Entities

- **Change Proposal**: A tenant-scoped, exact pending business mutation prepared by Chat but not
  decided by it.
- **Human Decision**: An authenticated approval or rejection recorded against the proposal and
  attributable to the deciding user.
- **Chat Tool Access**: The server-selected capabilities exposed to the built-in model; it is not
  mutable by conversation content.
- **Fulfillment Readiness**: The existing read-time operational decision Chat may inspect and
  explain before preparing work.

## Success Criteria

- **SC-001**: In automated provider simulations, 100% of built-in Chat tool catalogs omit all
  proposal settlement tools and aliases.
- **SC-002**: In mutation stories, 100% of Chat-prepared proposals remain pending until a separate
  authenticated human review occurs.
- **SC-003**: Human confirmation executes each tested proposal exactly once and records the human
  decision maker; rejection produces zero target business effects.
- **SC-004**: Prompt-injection and direct tool-name attempts produce zero proposal decisions and
  zero target business effects.
- **SC-005**: Existing fulfillment-readiness, proposal reconciliation, external MCP permission,
  tenant-isolation and Playground Chat tests remain green.
- **SC-006**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Specs 275 and 276 are implemented and remain the authoritative readiness and review contracts.
- The canonical Web decision review is the human confirmation surface for built-in Chat proposals.
- An external MCP agent may still receive confirmation authority through an explicitly configured
  access token; that separate trust boundary is outside this feature.
- Broad natural-language authorization is intent to prepare work, not confirmation of an exact
  proposal generated later.
- No schema expansion is required.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003, FR-008 | US1.1, US1.3 | Built-in Chat catalog and unoffered-tool refusal tests |
| FR-004–FR-005 | US1.2 | Provider conversation contract and pending-proposal story |
| FR-006–FR-007 | US2.1–US2.3 | Authenticated review approval/rejection and attribution tests |
| FR-009 | Edge cases | Playground and external MCP regression tests |
| FR-010–FR-011 | US3.1–US3.3 | Read-before-propose and workflow-handoff tests |
| FR-012 | US1–US3 | Catalog generation diff/check |
| DR-001–DR-004 | US1–US3 | Proposal, event, tenant and interaction assertions |
