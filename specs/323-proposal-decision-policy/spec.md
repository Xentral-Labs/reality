# Feature Specification: Consistent Proposal Decision Policy

**Created**: 2026-10-02
**Status**: Implemented and verified
**Language**: English
**Input**: Unify proposal approval requirements used by presentation and execution, separating company role, decision authority and permitted channels.

## Context and Intent

### Problem

Proposal next-step guidance mixes company roles with a generic human-decision label.
The guidance can disagree with execution: credit-hold release requires an owner at
execution but can be described as an ordinary member decision. External access with
confirmation permission also does not establish that a human made the decision.
Users and agents need accurate requirements without gaining new authority.

### Scope

- One consistent decision requirement for each proposal action, used for both
  explanation and authorization.
- Separate required company authority, explicit decision requirements and permitted
  confirmation channels.
- Accurate reporting of existing contextual exceptions and technical limits.
- Preserve current external confirmation access and built-in Chat restrictions.

### Non-Goals

- Autonomous agent approval, agent-to-agent delegation or new confirmation rights.
- Proof that a human physically performed an external-client decision.
- New company roles, business tables, queues or proposal lifecycle states.
- Changes to operational business effects or verification formulas.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Web contract](../../docs/WEB_SPEC.md), proposal approval and execution.
- [Built-in Chat access](../278-human-chat-confirmation/contracts/chat-access.md)
- [OAuth access](../265-oauth-mcp-user-access/contracts/oauth.md)

## User Scenarios & Testing

### User Story 1 - Understand and enforce the same requirement (Priority: P1)

A person reviewing a proposal sees the authority that execution actually requires.

**Why this priority**: Incorrect guidance causes failed handoffs and can misstate authority.

**Independent Test**: Compare review requirements and confirmation outcomes for
finance account creation, settlement, costing, credit-hold release, shipment and reservation.

**Acceptance Scenarios**:

1. **Given** an owner-governed proposal, including credit-hold release, **When** it
   is prepared or reviewed, **Then** all surfaces describe owner authority and an
   ordinary member is refused when confirming.
2. **Given** a reviewed shipment, **When** an active company member confirms,
   **Then** the applicable member requirement is shown and enforced without an
   additional owner requirement.
3. **Given** an ordinary reservation proposal, **When** it is reviewed, **Then**
   its actual confirmation requirement is explained without inventing a new role
   named authorized human or granting owner-only authority.
4. **Given** membership or proposal state changed after preview, **When** confirmation
   is attempted, **Then** current authority and existing stale-state checks are enforced.

### User Story 2 - Understand channel and decision limits (Priority: P1)

A client distinguishes access to the confirmation operation from authority to make
an autonomous business decision.

**Why this priority**: A permissioned external call must not be presented as proof of human approval.

**Independent Test**: Exercise built-in Chat, authenticated Web, permissioned external
clients and existing trusted local contexts against the same proposal requirements.

**Acceptance Scenarios**:

1. **Given** built-in Chat, **When** it prepares a proposal, **Then** it hands off
   to human review and cannot confirm or reject it.
2. **Given** an external client with confirmation access, **When** it confirms,
   **Then** exact-proposal explicit approval and existing business authority checks
   remain required; access alone is not represented as delegated autonomous authority.
3. **Given** token-only attribution, **When** a decision is displayed, **Then** no
   human identity or independently verified human decision is inferred.
4. **Given** an existing trusted local or platform exception, **When** requirements
   are evaluated, **Then** its applicable context is preserved and not generalized
   into unrestricted external-agent access.

### Edge Cases

- Cross-company proposals and identities remain inaccessible.
- Unknown or retired actions cannot acquire confirmation authority from a fallback label.
- Review markers provide review evidence, not an independent role definition.
- Missing identity, removed membership and inactive users follow existing restrictions.
- Replayed, rejected and executing proposals retain existing lifecycle behavior.

## Requirements

### Functional Requirements

- **FR-001**: Preparation, review and execution MUST use the same action-specific
  decision requirements; contextual requirements MUST be evaluated for the current context.
- **FR-002**: Requirements MUST distinguish company authority, explicit approval,
  permitted confirmation channels and whether autonomous delegation exists.
- **FR-003**: Existing owner-only actions, including credit-hold release, MUST be
  described and enforced as owner-only in ordinary authenticated company contexts.
- **FR-004**: Ordinary actions MUST retain existing authority boundaries without
  acquiring an owner-only restriction from this consolidation.
- **FR-005**: Built-in Chat MUST remain unable to settle proposals; external
  confirmation MUST retain its existing access and business-authority checks.
- **FR-006**: Explanations MUST NOT claim human-decision proof from a boolean approval
  argument or token identity; no autonomous delegation is granted by this feature.
- **FR-007**: Confirmation MUST recheck current authority while preserving review,
  stale-state, tenant, replay and reconciliation protections.
- **FR-008**: Existing compatibility guidance MUST remain accurate during transition;
  documentation and clients MUST explain the new distinctions consistently.

### Domain and Traceability Requirements

- **DR-001**: Decision requirements MUST NOT alter Source → Evidence → Reality
  effects or introduce stored derived business authority.
- **DR-002**: All channels MUST use shared application authorization, preserve tenant
  scope and retain existing decision attribution without inventing a human identity.

## Success Criteria

- **SC-001**: Every scoped action and context has zero discrepancies between
  displayed decision requirements and tested confirmation outcomes.
- **SC-002**: No tested client gains confirmation authority or loses an existing
  authorized business path as an unintended consequence of consolidation.
- **SC-003**: Every requirement has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The owner approved this concrete scope on 2026-10-02 and instructed continuation.
- Agent delegation requires a separate approved design and is excluded here.
- Existing external explicit approval is an authorized-decision assertion, not
  independent evidence of human involvement.
- No schema expansion is needed; existing specialized authority checks must be
  inventoried before technical planning.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-003 | US1.1–2 | Action requirement and execution parity matrix |
| FR-002, FR-006 | US2.2–3 | Decision metadata and attribution contract checks |
| FR-004 | US1.3 | Ordinary-action authority regression |
| FR-005 | US2.1–2 | Chat exclusion and external access regression |
| FR-007 | US1.4; edge cases | Changed membership, state, review and replay checks |
| FR-008 | US1.1–3; US2.2–3 | Client compatibility and documentation checks |
| DR-001 | US1.1–3 | Existing business-effect verification regression |
| DR-002 | US2.1–4; edge cases | Shared boundary, attribution and tenant isolation checks |
