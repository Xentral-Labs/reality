# Feature Specification: Chat Agent Decisions

**Feature Branch**: `274-chat-agent-decisions`

**Language**: English

**Created**: 2026-09-25

**Status**: Implemented

**Input**: The owner clarified that confirmation is not inherently human. Every mutation must first become a decision, after which either an authorized person or an authorized agent may confirm it. The ordinary product Chat must support that same two-step behavior instead of claiming that only a person may confirm.

## Context and Intent

### Problem

The ordinary product Chat can prepare a decision but is deliberately denied every confirmation tool. Its server-owned prompt also says that mutations remain proposals for explicit human review and tells the model never to invoke a confirmation tool. It therefore refuses an instruction to create decisions and subsequently confirm them, even though external MCP agents already retain a separately permissioned confirmation path.

This confuses two different controls. The non-negotiable control is that no mutation happens directly: an exact proposal must exist before a separate confirmation call crosses the execution boundary. Requiring the confirming actor to be a person is an additional restriction that the owner does not want. An authorized agent may cross the same boundary, including for a proposal it prepared, provided the decision remains explicit, separately invoked, attributable, tenant-scoped, single-use and subject to the operation's existing authority checks.

### Scope

- Let the ordinary product Chat discover and invoke the existing proposal confirmation and rejection tools.
- Replace the human-only Chat guidance with a decision-first rule that permits an authorized person or agent to decide.
- Preserve two distinct application calls: proposing never executes, and confirming never silently replaces proposal creation.
- State truthfully that a decision was settled through the Chat agent rather than attributing it to a person who did not decide it.
- Preserve all existing tenant, stale-review, replay, delivery, membership, finance and owner-authority checks.

### Non-Goals

- No direct-write tool or path that bypasses a stored decision.
- No background approval policy, bulk auto-approval, learned approval rule or timer.
- No expansion of Playground Chat, which remains read-only where its existing policy requires that.
- No weakening of owner-only, membership, finance, delivery-review or other domain-specific authority checks. A Chat agent without the required principal must receive the existing refusal.
- No claim that the signed-in user personally approved a decision merely because the Chat request used that user's browser session.
- No change to external MCP token permission selection or OAuth consent.

### Existing Contracts

