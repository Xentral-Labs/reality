# Feature Specification: Home Live Link Placement

**Feature Branch**: `spec/287-home-live-link`

**Created**: 2026-09-27

**Status**: Approved

**Language**: English

**Input**: Place the Welcome activity graph's "Watch live" action beside its live status instead of below the time-range control.

## Context and Intent

### Problem

The outlined live-monitor action currently sits below the graph's time-range selector. This makes it look like an unrelated second row and weakens the connection between the action and the graph's live status.

### Scope

- Present the existing live-monitor action as a quiet text action beside the graph's live status.
- Keep the time-range selector as the only control on the right of the graph header.
- Preserve the existing navigation, permissions, localization and responsive behavior.

### Non-Goals

- Changing what the live monitor displays or who can open it.
- Changing activity data, polling, periods, readiness or graph behavior.
- Adding a new navigation path, API, schema or business rule.

## User Scenarios & Testing

### User Story 1 - Recognize the live action in context (Priority: P1)

As a company owner scanning Welcome, I can recognize that the action beside the Live status opens the live monitor while the period selector remains visually independent.

**Why this priority**: It removes the current visual ambiguity without adding another control or concept.

**Independent Test**: Open Welcome as an owner on desktop and mobile; the localized action is beside the Live status, the period selector remains at the right, and activating the action opens the existing live monitor.

**Acceptance Scenarios**:

1. **Given** activity data and an owner who may open the live monitor, **When** the graph header appears, **Then** a quiet localized "Watch live" action appears inline beside the Live status rather than inside the period-control group.
2. **Given** the inline action, **When** the owner activates it, **Then** the existing live-monitor navigation callback runs unchanged.
3. **Given** a narrow viewport, **When** the graph header wraps, **Then** the status and action remain a coherent group and the period selector remains usable without horizontal page overflow.
4. **Given** a user without the live-monitor entry point, **When** the graph header appears, **Then** the existing Live status remains and no action is shown.

### Edge Cases

- Localized labels may be longer than English and must wrap without colliding with the period selector.
- The action is absent while no live-monitor callback is available.
- Loading, stale and failure states retain their current semantics.

## Requirements

### Functional Requirements

- **FR-001**: The existing live-monitor action MUST appear inline with the activity graph's Live status whenever that action is available.
- **FR-002**: The live-monitor action MUST use a quiet link-like presentation and MUST NOT use the outlined general-button treatment.
- **FR-003**: The period selector MUST remain a separate graph-header control and MUST NOT contain the live-monitor action.
- **FR-004**: Activating the action MUST invoke the existing live-monitor navigation unchanged.
- **FR-005**: The layout MUST preserve readable localized labels, keyboard access, visible focus and page-width containment on desktop and mobile.
- **FR-006**: Activity data, polling, readiness, authorization and live-monitor behavior MUST remain unchanged.

## Success Criteria

### Measurable Outcomes

- **SC-001**: On desktop and a 390-pixel viewport, the live-monitor action is visually grouped with the Live status and the page has no horizontal overflow.
- **SC-002**: All four supported languages display the action without overlap or truncation that hides its meaning.
- **SC-003**: Automated frontend evidence proves placement, presentation, conditional visibility and unchanged activation.

## Assumptions and Dependencies

- The existing owner-only callback remains the authority for whether the action is available.
- The existing translations for "Watch live" remain suitable.
- This refines spec 266 FR-009 and the Welcome layout in `docs/features/home-live-status.md` without changing their behavioral scope.

## Open Questions

None. The owner explicitly selected the quiet inline action beside the Live status.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1.1, US1.3, US1.4 | Focused frontend placement contract and responsive browser review |
| FR-004 | US1.2 | Existing callback retained; focused frontend contract and build |
| FR-005 | US1.1, US1.3 | Focused frontend contract, build and desktop/mobile browser review |
| FR-006 | All | Diff review; existing Home contracts and frontend gates |
| SC-001–SC-003 | All | Focused contract, build, localization audit and browser review |
