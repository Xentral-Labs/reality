# Feature Specification: Non-Blocking Authenticated Reads

**Feature Branch**: `002-auth-session-read-concurrency`
**Created**: 2026-08-31
**Status**: Approved
**Language**: English
**Input**: "Permanently correct the unresponsive local application and restart it."

## Context and Intent

### Problem

Authenticated reads currently mark `UserSession.last_seen_at` as changed. A later read
triggers an implicit row update. Concurrent requests using the same browser session can
then wait on that row while synchronous database work occupies the application event
loop, leaving the Web application unresponsive. The timestamp is not committed by these
read paths, so the write has no durable product effect.

### Scope

- Make current-user resolution read-only.
- Preserve login, logout, session creation, expiry, revocation, and cookie behavior.
- Add executable proof that authenticated reads do not update the session row.
- Verify concurrent browser-startup reads and local application responsiveness.

### Non-Goals

- Adding a new activity-tracking mechanism.
- Changing database schema, session lifetime, or cookie policy.
- Changing authorization, tenant membership, or access-review behavior.
- Changing Source, Evidence, or Reality business behavior.

### Existing Contracts

- [`AGENTS.md`](../../AGENTS.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Continue Using the Authenticated Web Application (Priority: P1)

As an authenticated operator, I can load and navigate the Web application while the
browser makes overlapping API requests using the same session.

**Why this priority**: Session-row lock waits can make the authenticated product appear
unavailable even though underlying business operations are healthy.

**Independent Test**: Resolve the current user repeatedly and concurrently with one
valid session while observing persistence statements; verify that reads emit no session
update and explicit session mutations still work.

**Acceptance Scenarios**:

1. **Given** a valid browser session, **When** an authenticated read resolves the
   current user, **Then** it performs no write to the session row.
2. **Given** overlapping authenticated reads for the same session, **When** both
   authenticate, **Then** neither waits for an application-created session-row lock.
3. **Given** login or session creation, **When** authentication succeeds, **Then** the
   existing session creation, expiry, revocation, and cookie behavior is unchanged.
4. **Given** an invalid, expired, or revoked session, **When** authentication is
   attempted, **Then** access remains rejected.

### Edge Cases

- Multiple browser startup requests use the same cookie concurrently.
- A session expires between requests.
- Logout explicitly revokes a session and remains a mutating operation.
- Profile mutation remains writable while unrelated current-user reads remain read-only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Resolving a user from a valid request session MUST be read-only.
- **FR-002**: Authenticated reads MUST NOT emit `UPDATE user_session` as a side effect
  of identifying the current user.
- **FR-003**: Invalid, expired, or revoked sessions MUST continue to be rejected.
- **FR-004**: Login, logout, session creation, and explicit profile mutations MUST
  retain their existing behavior.
- **FR-005**: A regression test MUST observe the persistence statements generated during
  current-user resolution and fail if a session update returns.

### Domain and Traceability Requirements

- **DR-001**: The change MUST NOT alter tenant membership, tenant isolation, or
  platform-administrator authorization semantics.
- **DR-002**: The change MUST NOT modify Source, Evidence, Reality, or business-event
  records.
- **DR-003**: Explicit session mutations MUST remain in the authentication boundary;
  ordinary reads MUST NOT introduce hidden persistence behavior.

### Key Entities

- **UserSession**: Revocable authentication session whose explicit lifecycle is stored;
  incidental reads do not create durable activity state.
- **AppUser**: Authenticated platform identity returned by current-user resolution.

## Success Criteria *(mandatory)*

- **SC-001**: Current-user resolution emits zero `UPDATE user_session` statements.
- **SC-002**: Existing user-access tests and the full required test suite pass.
- **SC-003**: After restart, the backend health endpoint and authenticated browser
  bootstrap respond without a database lock wait.

## Assumptions and Dependencies

- Existing read-path changes to `last_seen_at` are not durable because their
  request-scoped sessions close without committing them.
- Durable session activity tracking requires a separate specification with an explicit
  write and contention policy.

## Open Questions

No unresolved product decision remains. The approved scope removes only a non-durable
read side effect.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-002, FR-005 | US1 scenarios 1–2 | SQL-observation regression in `backend/tests/test_user_access.py` |
| FR-003–FR-004 | US1 scenarios 3–4 | Existing authentication/session lifecycle tests |
| DR-001–DR-003 | All scenarios | Tenant-access regression suite and final diff review |
| SC-001–SC-003 | US1 | SQL observation, complete quality suite, local health/bootstrap verification |
