# Feature Specification: Read Capability Guidance

**Feature Branch**: `047-read-capability-guidance`
**Created**: 2026-09-03
**Status**: Approved for implementation
**Language**: English
**Input**: "Extend capability guidance beyond commands so agents understand important read and verification capabilities."

## Context and Intent

### Problem

Agents can discover read tools, but canonical guidance currently describes only four
proposal capabilities. A schema does not explain what a read establishes, which
authoritative records or projections support it, what it cannot prove, or when its
result is incomplete or stale. These semantics can be duplicated in prompts and lead
to unsafe proposals or false verification claims.

### Scope

- Add a distinct validated guidance contract for public read capabilities.
- Describe knowledge provided, authoritative data basis, limitations, freshness,
  refusal/empty behavior, verification role, unknown conditions, and safe next steps.
- Cover `interpretation_coverage`, `business_records_discover`, `order_explain`,
  `commitments_list`, `inventory_read`, and `exceptions_list`.
- Return read and proposal descriptions through `capability_describe`.
- Reject incomplete, contradictory, mutating, or unresolvable read guidance.

### Non-Goals

- Describing every public read or command in this slice.
- Changing read results, business rules, authority, or confirmation.
- Automatically choosing, chaining, or executing tools.
- Creating tables, policies, prompts, routines, or a workflow engine.
- Treating an empty read or successful API response as proof.

### Existing Contracts

- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Read guidance idea](../../docs/ideas/read-capability-guidance.md)
- [Agent capability guidance](../044-agent-capability-guidance/spec.md)
- [Interpretation coverage](../045-interpretation-coverage/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select the right read before acting (Priority: P1)

An agent compares canonical descriptions and chooses the smallest read that provides
the IDs and context needed without treating search, evidence, projection, or exception
output as stronger truth than it is.

**Why this priority**: Safe proposals depend on correct observation and identity first.

**Independent Test**: Retrieve all six descriptions and distinguish discovery,
interpretation, explanation, operational registers, and attention signals using their
purposes, data bases, limitations, and examples.

**Acceptance Scenarios**:

1. **Given** an agent needs an order ID, **When** it compares discovery and order explanation, **Then** it is directed to discover first and explain only a selected record.
2. **Given** an empty exceptions list, **When** guidance is read, **Then** it does not imply all processes are correct or complete.
3. **Given** a source question, **When** interpretation coverage is selected, **Then** processing outcome remains distinct from canonical Reality.

### User Story 2 - Verify without overclaiming (Priority: P2)

After a governed effect, an agent selects a verification read and knows what supports
success and which conditions leave the outcome unknown.

**Why this priority**: A successful command response alone is not verification.

**Independent Test**: Confirm that relevant descriptions state what they prove, do not
prove, and when reconciliation or another read remains necessary.

**Acceptance Scenarios**:

1. **Given** stock was reserved, **When** inventory is re-read, **Then** it can verify derived reserved quantity but not physical movement.
2. **Given** a movement response, **When** the relevant read is stale or omits the subject, **Then** the outcome remains unknown.

### User Story 3 - Prevent read-guidance drift (Priority: P3)

A developer receives a deterministic failure if read guidance references a missing or
mutating tool, omits limitations, claims authority it does not own, or cannot state its
verification boundary.

**Why this priority**: Incorrect guidance is more dangerous than missing prose.

**Independent Test**: Validate planted unknown/mutating tools, missing fields, invalid
roles, unresolved data bases, and contradictory side-effect claims.

**Acceptance Scenarios**:

1. **Given** guidance names a mutating tool, **When** catalogs load, **Then** validation fails.
2. **Given** limitations or unknown conditions are absent, **When** catalogs load, **Then** validation fails before advertisement.

### Edge Cases

- A projection is stale or has not refreshed.
- A read returns empty, partial historical coverage, or not found.
- MCP and application-tool names differ.
- A read is safe but insufficient for independent verification.
- Guidance references raw payloads or human numbers as identity.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The catalog MUST distinguish `read` from `proposal` guidance without weakening existing proposal validation.
- **FR-002**: Each read description MUST state purpose, use/non-use conditions, required context, authoritative data basis, limitations, freshness, refusal/empty behavior, verification role, proofs, non-proofs, unknown conditions, next steps, and positive/negative examples.
- **FR-003**: Complete descriptions MUST exist for all six scoped reads.
- **FR-004**: `capability_describe` MUST retrieve read and proposal guidance through one non-mutating path shared by Chat and MCP.
- **FR-005**: Read guidance MUST resolve to exactly one existing non-mutating application tool and public agent tool.
- **FR-006**: Validation MUST reject missing fields, invalid roles, mutating targets, unknown data-basis references, and contradictory side-effect or confirmation claims.
- **FR-007**: Descriptions MUST distinguish independent verification from context-only or discovery reads and define unknown outcomes.
- **FR-008**: Guidance MUST NOT expose tenant data, payloads, secrets, hidden reasoning, or administrative operations.
- **FR-009**: Existing proposal descriptions and their confirmation, event, refusal, and verification contracts MUST remain unchanged.

### Domain and Traceability Requirements

- **DR-001**: Guidance MUST preserve Source → Evidence → Reality and identify the stage or projection supplying each read.
- **DR-002**: Discovery, projections, exceptions, and interpretation outcomes MUST NOT be described as new business authority.
- **DR-003**: Descriptions grant no tenant access or authority; runtime reads retain existing tenant boundaries.
- **DR-004**: The feature MUST add no schema or duplicated business state.

## Success Criteria *(mandatory)*

- **SC-001**: 100% of the six scoped reads return complete validated descriptions.
- **SC-002**: All six include an explicit non-proof and unknown condition.
- **SC-003**: Every planted contract defect fails before runtime advertisement.
- **SC-004**: Every FR and DR maps to executable proof.

## Assumptions and Dependencies

- Existing reads and projections remain authoritative and unchanged.
- Public MCP identity may differ from application-tool identity and is mapped explicitly.
- The owner's "ja mach das" approves this bounded six-read slice.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Planned evidence |
|---|---|---|
| FR-001–FR-003, DR-001–DR-002 | US1 | Six-read catalog matrix |
| FR-004–FR-005, DR-003 | US1, US3 | Application/MCP lookup and drift tests |
| FR-006–FR-008 | US2, US3 | Planted validation defects |
| FR-009, DR-004 | Regression | Existing proposal guidance and schema-diff tests |
