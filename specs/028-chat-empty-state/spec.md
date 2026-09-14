# Feature Specification: Focused Chat Empty State

**Status**: Approved  
**Created**: 2026-09-02
**Language**: English

## Context and Intent

### Problem

The zero-session Ask Reality page currently renders an empty session rail and an empty
conversation header. This chrome competes with the only useful first-use controls.

### Scope

- Present a centered first-use surface only after zero sessions are confirmed.
- Restore the complete workbench as soon as a session exists.

### Non-Goals

- Changing chat persistence, suggestions, provider behavior, or confirmation rules.

## User Scenarios & Testing

### User Story 1 - Start a first conversation (Priority: P1)

As an operator with no saved conversations, I see a calm, centered Ask Reality entry surface without an empty conversation list or conversation header.

**Independent Test**: Open Ask Reality for a tenant with zero sessions and verify that only the centered introduction, prompt suggestions, and composer are shown.

**Acceptance Scenarios**:

1. **Given** a tenant has no chat sessions, **When** Ask Reality loads, **Then** the session list and conversation header are absent and the entry controls are centered.
2. **Given** the focused empty state, **When** the user submits text or selects a suggestion, **Then** the normal chat path creates a session and sends the message.

### User Story 2 - Continue existing conversations (Priority: P2)

As an operator with saved conversations, I retain the session list, history, and composer without a redundant conversation header.

**Acceptance Scenario**: **Given** saved sessions, **When** Ask Reality loads, **Then** the standard conversation workbench remains visible.

## Edge Cases

- Loading data must not briefly present the focused empty state as confirmed tenant data.
- Deleting the final conversation returns the user to the focused empty state.
- Mobile presentation preserves a reachable composer without horizontal overflow.

## Requirements

- **FR-001**: Ask Reality MUST hide the session list when the loaded tenant has zero sessions.
- **FR-002**: Ask Reality MUST never render a conversation header above the message area.
- **FR-003**: The empty-state introduction, suggestions, and composer MUST form one centered entry surface.
- **FR-004**: Sending from the empty state MUST create a session through the existing chat flow.
- **FR-005**: Tenants with saved sessions MUST retain the session list and chat controls.
- **FR-006**: The focused empty state MUST remain usable at desktop and mobile widths.

## Assumptions and Dependencies

- "No session" means the loaded session collection is empty, not merely that no active ID is selected.
- Existing suggestion content and chat service behavior remain unchanged.

## Success Criteria

- **SC-001**: In every zero-session verification, no empty navigation rail or conversation header is visible.
- **SC-002**: A user can start the first conversation with one submit action from the centered surface.
- **SC-003**: Existing-session and mobile checks retain all prior chat controls without overflow.

## Scope

This change is limited to the Ask Reality presentation before the first session exists. It adds no business rules, persistence fields, API behavior, or provider changes.

## Requirement Traceability

| Requirement | Acceptance evidence | Planned task |
|---|---|---|
| FR-001–FR-003 | Zero-session layout contract and visual check | T001–T003 |
| FR-004 | Existing lazy send path retained and build-checked | T002, T005 |
| FR-005 | Existing-session conditional and regression contract | T001, T002, T005 |
| FR-006 | Desktop/mobile visual check | T003, T005 |
