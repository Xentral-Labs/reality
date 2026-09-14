# Feature Specification: Complete Read Capability Guidance

**Feature Branch**: `048-complete-read-guidance`
**Created**: 2026-09-03
**Status**: Approved for implementation
**Language**: English
**Input**: "Identify all necessary public reads and add canonical guidance for them."

## Context and Intent

### Problem

Six public business reads still expose only a name, schema, and short description.
Agents can call them but cannot canonically distinguish operational queues from
independent verification, or understand freshness, empty results, and non-proofs.

### Scope

- Complete guidance for every currently public business read.
- Add `fulfillment_queue`, `fulfillment_blockers`, `item_supply_demand`,
  `exception_explain`, `proposals_awaiting_approval`, and `finance_balances`.
- Keep one shared `capability_describe` lookup for MCP and Chat.
- Route the pending-proposals read through the shared application-tool boundary.
- Make catalog validation fail when any public business read lacks guidance.

### Non-Goals

- Describing `capability_describe` with itself.
- Adding reads, projections, tables, commands, authority, or agent orchestration.
- Claiming that derived queues, balances, or exceptions are source truth beyond their
  declared data basis.

## User Scenarios & Testing

### User Story 1 - Discover every business read safely (Priority: P1)

An agent can describe every public business read before relying on its result.

**Independent Test**: Compare the public read registry with the guidance registry;
only the `capability_describe` meta-read may be excluded.

**Acceptance Scenarios**:

1. **Given** the public MCP catalog, **When** business reads are enumerated, **Then** every read except the meta-read has exactly one complete description.
2. **Given** a new public read without guidance, **When** catalogs load, **Then** validation fails before advertisement.

### User Story 2 - Distinguish operations, attention, approval, and finance (Priority: P2)

An agent selects the smallest read and does not overclaim what a derived result proves.

**Independent Test**: Each new description exposes distinct use, data basis,
limitations, verification role, non-proof, unknown state, and next step.

**Acceptance Scenarios**:

1. **Given** a blocked order, **When** queue and blocker guidance are compared, **Then** the queue supplies work state while blockers supply derived causes.
2. **Given** an empty pending-proposals result, **When** guidance is consulted, **Then** it proves only that no pending proposal is visible in the current tenant read.
3. **Given** finance balances, **When** used for verification, **Then** ledger-derived receivable/payable position is distinguished from bank settlement and reconciliation.

### User Story 3 - Preserve the shared service boundary (Priority: P3)

MCP and Chat call the same non-mutating application tools for all described reads.

**Independent Test**: Every read description resolves from one public identity to one
registered non-mutating application tool, including pending proposals.

**Acceptance Scenarios**:

1. **Given** `proposals_awaiting_approval`, **When** invoked through MCP, **Then** it delegates to the shared application read and preserves its response.
2. **Given** guidance targets a missing or mutating application tool, **When** catalogs load, **Then** validation fails.

### Edge Cases

- A materialized projection is stale or empty.
- A blocker disappears between list and explanation reads.
- A proposal is approved while the pending list is read.
- Ledger entries exist but provider settlement is absent.
- A future public business read is added without guidance.

## Requirements

### Functional Requirements

- **FR-001**: Every current public business read MUST have exactly one canonical description; only the description meta-read is exempt.
- **FR-002**: The six remaining reads MUST include complete use, non-use, context, data-basis, limitation, freshness, empty/refusal, verification, unknown, next-step, and example guidance.
- **FR-003**: Guidance MUST distinguish operational work queues, derived blocker context, source-linked explanation, pending approvals, and ledger-derived finance position.
- **FR-004**: An empty or successful read MUST NOT be described as proof beyond its returned tenant-scoped state and declared data basis.
- **FR-005**: Every described read MUST map to one public MCP identity and one registered non-mutating application tool.
- **FR-006**: Pending-proposal listing MUST use the shared application-tool boundary while preserving public behavior.
- **FR-007**: Catalog validation MUST reject any future public business read that is missing guidance.
- **FR-008**: Existing six read descriptions and proposal descriptions MUST remain compatible.

### Domain and Traceability Requirements

- **DR-001**: Projection and queue descriptions MUST name their shortest authoritative Reality data basis.
- **DR-002**: Exceptions, blockers, proposals, and balances MUST remain derived or operational views, not new business authority.
- **DR-003**: Existing tenant boundaries and confirmation rules MUST remain unchanged.
- **DR-004**: No schema, migration, or duplicated business state may be added.

## Success Criteria

- **SC-001**: 100% of public business reads are described, with only one documented meta-read exemption.
- **SC-002**: All six new descriptions contain an explicit non-proof and unknown condition.
- **SC-003**: Registry drift and mutating/missing targets fail deterministic tests.
- **SC-004**: All existing read responses remain compatible.

## Assumptions and Dependencies

- The current public MCP registry defines the bounded set of necessary reads.
- `capability_describe` is metadata infrastructure and is intentionally not self-described.
- The owner's request approves completing this bounded catalog without further scope questions.

## Open Questions

None.

## Requirement Traceability

| Requirement                  | Scenario   | Evidence                            |
| ---------------------------- | ---------- | ----------------------------------- |
| FR-001, FR-007               | US1        | Public-read completeness drift test |
| FR-002–FR-004, DR-001–DR-002 | US2        | Six-read semantic matrix tests      |
| FR-005–FR-006, DR-003        | US3        | MCP/application parity tests        |
| FR-008, DR-004               | Regression | Existing guidance and full suite    |
