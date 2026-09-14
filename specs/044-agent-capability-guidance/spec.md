# Feature Specification: Agent Capability Guidance

**Feature Branch**: `044-agent-capability-guidance`
**Created**: 2026-09-03
**Status**: Draft
**Language**: English
**Input**: "Give Chat and MCP agents one reliable way to understand when to use or avoid core Reality commands, propose them through the governed boundary, and verify the resulting business state. Begin with observe_fact, create_manual_order, reserve, and record_movement."

## Context and Intent

### Problem

Reality exposes typed commands and input schemas, but agents do not yet receive a
complete authoritative explanation of when a command is appropriate, when a similar
command must not be used, which refusals to expect, or which read model proves the
result. This knowledge can therefore be duplicated inconsistently in prompts. An agent
may create a Fact instead of typed Reality, confuse a promise with a physical event, or
treat a successful response as a verified business outcome.

### Scope

- Provide one canonical, read-only description of every capability explicitly adopted
  into the guidance catalog.
- Describe purpose, use and non-use conditions, required business context,
  preconditions, confirmation, retry identity, expected refusals, resulting events,
  verification reads, and bounded examples.
- Make capability descriptions discoverable through both Chat and MCP without
  changing business state.
- Provide complete descriptions for Fact observation, manual order creation, stock
  reservation, and physical movement recording.
- Reject incomplete, contradictory, or unresolvable capability guidance before it can
  be advertised to an agent.
- Preserve the existing proposal, confirmation, shared-service, and tenant boundaries.

### Non-Goals

- Recording interpretation outcomes or measuring SourceRecord processing coverage.
- Building a Commerce domain pack, mapping language, policy-learning system, or
  generic workflow engine.
- Automatically selecting or executing a command on behalf of an agent.
- Adding new business entities, Fact predicates, operational commands, or autonomous
  authority.
- Replacing command-side validation with descriptive guidance.
- Claiming that a command response alone proves the resulting business state.

### Existing Contracts

- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Agent capability guidance idea](../../docs/ideas/agent-capability-guidance.md)
- [Data model](../../docs/DATA_MODEL.md)
- [Chat](../../docs/features/chat.md)
- [Source ingestion](../../docs/features/source_ingestion.md)
- [Facts](../../apps/docs/content/concepts/facts.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand the correct capability (Priority: P1)

An agent handling a business request discovers a candidate Reality capability and
reads one authoritative description before proposing a mutation. The description
allows the agent and reviewing person to distinguish an observation from a promise,
allocation, or physical event.

**Why this priority**: Safe access to a command is insufficient if an agent cannot
reliably determine whether it is the correct business operation.

**Independent Test**: For each of the four initial capabilities, request its
description and verify that a person can determine the intended use, prohibited use,
required context, confirmation boundary, expected outcome, and verification reads
without inspecting source code or a private prompt.

**Acceptance Scenarios**:

1. **Given** an agent can discover registered Reality capabilities, **When** it asks
   for the reservation capability, **Then** it receives a read-only description that
   distinguishes allocation from physical movement and names the records and reads
   needed before and after execution.
2. **Given** a customer source states a shipping preference, **When** an agent compares
   Fact observation, reservation, and movement guidance, **Then** the guidance directs
   it toward a source-supported Fact proposal and explicitly rules out manufacturing
   typed stock state.
3. **Given** an unknown or non-agent capability name, **When** its description is
   requested, **Then** no business data changes and the caller receives a bounded,
   non-disclosing not-found result.

### User Story 2 - Review a complete proposal and verification path (Priority: P2)

An accountable person reviewing an agent proposal can see why the selected command
applies, what may refuse it, and which business view must be checked after execution.

**Why this priority**: Confirmation is meaningful only when the reviewer can understand
the proposed transition and the evidence that will later prove it.

**Independent Test**: Create proposals for the four initial capabilities, confirm that
each still uses the existing mutation boundary, and verify that its capability
description names at least one resolvable post-execution read that independently
exposes the relevant Reality.

**Acceptance Scenarios**:

1. **Given** an agent has selected a described capability, **When** it proposes the
   mutation through Chat or MCP, **Then** the existing confirmation-required proposal
   is created and no Reality record changes before approval.
2. **Given** an approved command succeeds, **When** the caller follows the declared
   verification guidance, **Then** it can re-read the relevant business view and
   distinguish a verified result from a response that has not yet been verified.
3. **Given** command execution is refused or its outcome cannot be reconciled with the
   declared business view, **When** the result is explained, **Then** it is not labeled
   verified and the declared refusal or recovery context remains visible.

### User Story 3 - Prevent guidance drift (Priority: P3)

A developer adding or changing an agent-visible command receives an immediate quality
failure when its semantic guidance is missing, references an unavailable read, or
contradicts its governed mutation boundary.

**Why this priority**: Guidance becomes unsafe if it silently diverges from executable
capabilities as the system evolves.

**Independent Test**: Introduce each supported drift defect into an isolated catalog
fixture and verify that validation reports the exact missing or invalid relationship.

**Acceptance Scenarios**:

1. **Given** an agent-eligible command lacks use, non-use, refusal, or verification
   guidance, **When** capability contracts are validated, **Then** validation fails and
   the command is not advertised as completely described.
2. **Given** guidance names an unknown command, event, projection, or agent tool,
   **When** contracts are validated, **Then** validation fails with an attributable
   error.
3. **Given** a mutation is advertised as read-only or bypasses confirmation, **When**
   parity checks run, **Then** the mismatch fails before release.

### Edge Cases

- Two commands share similar language but produce different kinds of Reality.
- A capability is registered for internal or administrative use but not agent use.
- A declared verification read exists but does not expose the affected Reality type.
- A command has no safe retry identity and must explicitly warn against unattended
  retry.
- A command can produce more than one accepted Business Event or refusal.
- Guidance examples contain human-readable numbers that must not be treated as IDs.
- Chat and MCP request the same description under different authenticated tenants.
- A capability description is requested while the underlying command remains valid
  but temporarily unavailable to the caller.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide one canonical description for each capability
  explicitly adopted into the guidance catalog and MUST provide complete descriptions
  for the four initial public proposal tools.
- **FR-002**: Each description MUST state the capability purpose, at least one use
  condition, at least one non-use condition, required business context, relevant
  preconditions, confirmation behavior, retry/idempotency guidance, expected refusals,
  expected outcome events, verification reads, and bounded positive and negative
  examples.
- **FR-003**: A caller MUST be able to discover and retrieve capability descriptions
  through both Chat and MCP using the same underlying catalog and read-only application
  path.
- **FR-004**: Retrieving or comparing descriptions MUST NOT create a proposal, execute
  a command, or mutate business state.
- **FR-005**: Unknown, internal-only, or unavailable capabilities MUST produce a
  bounded response without disclosing another tenant's data or administrative
  operations.
- **FR-006**: Fact observation guidance MUST state that Facts require source evidence
  and MUST NOT mirror Commitments, Reservations, Movements, or Ledger entries.
- **FR-007**: Manual order guidance MUST distinguish the creation of source evidence,
  order evidence, and Commitments from later reservation, movement, and financial
  events.
- **FR-008**: Reservation guidance MUST distinguish allocation from a physical
  Movement and identify the business views that expose both the reservation and its
  inventory consequence.
- **FR-009**: Movement guidance MUST distinguish a physical event from a promise,
  allocation, document status, or unsupported source claim.
- **FR-010**: Every described mutation MUST continue to use the existing typed
  proposal, confirmation, and shared application-service boundary.
- **FR-011**: Successful command execution MUST NOT be described as verified until a
  declared read independently exposes the expected resulting Reality.
- **FR-012**: Capability contract validation MUST reject missing mandatory guidance,
  duplicate capability descriptions, unresolved command/tool/event/read references,
  and disagreement with registered mutation or confirmation behavior.
- **FR-013**: The public developer documentation MUST explain the common agent loop,
  the Fact-versus-typed-Reality decision, and how to add valid guidance for another
  command.

### Domain and Traceability Requirements

- **DR-001**: Capability guidance MUST preserve Source → Evidence → Reality and MUST
  never instruct a caller to invent a source, skip applicable evidence, or manufacture
  typed Reality from unsupported model output.
- **DR-002**: Guidance MUST use the shortest true relationship and opaque IDs; examples
  MUST NOT turn document numbers, source labels, or display values into identity.
- **DR-003**: Chat and MCP MUST call the same tenant-safe read service and the same
  governed mutation tools; neither adapter may maintain alternative business guidance.
- **DR-004**: The feature MUST NOT require a new business table or expand the typed
  Reality schema because capability descriptions are configuration and derived
  application metadata rather than business truth.
- **DR-005**: Service-side domain validation remains authoritative when descriptive
  guidance and submitted command arguments disagree.

### Key Entities *(when data is involved)*

- **Capability Description**: Versioned application metadata explaining the safe use,
  prohibited use, context, outcomes, and verification path of one registered business
  command.
- **Verification Read**: A registered tenant-scoped business view that independently
  exposes the Reality expected after a command.
- **Refusal**: A stable, business-readable reason why an otherwise valid capability
  cannot perform the requested transition.
- **Example**: Bounded non-authoritative guidance demonstrating correct or incorrect
  command selection without supplying real tenant data or usable human-number identity.

## Success Criteria *(mandatory)*

- **SC-001**: All four initial capabilities provide complete descriptions from one
  authoritative source through both Chat and MCP.
- **SC-002**: Every FR and DR has an acceptance scenario and executable proof.
- **SC-003**: In a reviewed set of at least 12 command-selection scenarios covering
  observations, promises, allocations, and physical events, an agent using only the
  published guidance selects the intended capability or safely declines in every case.
- **SC-004**: Every planted missing, stale, contradictory, or unresolved guidance
  defect is rejected before the capability is advertised as complete.
- **SC-005**: No description lookup or comparison changes a proposal, Fact,
  Commitment, Reservation, Movement, LedgerEntry, or Business Event count.
- **SC-006**: For each initial mutation, a reviewer can identify the post-execution
  verification read and determine whether the outcome is verified in under two
  minutes without inspecting implementation code.

## Assumptions and Dependencies

- The existing command catalog, application tool registry, proposal confirmation,
  agent parity validation, and tenant-scoped projections remain authoritative.
- Guidance is keyed by public proposal-tool identity because one underlying service may
  expose capabilities with opposite intent, such as reservation creation and release.
- The four initial commands are enough to prove distinctions among observation,
  promise, allocation, and physical event without creating a generic workflow system.
- Capability descriptions are public product/developer semantics; they contain no
  tenant business data, credentials, private model prompts, or authorization grants.
- Verification in this feature means that a declared read exposes the expected Reality;
  orchestration of a durable multi-step verification state belongs to a later feature.
- Product/domain owner approval of this scope is required before technical planning.

## Open Questions

No unresolved clarification markers remain. Planning may choose the smallest catalog
shape and read interface consistent with these requirements.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-005 | US1 scenarios 1–3 | Catalog completeness and shared read-only Chat/MCP contract tests |
| FR-006–FR-009 | US1 scenarios 1–2 | Four initial capability descriptions and command-selection story tests |
| FR-010–FR-011 | US2 scenarios 1–3 | Proposal parity, no-preapproval-mutation, and verification-read tests |
| FR-012 | US3 scenarios 1–3 | Planted catalog drift and reference-resolution tests |
| FR-013 | US1 and US2 | Public documentation contract test |
| DR-001–DR-003 | US1 and US2 | Source/identity examples, tenant isolation, and adapter parity tests |
| DR-004–DR-005 | US2 and US3 | Schema-diff review and service-authority rejection tests |
| SC-001–SC-006 | All stories | Acceptance suite, command-selection evaluation, and reviewer walkthrough |