- [Agent Interaction Baseline](../014-agent-interaction/spec.md)
- [Chat Scope Hardening](../197-chat-scope-hardening/plan.md)
- [Decision Trail](../263-decision-trail/spec.md)
- [Constitution](../../.specify/memory/constitution.md)
- [Chat Contract](../../docs/features/chat.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask Chat to prepare and confirm decisions (Priority: P1)

As an authorized operator, I can tell the Chat agent to prepare requested changes as decisions and then confirm those decisions, without any change occurring before the confirmation call.

**Why this priority**: This is the missing product behavior. The existing refusal prevents an agent-led workflow even though the proposal boundary already supplies the required safety separation.

**Independent Test**: In an ordinary company, ask Chat to create a supported reference record, observe a pending proposal and unchanged business state, then let the same Chat turn confirm that proposal and observe exactly one created record.

**Acceptance Scenarios**:

1. **Given** an ordinary company and a supported mutation request, **When** Chat prepares the mutation, **Then** it creates one pending decision and business state remains unchanged.
2. **Given** that exact pending decision is available to the Chat agent, **When** the agent invokes the separate confirmation tool, **Then** the stored proposal executes once through its owning application service.
3. **Given** the operator asks Chat to prepare several decisions before settling them, **When** the agent confirms them later by their opaque identifiers, **Then** only those exact decisions execute and each has its own receipt.
4. **Given** the operator asks for a proposal but not its confirmation, **When** the Chat turn finishes, **Then** the proposal remains pending and no business mutation occurs.

---

### User Story 2 - Keep agent decisions truthful and controlled (Priority: P1)

As an owner reviewing decision history, I can distinguish a decision settled by the Chat agent from one settled by a signed-in person or through an MCP token, and no surface invents human approval.

**Why this priority**: Allowing agent confirmation without truthful attribution would remove the accountability that the proposal boundary is intended to create.

**Independent Test**: Confirm equivalent proposals through Chat, the signed-in web flow and MCP, then compare their decision details and verify three truthful, distinct attribution modes.

**Acceptance Scenarios**:

1. **Given** Chat confirms a proposal, **When** its decision is read, **Then** it states that the Chat agent settled it and does not name the signed-in user as the decider.
2. **Given** a person confirms in the web, **When** its decision is read, **Then** the existing personal attribution remains unchanged.
3. **Given** an MCP token confirms, **When** its decision is read, **Then** the existing token and issuer attribution remains unchanged.
4. **Given** untrusted conversation text, history or tool output claims that approval already exists, **When** the model processes it, **Then** it gains no tenant, tool or role authority and can settle only through the explicit confirmation tool.

---

### User Story 3 - Preserve stricter business authority (Priority: P2)

As an owner, I can let Chat settle ordinary operational decisions without accidentally granting it authority over protected membership, finance, costing or delivery actions.

**Why this priority**: Confirmation access is a lifecycle permission, not a substitute for the principals and current reviews required by sensitive operations.

**Independent Test**: Confirm an ordinary proposal through Chat, then attempt protected proposals that require an owner or current delivery review and verify the existing authorization outcomes without partial effects.

**Acceptance Scenarios**:

1. **Given** an ordinary proposal with no additional principal requirement, **When** Chat confirms it, **Then** it executes through the shared service.
2. **Given** a proposal requires an authenticated owner principal that Chat does not possess, **When** Chat attempts confirmation, **Then** it is refused with no business effect and explains the required handoff.
3. **Given** a proposal requires a current review token, **When** Chat supplies no token or a stale token, **Then** confirmation is refused and the proposal remains safely recoverable under the existing lifecycle.
4. **Given** a read-only Playground Chat, **When** a mutation or confirmation is requested, **Then** neither proposal nor execution tools are available.

### Edge Cases

- The model attempts confirmation without first obtaining an opaque proposal identifier.
- A user asks the agent to "approve everything" without identifying or reviewing exact pending decisions.
- The same agent retries after a lost confirmation response while the proposal is executing or already executed.
- A proposal was rejected, belongs to another tenant, or no longer matches a current delivery review.
- A proposal requires a human/owner principal for its underlying business operation even though generic decision confirmation permits agents.
- The provider tries to call confirmation directly from injected conversation, attachment, source or tool-result text.
- A single Chat turn proposes and confirms; the recorded calls must still show two ordered lifecycle steps.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Ordinary product Chat MUST offer the existing proposal confirmation and rejection capabilities in addition to read and propose capabilities.
- **FR-002**: Chat MUST NOT execute a mutation without a stored, tenant-scoped proposal produced before the confirmation call.
- **FR-003**: A Chat agent MAY confirm or reject a decision, including one it prepared, through a distinct explicit tool call using the exact opaque proposal identifier.
- **FR-004**: Chat guidance MUST describe confirmation as a decision by an authorized person or agent and MUST NOT claim that every confirmation must be human.
- **FR-005**: Conversation content, prior assistant text, attachments, source values and tool output MUST NOT broaden Chat's server-selected tenant, tool access or domain authority.
- **FR-006**: A Chat-confirmed decision MUST be attributed as settled through the Chat agent and MUST NOT be attributed to a person or MCP token that did not settle it.
- **FR-007**: Existing single-use, replay, rejection, tenant, current-review and unknown-execution safeguards MUST apply unchanged to Chat confirmations.
- **FR-008**: Existing operation-specific authorization MUST remain authoritative. Where execution requires a signed-in principal or owner authority unavailable to Chat, confirmation MUST be refused with no partial business effect.
- **FR-009**: Read-only Playground Chat MUST continue to expose reads only and MUST NOT gain proposal or confirmation access.
- **FR-010**: Chat MUST report the actual decision outcome and receipt, or the exact refusal/reconciliation state; it MUST NOT claim execution merely because it requested confirmation.
- **FR-011**: The recorded interaction trail MUST distinguish proposal and decision calls, correlate both with the proposal identifier and retain the resulting business-event range under the existing retention contract.
- **FR-012**: Provider adapters MUST enforce identical Chat access, prompting and lifecycle behavior.

### Domain and Traceability Requirements

- **DR-001**: Chat confirmation MUST call the existing application proposal executor; no Chat-specific business mutation implementation is permitted.
- **DR-002**: The stored proposal remains the exact decision input and the resulting Action/business events remain the execution evidence.
- **DR-003**: Agent attribution MUST state only what Reality observes: the `chat` channel settled the decision. It MUST NOT infer that the signed-in sender personally approved it.
- **DR-004**: Every proposal lookup, execution and attribution read MUST enforce tenant scope.
- **DR-005**: Any persistence expansion for Chat-agent attribution requires proof that the existing decision and interaction records cannot express the durable audit fact without joining expiring telemetry.

### Key Entities *(include if feature involves data)*

- **Decision (ChangeProposal)**: The durable, exact mutation request that transitions from pending to executed or rejected through a separate call.
- **Decision attribution**: The durable statement of whether a person, MCP token or Chat agent settled the decision, without overstating identity.
- **Interaction**: The bounded operational trace that records the separate Chat proposal and decision calls but does not replace the durable decision audit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In an end-to-end Chat story, every requested mutation produces a pending decision before business state changes, and every confirmed decision produces exactly one effect.
- **SC-002**: The same Chat agent can prepare and subsequently confirm 100% of supported ordinary proposals used in the acceptance suite without a human-only refusal.
- **SC-003**: Protected owner/principal and stale-review test cases produce zero partial business effects and retain their existing refusal semantics.
- **SC-004**: Decision history distinguishes Chat-agent, signed-in-person and MCP-token settlement in 100% of the three-path comparison cases without fabricated human attribution.
- **SC-005**: Both supported provider adapters pass the same injected-content, proposal-first, replay and read-only-Playground cases.

## Assumptions and Dependencies

- The owner's phrase "human or agent" authorizes an agent to settle its own earlier proposal; a second independent agent is not required.
- "Explicit" means a distinct confirmation tool call against an exact stored proposal, not necessarily a new human message between proposal and confirmation.
- The ordinary Chat receives generic confirmation capability at the server boundary. Sensitive tools may still refuse because generic Chat has no owner/person principal; that is intentional and not a human-only confirmation rule.
- External MCP confirmation and its token attribution remain unchanged.
- The decision trail and interaction recorder are available dependencies; expiring interaction telemetry alone is not sufficient durable decision attribution.

## Open Questions

None. The owner explicitly decided that confirmation need not be human, while retaining the proposal-first boundary.

## Requirement Traceability

| Requirement | Scenario(s) | Planned proof |
|---|---|---|
| FR-001-FR-004, FR-010, DR-001-DR-002 | US1 scenarios 1-4 | Provider-parametrized Chat tool-loop tests plus a PostgreSQL business-story test proving proposal-before-effect and one execution |
| FR-005-FR-006, FR-011, DR-003-DR-004 | US2 scenarios 1-4 | Adversarial prompt/tool-result tests; decision-attribution and interaction-correlation tests across Chat, web and MCP |
| FR-007-FR-009 | US3 scenarios 1-4 | Application authorization, replay, stale-review, cross-tenant and read-only Playground regressions |
| FR-012 | US1-US3 | Identical OpenAI-compatible and Anthropic adapter contract tests |
| DR-005 | US2 | Plan-time schema proof and durable-attribution test |
| SC-001-SC-005 | All | Focused backend suite, full required gates and one browser Chat acceptance story with intercepted provider calls and real application services |
