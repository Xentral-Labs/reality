# Feature Specification: Live Activity Signal

**Feature Branch**: `[061-live-activity-signal]`
**Created**: 2026-09-03
**Status**: Approved
**Language**: English
**Input**: "Show new tenant activity as it happens with a sidebar count, subtle pulse, automatic Activity refresh, and attention-only notifications."

## Context and Intent

### Problem

Activity currently loads only on entry or filter changes while presenting itself as live. Operators can miss changes made elsewhere unless they manually reload.

### Scope

- Poll a lightweight tenant-scoped activity signal while the browser tab is visible.
- Show newly observed events as an unread count and brief pulse on the Activity navigation entry.
- Refresh the open Activity page automatically.
- Announce only newly observed attention events as a non-blocking notification.

### Non-Goals

- WebSockets, durable per-user notification inboxes, browser push notifications, or email.
- A new event store, schema, business calculation, or mutation.
- Replacing the bounded Activity timeline or its filters.

## User Scenarios & Testing

### User Story 1 - Notice new activity (Priority: P1)

As an operator, I can see that business activity occurred without leaving my current page.

**Independent Test**: After the initial cursor is established, create events and verify the Activity entry shows their count and pulses briefly.

**Acceptance Scenarios**:

1. **Given** a visible authenticated workspace, **When** new tenant events commit, **Then** the Activity entry shows the number observed since Activity was last opened.
2. **Given** the tab is hidden, **When** time passes, **Then** polling pauses and resumes when the tab becomes visible.
3. **Given** Activity is opened, **When** the page loads, **Then** the unread count is cleared without mutating business data.

### User Story 2 - Follow live activity safely (Priority: P1)

As an operator reviewing Activity, I see new records without manually refreshing and receive a polite notification only for attention events.

**Independent Test**: Keep Activity open, add completed and attention events, and verify automatic refresh plus attention-only announcement.

**Acceptance Scenarios**:

1. **Given** Activity is open, **When** the signal cursor advances, **Then** the existing filtered timeline reloads and newly returned rows are briefly highlighted.
2. **Given** one or more new attention events, **When** they are observed, **Then** one non-blocking accessible notification reports the count.
3. **Given** only completed events, **When** they are observed, **Then** no notification interrupts the operator.

### Edge Cases

- The tenant changes between polls.
- The first signal contains historical events.
- Multiple events arrive in one polling interval.
- A poll fails temporarily or resolves after tenant navigation.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST expose a tenant-scoped read returning latest sequence, event count, and attention-event count strictly after a supplied non-negative sequence.
- **FR-002**: The browser MUST establish the first response as its baseline and MUST NOT report historical events as newly observed.
- **FR-003**: The browser MUST poll no more frequently than every five seconds, pause while hidden, tolerate transient failures, and discard stale-tenant responses.
- **FR-004**: Activity navigation MUST show a bounded unread count and a brief non-semantic pulse when new events are observed.
- **FR-005**: Opening Activity MUST clear its unread presentation state.
- **FR-006**: An open Activity page MUST reload its existing bounded, filtered timeline when the signal advances.
- **FR-007**: Only newly observed attention events MUST produce one polite, non-blocking accessible notification per poll.

### Domain and Traceability Requirements

- **DR-001**: `BusinessEvent` remains the durable authority; polling and notifications MUST create no business records.
- **DR-002**: Every signal read MUST enforce tenant membership and tenant filtering through the shared service boundary.
- **DR-003**: The feature MUST add no schema, alternate event store, or browser-side event classification.

## Success Criteria

- **SC-001**: New committed activity becomes visible within 10 seconds while the tab is visible.
- **SC-002**: Historical activity produces zero unread or attention notifications on initialization.
- **SC-003**: Completed-only activity produces zero attention notifications.
- **SC-004**: Automated service, API, and frontend contracts prove every FR and DR.

## Assumptions and Dependencies

- Tenant-local BusinessEvent sequence allocation remains monotone.
- A 10-second polling interval is sufficiently real-time-like without persistent connections.
- Notification state is intentionally browser-session presentation state, not durable business state.

## Open Questions

None. Product scope was explicitly approved by the user.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001-FR-003, DR-001-DR-003 | US1.1-US1.2 | Service/API and frontend polling tests |
| FR-004-FR-005 | US1.1-US1.3 | Frontend navigation contract |
| FR-006-FR-007 | US2.1-US2.3 | Frontend refresh and notification contract |
| SC-001-SC-004 | All | Focused tests, build, and review |
