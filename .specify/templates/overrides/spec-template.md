# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Created**: [DATE]
**Status**: Draft
**Language**: English
**Input**: "$ARGUMENTS"

## Context and Intent

### Problem

[What business problem exists, who experiences it, and why it matters now?]

### Scope

- [Observable outcome included in this feature]

### Non-Goals

- [Explicitly excluded behavior]

### Existing Contracts

- [Link applicable docs/features, WEB_SPEC, DATA_MODEL, ADRs]

## User Scenarios & Testing *(mandatory)*

### User Story 1 - [Title] (Priority: P1)

[Technology-independent journey]

**Why this priority**: [Value]

**Independent Test**: [How this slice is verified by itself]

**Acceptance Scenarios**:

1. **Given** [state], **When** [event], **Then** [observable result]
2. **Given** [boundary/error state], **When** [event], **Then** [safe result]

[Add independently testable P2/P3 stories only when needed.]

### Edge Cases

- [Tenant boundary, idempotency, partial flow, correction, empty state, failure]

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST [specific observable behavior].
- **FR-002**: The system MUST [specific invariant or failure behavior].

### Domain and Traceability Requirements

- **DR-001**: [How Source → Evidence → Reality is preserved or why a stage is N/A]
- **DR-002**: [Shortest true relationship and derived-state implications]
- **DR-003**: [Tenant isolation and shared-service path]

### Key Entities *(when data is involved)*

- **[Entity]**: [Business meaning and relationships, not implementation fields]

## Success Criteria *(mandatory)*

- **SC-001**: [Measurable, technology-independent outcome]
- **SC-002**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- [Explicit assumption or dependency]

## Open Questions

- [NEEDS CLARIFICATION: question and why it changes scope/behavior]

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | [test/story to be named in plan/tasks] |
